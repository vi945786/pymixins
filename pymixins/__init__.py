import gc
import importlib.util
import pkgutil
import sys
import os
import types
import weakref
from typing import List, Tuple, Any
import pymixins.object_manipulator as om
import inspect


def get_module_code(module: types.ModuleType):
    return inspect.getsource(module)


def get_module_file_without_importing(module: str) -> str:
    parts = module.split('.')

    path = importlib.util.find_spec(parts[0]).origin
    if path == "built-in":
        raise TypeError(f"{module} is a built-in module and does not have python source code")

    if len(parts) == 1:
        return path

    path = os.path.join(os.path.dirname(path), *parts[1:])

    init_file = os.path.join(path, '__init__.py')
    if os.path.isfile(init_file):
        return init_file

    module_file = path + '.py'
    if os.path.isfile(module_file):
        return module_file

    raise ValueError(f"{module} source file not found")


def define_module_as_code(module_name: str, code_string: str):
    if module_name in sys.modules:
        raise ValueError(f"Module '{module_name}' already exists")

    module = types.ModuleType(module_name)
    exec(code_string, module.__dict__)
    sys.modules[module_name] = module
    return module


def replace_everywhere(*objs: Tuple[Any, Any], do_weakrefs: bool = True):
    seen = set()
    obj_queue = [(old, new) for old, new in objs]

    primitive_types = (str, int, tuple, float, bool, bytes, frozenset, complex)

    gc.collect()
    all_objs = om.get_all_objs()

    while obj_queue:
        old, new = obj_queue.pop()
        old_id = id(old)
        if old_id in seen:
            continue
        seen.add(old_id)

        if do_weakrefs:
            for weak in weakref.getweakrefs(old):
                obj_queue.append((weak, weakref.ref(new)))

        for referrer, key in om.get_all_refs_to_value(all_objs, old):
            om.set_value(referrer, key, new)

        old_keys = om.get_all_keys(old)
        new_keys = om.get_all_keys(new)
        common_keys = [k for k in old_keys if k in new_keys]

        for key in common_keys:
            old_val = om.get_value(old, key)
            new_val = om.get_value(new, key)

            if isinstance(old_val, primitive_types):
                om.set_value(old, key, new_val)
                continue

            if old_val is not new_val and id(old_val) not in seen:
                obj_queue.append((old_val, new_val))

    om.clear_cache()
    gc.collect()


def redefine_modules_file_as_code(
    *redefine_modules: Tuple[types.ModuleType, str],
    do_replace=True,
    **kwargs
) -> List[Tuple[types.ModuleType, dict]]:

    redefined: List[Tuple[types.ModuleType, str, dict]] = []

    for module, code in redefine_modules:
        old_dict = module.__dict__.copy()
        redefined.append((module, code, old_dict))

        keep = {"__name__", "__doc__", "__package__", "__loader__", "__spec__", "__path__", "__file__", "__builtins__"}
        if "__path__" in old_dict:
            keep.update({f"{name}" for _, name, is_pkg in pkgutil.iter_modules(old_dict["__path__"])})

        for k in list(module.__dict__.keys()):
            if k not in keep:
                del module.__dict__[k]

        if "__cached__" in old_dict:
            module.__dict__["__cached__"] = ""

    for module, code, old_dict in redefined:
        exec(code, module.__dict__)
        if do_replace:
            replace_everywhere((old_dict, module.__dict__), **{k.replace("replace_", "", 1): v for k, v in kwargs.items() if k.startswith("replace_")})

    return [(module, old_dict) for module, _, old_dict in redefined]
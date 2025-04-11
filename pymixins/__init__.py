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

    # if not module or not module.__spec__ or not module.__spec__.origin:
    #     raise ValueError(f"{module} source file not found")
    # return module.__spec__.origin


def get_module_file_without_importing(module: str) -> str:
    parts = module.split('.')

    path = importlib.util.find_spec(parts[0]).origin
    if path == "built-in":
        raise ValueError(f"{module} is a built-in module and does not have python source code")

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


def replace_everywhere(*objs: Tuple[Any, Any], max_depth: int = None, weakref_depth: int = None, do_weakrefs: bool = True):
    seen = set()
    obj_list = [(old_obj, new_obj, max_depth) for old_obj, new_obj in objs]

    while obj_list:
        old, new, depth = obj_list.pop(0)
        if id(old) in seen:
            continue
        seen.add(id(old))

        if depth and depth < 0 or isinstance(old, (int, float, complex, bool, str, bytes)):
            continue

        if do_weakrefs:
            for weak in weakref.getweakrefs(old):
                obj_list.insert(0, (weak, weakref.ref(new), weakref_depth))

        referrers = gc.get_referrers(old)
        for referrer in referrers:
            if referrer is old or referrer is locals():
                continue

            for key in om.get_keys_from_value(referrer, old, do_attrs=False):
                om.set_value(referrer, key, new)

                if isinstance(referrer, dict):
                    for ref_ref in gc.get_referrers(referrer):
                        if hasattr(ref_ref, "__dict__") and hasattr(ref_ref, key[0]):
                            if getattr(ref_ref, key[0]) is old:
                                setattr(ref_ref, key[0], new)

        if depth and depth <= 0:
            continue

        common_keys = []

        new_type_keys = om.get_all_keys(type(new))
        new_keys_no_attrs = om.get_all_keys(new, do_attrs=False)

        if id(type(old)) not in seen:
            seen.add(id(type(old)))
            for key in om.get_all_keys(type(old)):
                if key in new_type_keys:
                    common_keys.append(key)

        for key in om.get_all_keys(old, do_attrs=False):
            if key in new_keys_no_attrs:
                common_keys.append(key)

        for key in common_keys:
            old_val = om.get_value(old, key)
            new_val = om.get_value(new, key)

            if old_val is new_val or id(old_val) in seen or old_val is None:
                continue

            obj_list.append((old_val, new_val, depth - 1 if depth else None))


def redefine_modules_file_as_code(
    *redefine_modules: Tuple[types.ModuleType, str],
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
        replace_everywhere((old_dict, module.__dict__), **{k.replace("replace_", "", 1): v for k, v in kwargs.items() if k.startswith("replace_")})

    return [(module, old_dict) for module, _, old_dict in redefined]

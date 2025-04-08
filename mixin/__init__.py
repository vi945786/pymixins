import gc
import sys
import os
import types
import weakref
from typing import List, Tuple, Any
import mixin.object_manipulator as om


def get_module_file(module_name: str) -> str | None:
    parts = module_name.split('.')

    for path in sys.path:
        if not os.path.isdir(path):
            continue

        potential_path = os.path.join(path, *parts)

        init_file = os.path.join(potential_path, '__init__.py')
        if os.path.isfile(init_file):
            return init_file

        module_file = potential_path + '.py'
        if os.path.isfile(module_file):
            return module_file

    return None


def define_module_as_code(module_name: str, code_string: str):
    if module_name in sys.modules:
        raise ValueError(f"Module '{module_name}' already exists")

    module = types.ModuleType(module_name)
    exec(code_string, module.__dict__)
    sys.modules[module_name] = module
    return module


def replace_everywhere(*objs: Tuple[Any, Any], max_depth=1, weakref_depth=0, do_weakrefs=True):
    seen = set()
    obj_list = [(old_obj, new_obj, max_depth) for old_obj, new_obj in objs]

    while obj_list:
        old, new, depth = obj_list.pop(0)
        if id(old) in seen:
            continue
        seen.add(id(old))

        if depth < 0:
            continue

        for referrer in gc.get_referrers(old):
            if referrer is old or isinstance(referrer, (str, tuple, int, float, complex)):
                continue

            for key in om.get_keys_from_value(referrer, old, do_attrs=False):
                if om.get_value(referrer, key) is old:
                    om.set_value(referrer, key, new)

                    if isinstance(referrer, dict):
                        for ref_ref in gc.get_referrers(referrer):
                            if hasattr(ref_ref, "__dict__") and hasattr(ref_ref, key[0]):
                                if getattr(ref_ref, key[0]) is old:
                                    setattr(ref_ref, key[0], new)

        if depth <= 0:
            continue

        for key in om.get_all_keys(old):
            if key not in om.get_all_keys(new):
                continue

            old_val = om.get_value(old, key)
            new_val = om.get_value(new, key)

            if old_val is new_val or id(old_val) in seen:
                continue

            if do_weakrefs:
                for weak in weakref.getweakrefs(old_val):
                    obj_list.append((weak, weakref.ref(new_val), weakref_depth))

            obj_list.append((old_val, new_val, depth - 1))


def redefine_modules_file_as_code(
    *redefine_modules: Tuple[str, str],
    **kwargs
) -> List[Tuple[types.ModuleType, dict]]:

    redefined: List[Tuple[types.ModuleType, str, dict]] = []

    for mod_name, code in redefine_modules:
        module = __import__(mod_name)
        old_dict = module.__dict__.copy()
        redefined.append((module, code, old_dict))

        keep = {"__name__", "__doc__", "__package__", "__loader__", "__spec__", "__file__", "__builtins__"}
        module.__dict__.clear()
        module.__dict__.update({k: v for k, v in old_dict.items() if k in keep})

        if "__cached__" in old_dict:
            module.__dict__["__cached__"] = ""

    for module, code, old_dict in redefined:
        exec(code, module.__dict__)
        replace_everywhere((old_dict, module.__dict__), **{k.replace("replace_", "", 1): v for k, v in kwargs.items() if k.startswith("replace_")})

    return [(module, old_dict) for module, _, old_dict in redefined]

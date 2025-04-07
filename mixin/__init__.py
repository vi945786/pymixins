import gc
import sys
import os
import types
import weakref

from typing import List, Tuple


def get_module_file(module_name):
    parts = module_name.split('.')

    for path in sys.path:
        potential_path = os.path.join(path, *parts)

        if os.path.isdir(potential_path) and os.path.isfile(os.path.join(potential_path, '__init__.py')):
            return os.path.join(potential_path, '__init__.py')

        module_file = potential_path + ".py"
        if os.path.isfile(module_file):
            return module_file

    return None


def define_module_as_code(code_string, module_name):
    if module_name in sys.modules:
        raise ValueError("module exists")

    module = types.ModuleType(module_name)
    exec(code_string, module.__dict__)
    sys.modules[module_name] = module
    return module


def replace_everywhere(old_obj, new_obj, max_depth=2):
    import mixin.object_manipulator as om

    seen = []
    obj_list = [(old_obj, new_obj, 0)]

    while len(obj_list) != 0:
        old, new, depth = obj_list.pop(0)
        seen.append(old)

        # won't get any attribute refs
        for referrer in gc.get_referrers(old):
            if referrer is old or isinstance(referrer, (str, tuple, int, float, complex)):
                continue
            for key in om.get_keys_from_value(referrer, old):
                if key[1] != "index":
                    continue
                if om.get_value(referrer, key) is old:
                    om.set_value(referrer, key, new)
                    if isinstance(referrer, dict):
                        for referrer_referrer in gc.get_referrers(referrer):
                            if hasattr(referrer_referrer, "__dict__"):
                                if hasattr(referrer_referrer, key[0]):
                                    if getattr(referrer_referrer, key[0]) is old:
                                        setattr(referrer_referrer, key[0], new)

        if not depth < max_depth:
            continue

        for key in om.get_all_keys(old):
            if key not in om.get_all_keys(new):
                continue
            old_value = om.get_value(old, key)
            new_value = om.get_value(new, key)

            if not (old_value is new_value or old_value in seen):
                for ref in weakref.getweakrefs(old_value):
                    obj_list.append((ref, weakref.ref(new_value), depth + 1))

                obj_list.append((old_value, new_value, depth + 1))


def redefine_modules_file_as_code(*redefine_modules: Tuple[str, str], max_replace_depth=2) -> List[Tuple[types.ModuleType, dict]]:
    redefined_modules: List[Tuple[types.ModuleType, str, dict]] = []
    for redefine_module in redefine_modules:

        module = __import__(redefine_module[0])

        old_dict = module.__dict__.copy()
        redefined_modules.append((module, redefine_module[1], old_dict))

        for key in list(module.__dict__.keys()):
            if key not in ["__name__", "__doc__", "__package__", "__loader__", "__spec__", "__file__", "__builtins__"]:
                del module.__dict__[key]

        if "__cached__" in old_dict:
            module.__dict__["__cached__"] = ""

    for module, code, old_dict in redefined_modules:
        exec(code, module.__dict__)
        replace_everywhere(old_dict, module.__dict__, max_replace_depth)

    return [(module, old_dict) for module, _, old_dict in redefined_modules]

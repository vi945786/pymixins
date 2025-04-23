import gc
from typing import Any, Tuple, List


def _get_all_attr_keys(obj):
    result = []

    for base in type(obj).__mro__:
        for k, v in base.__dict__.items():
            if hasattr(v, "__set__"):
                result.append((k, "attr", False))

    return result


def get_all_keys(obj: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    keys = []
    if do_attrs:
        keys.extend(_get_all_attr_keys(obj))

    if not isinstance(obj, skip_types):
        if isinstance(obj, dict):
            keys.extend([(k, "keys", False) for k in obj.keys()])
        elif isinstance(obj, list):
            keys.extend([(i, "index", False) for i in range(len(obj))])
        elif isinstance(obj, tuple):
            keys.extend([(i, "index", True) for i in range(len(obj))])
        elif isinstance(obj, set):
            keys.extend([(i, "old_val", False) for i in obj])
        elif isinstance(obj, frozenset):
            keys.extend([(i, "old_val", True) for i in obj])
    return keys


_get_attr_keys_from_value_cache = {}
def _get_attr_keys_from_value(obj: Any, val_id: int):
    if type(obj) in _get_attr_keys_from_value_cache:
        keys = _get_attr_keys_from_value_cache[type(obj)]
    else:
        obj_type = type(obj)
        keys = _get_all_attr_keys(obj)
        _get_attr_keys_from_value_cache[obj_type] = keys
    filtered_keys = []

    for key in keys:
        try:
            if id(getattr(obj, key[0])) == val_id:
                filtered_keys.append(key)
        except (ValueError, AttributeError):
            pass

    return filtered_keys


def get_keys_from_value(obj: Any, value: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    val_id = id(value)
    keys = []

    if do_attrs:
        keys.extend(_get_attr_keys_from_value(obj, val_id))

    if isinstance(obj, skip_types):
        return keys

    t = type(obj)
    if t is dict:
        for k, v in obj.items():
            if v is value:
                keys.append((k, "keys", False))
    elif t is list:
        keys.extend((i, "index", False) for i, v in enumerate(obj) if v is value)
    elif t is tuple:
        keys.extend((i, "index", True) for i, v in enumerate(obj) if v is value)
    elif t is set:
        try:
            if value in obj:
                keys.append((value, "old_val", False))
        except TypeError:
            pass
    elif t is frozenset:
        try:
            if value in obj:
                keys.append((value, "old_val", True))
        except TypeError:
            pass

    return keys


def get_value(obj: Any, ref: Tuple[Any, str]) -> Any:
    if ref[1] == "attr":
        return getattr(obj, ref[0])
    elif ref[1] in ("keys", "index"):
        return obj[ref[0]]
    elif ref[1] == "old_val":
        return ref[0]


def set_value(obj: Any, ref: Tuple[Any, str], value: Any) -> None:
    try:
        if ref[2]:
            if ref[1] == "index":
                index = int(ref[0])
                new_instance = obj[:index] + (value,) + obj[index+1:]
            elif ref[1] == "old_val":
                new_instance = frozenset(x if x != ref[0] else value for x in obj)
            for referrer in gc.get_referrers(obj):
                if referrer is locals():
                    continue
                for key in get_keys_from_value(referrer, obj):
                    set_value(referrer, key, new_instance)
        elif ref[1] == "attr":
            setattr(obj, ref[0], value)
        elif ref[1] in ("keys", "index"):
            obj[ref[0]] = value
        elif ref[1] == "old_val":
            obj.discard(ref[0])
            obj.add(value)
    except AttributeError as e:
        pass

def get_all_refs_to_value(all_objs, value):
    return [(o, refs) for o in all_objs if (refs := get_keys_from_value(o, value))]


def get_all_objs():
    objs = []
    seen = set()
    todo = gc.get_objects()

    while todo:
        o = todo.pop()
        oid = id(o)
        if oid in seen:
            continue
        seen.add(oid)
        objs.append(o)
        todo.extend(gc.get_referents(o))

    return objs
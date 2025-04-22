import gc
import inspect
import types
from types import GetSetDescriptorType
from typing import Any, Tuple, List


def get_all_keys(obj: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    keys = []
    if do_attrs:
        for k, v in inspect.getmembers(obj):
            if isinstance(v, GetSetDescriptorType):
                keys.append((k, "attr"))

    if not isinstance(obj, skip_types):
        if isinstance(obj, (list, tuple)):
            keys += [(i, "index") for i in range(len(obj))]
        elif isinstance(obj, (set, frozenset)):
            keys += [(i, "old_val") for i in obj]
        elif isinstance(obj, dict):
            keys += [(k, "keys") for k in obj.keys()]
    return keys


_get_attr_keys_from_value_cache = {}
def _get_attr_keys_from_value(obj: Any, val_id: int):
    if type(obj) in _get_attr_keys_from_value_cache:
        keys = _get_attr_keys_from_value_cache[type(obj)]
    else:
        obj_type = type(obj)
        keys = []
        for k in dir(obj):
            old_v = obj_type.__dict__.get(k, None)
            if not isinstance(old_v, (types.NoneType, types.WrapperDescriptorType)):
                keys.append((k, "attr"))
            _get_attr_keys_from_value_cache[obj_type] = keys

    filter_keys = []
    for k in keys:
        try:
            if id(getattr(obj, k[0])) == val_id:
                filter_keys.append((k, "attr"))
        except (ValueError, AttributeError):
            pass

    return filter_keys


def get_keys_from_value(obj: Any, value: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    val_id = id(value)
    keys = []

    if do_attrs:
        keys.extend(_get_attr_keys_from_value(obj, val_id))

    if isinstance(obj, skip_types):
        return keys

    t = type(obj)
    if t in (list, tuple):
        keys.extend((i, "index") for i, v in enumerate(obj) if v is value)
    elif t in (set, frozenset):
        try:
            if value in obj:
                keys.append((value, "old_val"))
        except TypeError:
            pass
    elif t is dict:
        for k, v in obj.items():
            if v is value:
                keys.append((k, "keys"))

    return keys


def get_keys_and_values(obj, do_attrs=True, skip_types=()):
    if isinstance(obj, skip_types):
        return []

    kvs = []

    if do_attrs:
        append = kvs.append
        for k in dir(obj):
            try:
                append(((k, "attr"), getattr(obj, k)))
            except (ValueError, AttributeError):
                continue

    t = type(obj)
    if t is list or t is tuple:
        kvs.extend(((i, "index"), v) for i, v in enumerate(obj))
    elif t is set or t is frozenset:
        kvs.extend(((v, "old_val"), v) for v in obj)
    elif t is dict:
        kvs.extend(((k, "keys"), v) for k, v in obj.items())

    return kvs


def get_all_values(obj: Any, do_attrs=True, skip_types=()) -> list[GetSetDescriptorType]:
    values = []
    if do_attrs:
        for _, v in inspect.getmembers(obj):
            if isinstance(v, GetSetDescriptorType):
                values.append(v)

    if not isinstance(obj, skip_types):
        if isinstance(obj, (list, tuple)):
            values += [obj[i] for i in range(len(obj))]
        elif isinstance(obj, (set, frozenset)):
            values += [i for i in obj]
        elif isinstance(obj, dict):
            values += [v for v in obj.values()]
    return values


def get_value(obj: Any, ref: Tuple[Any, str]) -> Any:
    if ref[1] == "attr":
        return getattr(obj, ref[0])
    elif ref[1] == "index" or ref[1] == "keys":
        return obj[ref[0]]
    elif ref[1] == "old_val":
        return ref[0]


def set_value(obj: Any, ref: Tuple[Any, str], value: Any) -> None:
    if ref[1] == "attr":
        setattr(obj, ref[0], value)
    else:
        if (isinstance(obj, tuple) and ref[1] == "index") or (isinstance(obj, frozenset) and ref[1] == "old_val"):
            if isinstance(obj, tuple):
                index = int(ref[0])
                new_instance = obj[:index] + (value,) + obj[index+1:]
            else:
                new_instance = frozenset(x if x != ref[0] else value for x in obj)
            for referrer in gc.get_referrers(obj):
                if referrer is locals():
                    continue
                for key in get_keys_from_value(referrer, obj):
                    set_value(referrer, key, new_instance)
        elif ref[1] == "index" or ref[1] == "keys":
            obj[ref[0]] = value
        elif ref[1] == "old_val":
            obj.discard(ref[0])
            obj.add(value)


def get_all_refs_to_value(objs_graph, value, *ignore):
    # ignore = {id(i) for i in ignore}
    # return [(o, refs) for o in all_objs if id(o) not in ignore and (refs := get_keys_from_value(o, value))]
    return objs_graph[id(value)]

def _get_all_objs():
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

def get_objs_graph():
    all_objs = _get_all_objs()
    graph = {}

    for o in all_objs:
        for k, v in get_keys_and_values(o):
            graph.setdefault(id(v), []).append((o, k))

    return graph
import gc
from typing import Any, Tuple, List


def get_all_keys(obj: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    keys = []
    if do_attrs:
        keys += [(attr, "attr") for attr in dir(obj)]

    if not isinstance(obj, skip_types):
        if isinstance(obj, (list, tuple)):
            keys += [(i, "index") for i in range(len(obj))]
        elif isinstance(obj, set):
            keys += [(i, "old_val") for i in obj]
        elif isinstance(obj, dict):
            keys += [(k, "keys") for k in obj.keys()]
        else:
            if hasattr(obj, "__slots__"):
                slots = getattr(obj, "__slots__")
                keys.extend([(slot, "attr") for slot in slots])
    return keys


def get_keys_from_value(obj: Any, value: Any, do_attrs=True, skip_types=()) -> List[Tuple[Any, str]]:
    keys = []

    if do_attrs:
        val_id = id(value)
        for attr in dir(obj):
            if id(getattr(obj, attr)) == val_id:
                keys.append((attr, "attr"))

    if not isinstance(obj, skip_types):
        if isinstance(obj, (list, tuple)):
            keys.extend((i, "index") for i, v in enumerate(obj) if v is value)
        elif isinstance(obj, set):
            keys += [(i, "old_val") for i in obj]
        elif isinstance(obj, dict):
            keys.extend((k, "keys") for k, v in obj.items() if v is value)
        else:
            if hasattr(obj, "__slots__"):
                slots = getattr(obj, "__slots__")
                keys.extend([(slot, "attr") for slot in slots if getattr(obj, slot) is value])
    return keys


def get_value(obj: Any, ref: Tuple[Any, str]) -> Any:
    if ref[1] == "attr":
        return getattr(obj, ref[0])
    elif ref[1] == "index" or ref[1] == "keys":
        return obj[ref[0]]
    elif ref[1] == "old_val":
        return ref[0]


def set_value(obj: Any, ref: Tuple[Any, str], value: Any) -> None:
    try:
        if ref[1] == "attr":
            setattr(obj, ref[0], value)
        elif ref[1] == "index" or ref[1] == "keys":
            if isinstance(obj, tuple):
                index = int(ref[0])
                new_tuple = obj[:index] + (value,) + obj[index+1:]
                for referrer in gc.get_referrers(obj):
                    for key in get_keys_from_value(referrer, obj):
                        set_value(referrer, key, new_tuple)
            else:
                obj[ref[0]] = value
        elif ref[1] == "old_val":
            obj.discard(ref[0])
            obj.add(value)
    except (AttributeError, TypeError) as e:
        ok_exceptions = ["readonly attribute", "not writable", "not support item assignment"]
        e_str = str(e)
        if all([ok not in e_str for ok in ok_exceptions]):
            raise
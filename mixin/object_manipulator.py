from typing import Any, Tuple, List


def get_all_keys(obj: Any, do_attrs=True, do_indexes=True, do_keys=True) -> List[Tuple[Any, str]]:
    keys = []
    if do_attrs:
        keys += [(attr, "attr") for attr in dir(obj)]
    if do_indexes and isinstance(obj, (list, tuple)):
        keys += [(i, "index") for i in range(len(obj))]
    elif do_keys and isinstance(obj, dict):
        keys += [(k, "keys") for k in obj.keys()]
    return keys


def get_all_value(obj: Any, do_attrs=True, do_indexes=True, do_keys=True) -> List[Tuple[Any, str]]:
    values = []
    if do_attrs:
        values = [(attr, "attr") for attr in dir(obj)]
    if do_indexes and isinstance(obj, (list, tuple)):
        values += [(i, "index") for i in range(len(obj))]
    elif do_keys and isinstance(obj, dict):
        values += [(k, "keys") for k in obj]
    return values


def get_keys_from_value(obj: Any, value: Any, do_attrs=True, do_indexes=True, do_keys=True) -> List[Tuple[Any, str]]:
    keys = []

    if do_attrs:
        val_id = id(value)
        for attr in dir(obj):
            if id(getattr(obj, attr)) == val_id:
                keys.append((attr, "attr"))

    if do_indexes and isinstance(obj, (list, tuple)):
        keys.extend((i, "index") for i, v in enumerate(obj) if v is value)

    elif do_keys and isinstance(obj, dict):
        keys.extend((k, "keys") for k, v in obj.items() if v is value)

    return keys


def get_value(obj: Any, ref: Tuple[Any, str]) -> Any:
    return getattr(obj, ref[0]) if ref[1] == "attr" else obj[ref[0]]


def set_value(obj: Any, ref: Tuple[Any, str], value: Any) -> None:
    try:
        if ref[1] == "attr":
            setattr(obj, ref[0], value)
        else:
            obj[ref[0]] = value
    except AttributeError as e:
        if "readonly attribute" not in str(e) and "not writable" not in str(e):
            raise

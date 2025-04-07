from typing import Any, Tuple, List


def get_all_keys(obj: Any) -> List[Tuple[Any, str]]:
    keys = [(attr, "attr") for attr in dir(obj)]
    if isinstance(obj, (list, tuple)):
        keys += [(i, "index") for i in range(len(obj))]
    elif isinstance(obj, dict):
        keys += [(k, "index") for k in obj.keys()]
    return keys


def get_all_value(obj: Any) -> List[Tuple[Any, str]]:
    values = [(attr, "attr") for attr in dir(obj)]
    if isinstance(obj, (list, tuple)):
        values += [(i, "index") for i in range(len(obj))]
    elif isinstance(obj, dict):
        values += [(k, "index") for k in obj]
    return values


def get_keys_from_value(obj: Any, value: Any) -> List[Tuple[Any, str]]:
    keys = [(attr, "attr") for attr in dir(obj) if getattr(obj, attr, None) is value]
    if isinstance(obj, (list, tuple)):
        keys += [(i, "index") for i, v in enumerate(obj) if v is value]
    elif isinstance(obj, dict):
        keys += [(k, "index") for k, v in obj.items() if v is value]
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

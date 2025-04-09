import weakref

import modify
from modify import func
from modify import func as get_status

func_ref = weakref.ref(func)
func_tuple = (func,)
func_list = [func]
func_set = {func}


class Test:
    from modify import func

    def __init__(self):
        self.func = func

    def call_func(self):
        return self.func()


def test(output):
    assert modify.func() == output
    assert func() == output
    assert get_status() == output
    assert Test.func() == output
    assert Test().call_func() == output
    assert func_ref()() == output
    assert func_tuple[0]() == output
    assert func_list[0]() == output
    assert func_set.copy().pop()() == output
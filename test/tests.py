import io
import weakref
import pymixins
import time

import test.modify as modify
from test.modify import func
from test.modify import func as get_status

func_ref = weakref.ref(func)
func_tuple = (func,)
func_list = [func]
func_set = {func}
func_frozenset = frozenset({func})


class Test:
    from test.modify import func

    def __init__(self):
        self.func = func

    def call_func(self):
        return self.func()


class SlotsTest:
    __slots__ = ("func",)

    def __init__(self):
        from test.modify import func
        self.func = func


test_instance = Test()
slot_test_instance = SlotsTest()


def run_tests(output):
    return tuple({
        assert_equals(modify.func(), output),
        assert_equals(func(), output),
        assert_equals(get_status(), output),
        assert_equals(Test.func(), output),
        assert_equals(test_instance.call_func(), output),
        assert_equals(slot_test_instance.func(), output),
        assert_equals(func_ref()(), output),
        assert_equals(func_tuple[0](), output),
        assert_equals(func_list[0](), output),
        assert_equals(func_set.copy().pop()(), output),
        assert_equals(list(func_frozenset)[0](), output)
    } - {None})


def assert_equals(actual, expected):
    import traceback
    try:
        assert actual == expected
    except AssertionError:
        stack = traceback.extract_stack()
        return ''.join(traceback.format_list(stack[-2:-1]))[:-1] + f" expected '{expected}' but got '{actual}'"
    else:
        return None


def time_redefine(module_name):
    module = __import__(module_name)
    code = pymixins.get_module_code(module)
    [(_, old_module)] = pymixins.redefine_modules_file_as_code((module, code), replace_max_depth=-1)
    times = 100
    all_time = 0
    for _ in range(times):
        time1 = time.time()
        pymixins.replace_everywhere((old_module, module.__dict__))
        time2 = time.time()
        all_time += time2 - time1
    print("redefining {} average: {:.4f}s".format(module.__name__, all_time / times))
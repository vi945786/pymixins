import weakref

import pymixins
import time
import test.setup as setup
setup.load_c_test()
import c_test

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

    def get_func(self):
        return self.func


class SlotsTest:
    __slots__ = ("func",)

    def __init__(self):
        from test.modify import func
        self.func = func


test_instance = Test()
slot_test_instance = SlotsTest()
c_class = c_test.Class(func)

def run_tests(output):
    current_func = __import__("test").modify.func
    assert_equals(current_func(), output)
    tests = [
        assert_is(modify.func, current_func),
        assert_is(func, current_func),
        assert_is(get_status, current_func),
        assert_is(Test.func, current_func),
        assert_is(test_instance.get_func(), current_func),
        assert_is(slot_test_instance.func, current_func),
        assert_is(func_ref(), current_func),
        assert_is(func_tuple[0], current_func),
        assert_is(func_list[0], current_func),
        assert_is(func_set.copy().pop(), current_func),
        assert_is(list(func_frozenset)[0], current_func),
        assert_is(c_class.ref, current_func)
    ]
    if any(tests):
        tests.insert(0, f"Errors in run_tests('{output}')")
    return (test for test in tests if test)

def assert_is(actual, expected):
    return assert_equals(id(actual), id(expected), _traceback_offset=3)

def assert_equals(actual, expected, /, _traceback_offset=2):
    import traceback
    try:
        assert actual == expected
    except AssertionError:
        stack = traceback.extract_stack()
        return ''.join(traceback.format_list(stack[-_traceback_offset:-_traceback_offset+1]))[:-1] + f" expected '{expected}' but got '{actual}'"
    else:
        return None


def time_redefine(module_name, times=50):
    module = __import__(module_name)
    code = pymixins.get_module_code(module)
    all_time = 0
    for i in range(times):
        [(_, old_module)] = pymixins.redefine_modules_file_as_code((module, code), do_replace=False)
        time1 = time.time()
        pymixins.replace_everywhere((old_module, module.__dict__))
        time2 = time.time()
        all_time += time2 - time1
    print("redefining {} {} times took {:.4f}s with an average of {:.4f}s".format(module.__name__, times, all_time, all_time / times))

import mixin

import modify
import time
from modify import func
from modify import func as get_status
class Test: from modify import func
func_ref = __import__("weakref").ref(func)
func_tuple = (func,)

assert modify.func() == "original"
assert func() == "original"
assert get_status() == "original"
assert Test.func() == "original"
assert func_ref()() == "original"
assert func_tuple[0]() == "original"

with open(mixin.get_module_file("modify")) as file:
    code = file.readlines()
code[1] = "    return 'modified'"
time1 = time.time_ns()
mixin.redefine_modules_file_as_code(("modify", "\n".join(code)))
time2 = time.time_ns()
print(f"{(time2 - time1) / 1_000_000_000}s")

assert modify.func() == "modified"
assert func() == "modified"
assert get_status() == "modified"
assert Test.func() == "modified"
assert func_ref()() == "modified"
assert func_tuple[0]() == "modified"

print("all tests passed")

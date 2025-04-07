import weakref

import mixin
import modify
from modify import func, func as get_status


class Test:
    from modify import func


func_ref = weakref.ref(func)

assert modify.func() == "original"
assert func() == "original"
assert get_status() == "original"
assert Test.func() == "original"
assert func_ref()() == "original"

with open(mixin.get_module_file("modify")) as file:
    code = file.readlines()
code[1] = "\treturn 'modified'"
mixin.redefine_modules_file_as_code(("modify", "\n".join(code)))

assert modify.func() == "modified"
assert func() == "modified"
assert get_status() == "modified"
assert Test.func() == "modified"
assert func_ref()() == "modified"

print("all tests passed")

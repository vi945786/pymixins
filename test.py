import pymixins
import time
import tests

tests.test("original")

with open(pymixins.get_module_file("modify")) as file:
    code = file.readlines()
code[1] = "    return 'modified'"
time1 = time.time_ns()
pymixins.redefine_modules_file_as_code(("modify", "\n".join(code)))
time2 = time.time_ns()
print(f"{(time2 - time1) / 1_000_000_000}s")

tests.test("modified")

print("all tests passed")

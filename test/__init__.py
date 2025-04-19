import sys

from test.tests import *
import test.modify as modify

if __name__ == "__main__":
    tests_errors = list()
    tests_errors.extend(run_tests("original"))

    code = pymixins.get_module_code(modify).split("\n")
    code[1] = "    return 'modified'"
    code = "\n".join(code)
    [(module, old_module)] = pymixins.redefine_modules_file_as_code((modify, code))

    tests_errors.extend(run_tests("modified"))
    if len(tests_errors) == 0:
        print("all tests passed")
    else:
        for e in tests_errors:
            print(e, file=sys.stderr)

    time_redefine("asyncio")
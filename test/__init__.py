import sys

import pymixins
import time
from test.tests import run_tests
import test.modify as modify

if __name__ == "__main__":
    tests_errors = list()
    tests_errors.extend(run_tests("original"))

    code = pymixins.get_module_code(modify).split("\n")
    code[1] = "    return 'modified'"
    code = "\n".join(code)
    [(module, old_module)] = pymixins.redefine_modules_file_as_code((modify, code), replace_max_depth=-1)
    time1 = time.time()
    pymixins.replace_everywhere((old_module, module.__dict__))
    time2 = time.time()
    print("redefining module: {:.4f}s".format((time2 - time1) / 1))

    tests_errors.extend(run_tests("modified"))
    if len(tests_errors) == 0:
        print("all tests passed")
    else:
        for e in tests_errors:
            print(e, file=sys.stderr)
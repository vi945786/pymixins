import os
from setuptools import Extension
from setuptools.command.build_ext import build_ext
from distutils.dist import Distribution

class BuildExt(Distribution):
    def run(self):
        self.cmdclass = {'build_ext': build_ext}
        self.ext_modules = [Extension('c_test', sources=['CTest.c'])]
        build_ext_cmd = self.get_command_obj('build_ext')
        build_ext_cmd.inplace = True
        build_ext_cmd.build_lib = os.path.abspath('.')  # Set output path
        self.run_command('build_ext')

def load_c_test():
    dist = BuildExt()
    dist.script_name = 'setup.py'
    dist.script_args = ['build_ext']
    dist.run()


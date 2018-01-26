from setuptools import find_packages
from os import path, environ
import io
import os
import re

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import numpy as np
import pycparser
import pickle
import sys

def _get_enumlist(obj):
    for _, cc in obj.children():
        if type(cc) is pycparser.c_ast.EnumeratorList:
            return cc
        else:
            return _get_enumlist(cc)

def parse_lrs_classes():
    ## construct path to librealsense/rs.h
    if 'PYRS_INCLUDES' in environ:
        rs_h_filename = path.join(environ['PYRS_INCLUDES'], 'rs.h')

    ## for docs, use locally stored
    elif os.environ.get('READTHEDOCS') == 'True':
        rs_h_filename = './rs.h'

    elif sys.platform == 'win32':
        raise Exception('PYRS_INCLUDES must be set to the location of the librealsense headers!')

    else:
        rs_h_filename = '/usr/local/include/librealsense/rs.h'


    ## if not found, exit
    if not path.exists(rs_h_filename):
        raise Exception('librealsense/rs.h header not found at {}'.format(rs_h_filename))


    # Dynamically extract API version
    api_version = 0
    lrs_globals = {}
    with io.open(rs_h_filename, encoding='latin') as rs_h_file:
        for l in rs_h_file.readlines():
            if 'RS_API' in l:
                key, val = l.split()[1:]
                lrs_globals[key] = val
                api_version = api_version * 100 + int(val)
            if api_version >= 10000:
                break
    lrs_globals['RS_API_VERSION'] = api_version
    # Dynamically generate classes
    ast = pycparser.parse_file(rs_h_filename, use_cpp=True)
    lrs_classes = {}
    for c in ast.ext:
        if c.name in ['rs_capabilities',
                      'rs_stream',
                      'rs_format',
                      'rs_distortion',
                      'rs_ivcam_preset',
                      'rs_option',
                      'rs_preset']:
            e = _get_enumlist(c)

            class_name = c.name
            class_dict = {}
            for i, (_, child) in enumerate(e.children()):
                class_dict[child.name] = i

            name_for_value = {}
            for key, val in class_dict.items():
                name_for_value[val] = key
            class_dict['name_for_value'] = name_for_value
            lrs_classes[class_name] = class_dict
    classes_list = [lrs_globals, lrs_classes]
    with io.open('lrs_parsed_classes', "wb") as ser_classes:
        pickle.dump(classes_list, ser_classes)


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()


# pip's single-source version method as described here:
# https://python-packaging-user-guide.readthedocs.io/single_source_version/
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# fetch include and library directories
inc_dirs = [np.get_include(), '/usr/local/include/librealsense']
lib_dirs = ['/usr/local/lib']

# windows environment variables
if 'PYRS_INCLUDES' in environ:
    inc_dirs.append(environ['PYRS_INCLUDES'])
if 'PYRS_LIBS' in environ:
    lib_dirs.append(environ['PYRS_LIBS'])

# cython extension, dont build if docs
on_rtd = environ.get('READTHEDOCS') == 'True'
if on_rtd:
    module = []
else:
    module = cythonize(
        [Extension(
            name='pyrealsense.rsutilwrapper',
            sources=["pyrealsense/rsutilwrapper.pyx", "pyrealsense/rsutilwrapperc.cpp"],
            libraries=['realsense'],
            include_dirs=inc_dirs,
            library_dirs=lib_dirs,
            extra_compile_args=["-std=c++11"],
            language="c++",)])

# create long description from readme for pypi
here = path.abspath(path.dirname(__file__))
with io.open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

parse_lrs_classes()
setup(name='pyrealsense',
      version=find_version('pyrealsense', '__init__.py'),

      description='Cross-platform ctypes/Cython wrapper to the librealsense library.',
      long_description=long_description,
      author='Antoine Loriette',
      author_email='antoine.loriette@gmail.com',
      url='https://github.com/toinsson/pyrealsense',
      license='Apache',

      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        # 'License :: OSem :: Hardware',
      ],
      keywords='realsense',
      package_data={'pyrealsense': ['lrs_parsed_classes']},
      packages=find_packages(),
      ext_modules=module,
      setup_requires=['numpy', 'cython'],
      install_requires=['numpy', 'cython', 'pycparser', 'six'])

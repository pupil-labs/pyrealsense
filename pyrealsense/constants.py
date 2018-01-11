# -*- coding: utf-8 -*-
# Licensed under the Apache-2.0 License, see LICENSE for details.

"""This module extract the RS_API_VERSION to which pyrealsense is binded and wraps several enums
from rs.h into classes with the same name."""

import pycparser
import io
import pickle

# Platform dependent
import os

import sys
from os import environ, path

loaded_globals = {}
loaded_classes = {}

if getattr(sys, 'frozen', False):
    res_path = os.path.join(sys._MEIPASS, 'pyrealsense')

else:
    res_path = os.path.dirname(__file__)

try:
    with io.open(os.path.join(res_path, 'lrs_parsed_classes'), "rb") as ser2_classes:
        loaded_classes_list = pickle.load(ser2_classes)
        lrs_globals, lrs_classes = loaded_classes_list
        for name, val in lrs_globals.items():
            globals()[name] = val

        for class_name, class_dict in lrs_classes.items():
            class_gen = type(class_name, (object,), class_dict)
            # print("class dict:", class_dict);
            globals()[class_name] = class_gen
except IOError:
    raise

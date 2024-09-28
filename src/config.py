import os
from re import M
from pathlib import Path
import json
from yaml import load, dump

CAMERA_DEVICE = 0
# CAMERA_DEVICE = "D:/video.avi"

def resource_path(relative_path):
    base_path = os.path.abspath("GUI")
    return os.path.join(base_path, relative_path)

MAIN_GUI = resource_path("Main.ui")
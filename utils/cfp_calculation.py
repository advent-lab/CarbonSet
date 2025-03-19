import sys
import os

# Ensure Python can find `eco_chip_enhanced/`
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

# Now, import modules from eco_chip_enhanced
from eco_chip_enhanced import *

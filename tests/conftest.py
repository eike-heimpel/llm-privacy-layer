import os
import sys
import pytest

# Add the app directory to the Python path so that imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 
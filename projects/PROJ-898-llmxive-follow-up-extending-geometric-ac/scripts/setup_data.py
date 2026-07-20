"""
Script to execute data directory setup.
"""
import sys
import os

# Add the code directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
code_dir = os.path.join(project_root, 'code')

if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from setup_data_dirs import main

if __name__ == '__main__':
    sys.exit(main())
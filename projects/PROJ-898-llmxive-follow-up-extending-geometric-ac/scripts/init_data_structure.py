import sys
import os

# Add the project root to the path to allow importing from code/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.setup_data_dirs import main

if __name__ == "__main__":
  sys.exit(main())
"""
Runner script to execute T012 Negative Control Test.
This script is called by the pipeline to verify the negative control.
"""
import sys
from pathlib import Path

# Ensure the tests/integration directory is in the path if running directly
current_file = Path(__file__).resolve()
test_dir = current_file.parent
project_root = test_dir.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_negative_control import main

if __name__ == "__main__":
    main()

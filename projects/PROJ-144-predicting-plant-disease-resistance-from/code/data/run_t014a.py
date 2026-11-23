"""
Wrapper script to execute T014a: Detect label heterogeneity.
This script ensures the task runs as a standalone executable command.
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from detect_label_heterogeneity import main

if __name__ == "__main__":
    sys.exit(main())
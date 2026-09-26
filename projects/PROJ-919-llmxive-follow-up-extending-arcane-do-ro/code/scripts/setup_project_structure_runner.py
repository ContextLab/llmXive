"""
Wrapper script to execute project structure setup from the CLI.
This ensures the structure is created before other scripts run.
"""
import sys
from pathlib import Path

# Add the code directory to the path
code_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_root))

from setup_project_structure import main

if __name__ == "__main__":
    sys.exit(main() or 0)
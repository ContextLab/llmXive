"""
Wrapper script to execute project structure creation from the repository root.
"""
import os
import sys
from pathlib import Path

# Ensure the src package is importable
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir.parent))

from src.setup_project import create_directories, main

if __name__ == "__main__":
    sys.exit(main())
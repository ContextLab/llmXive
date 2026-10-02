"""
Wrapper script to generate manual labels for T007d.
This script calls the logic in code/manual_labels_generator.py.
"""
import sys
import os
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from manual_labels_generator import main

if __name__ == "__main__":
    print("Generating manual labels for T007d...")
    main()
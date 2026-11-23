"""
Runner script to execute T000 verification.
"""
import sys
import os

# Ensure the code directory is in the path
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from verify_spec_alignment import run_verification

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
"""
Wrapper script to expose the off‑CI fMRIPrep preprocessing functionality
under the `src` package namespace. The actual implementation lives in
`code/src/data/preprocess.py`. This thin wrapper simply forwards the
command‑line arguments to that implementation.
"""

import sys
from pathlib import Path

# Ensure the `code` package root is on the import path.
code_root = Path(__file__).resolve().parents[2] / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Import the real main function.
from code.src.data.preprocess import main as _real_main

if __name__ == "__main__":
    _real_main()
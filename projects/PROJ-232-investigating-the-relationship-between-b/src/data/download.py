"""
Wrapper script to expose the download functionality under the `src` package namespace.
The actual implementation lives in `code/src/data/download.py`. This thin wrapper
imports the real `main` function and forwards command‑line execution, ensuring that
the quickstart commands (`python src/data/download.py ...`) work without duplication.
"""
import sys
from pathlib import Path

# Ensure the `code` package directory is on the import path.
# This mirrors the repository layout where the implementation resides under `code/`.
code_root = Path(__file__).resolve().parents[2] / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

# Import the real entry point from the implementation module.
from code.src.data.download import main as _download_main

if __name__ == "__main__":
    _download_main()

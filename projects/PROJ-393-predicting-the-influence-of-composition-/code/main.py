"""
Top‑level entry point for the Heusler‑Alloy pipeline.

The repository stores the real implementation in ``code/src/main.py`` and
provides this thin wrapper so that the quickstart guide can simply run
``python main.py`` from the ``code`` directory.

Running the module as a script forwards to the library entry point
``src.main.main`` and propagates its exit code.
"""
import sys
from pathlib import Path

# Ensure the project root (the directory that contains ``code``) is on ``sys.path``.
# This mirrors the behaviour of the existing scripts that manipulate the path.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.main import main as src_main

if __name__ == "__main__":
    # Forward the command‑line arguments to the library entry point.
    # ``src_main`` returns an integer exit status, which we forward.
    sys.exit(src_main())

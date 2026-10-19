"""
code/src/data/download_gwtc.py

Thin wrapper that invokes the production download implementation located in
``src.data.download``.  The wrapper exists because the original task
specification referred to a script named ``download_gwtc.py`` under
``code/src/data``.  Keeping the logic in a single module (``src.data.download``)
avoids duplication while satisfying the expected import path.

This file ensures that the project's root directory is on ``sys.path`` so
that the absolute import ``src.data.download`` works even when the script
is executed directly (e.g. ``python code/src/data/download_gwtc.py``).
"""

import sys
from pathlib import Path

# Add the project root (two levels up from this file) to sys.path.
# This makes the top‑level ``src`` package importable when the script is
# run as a standalone module.
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.append(str(_project_root))

# Import the actual download implementation.
from src.data.download import main  # noqa: E402

if __name__ == "__main__":
    # Running this module performs the full GWTC download workflow.
    main()

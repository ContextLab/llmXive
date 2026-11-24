"""
Helper script to initialise the canonical project layout.

This script is imported by ``quickstart.md`` during the installation
instructions and can also be run manually:

```bash
python code/setup_project.py
```

It creates the required top‑level directories (``code/``, ``data/raw/``,
``data/processed/``, ``data/final/``, ``tests/``) if they do not already
exist.  The function is idempotent – repeated calls are safe.
"""

import os
from pathlib import Path

def ensure_directories() -> None:
    """Create the standard project directories if they are missing."""
    root = Path(__file__).resolve().parent.parent  # project root
    dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "final",
        root / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_directories()
    print("Project layout verified/created.")
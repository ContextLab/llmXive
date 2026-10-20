"""
create_layout.py

This script establishes the canonical project directory layout required by
task T001.  It creates the top‑level data folders and ensures that every
package directory under ``code/`` contains an ``__init__.py`` file so that
imports work correctly.

The script is safe to run multiple times – existing directories and files
are left untouched.
"""

import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create a directory (including parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def ensure_init(path: Path) -> None:
    """Create an ``__init__.py`` file in ``path`` if missing."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            "# -*- coding: utf-8 -*-\\n"
            "\"\"\"Package marker for {}.\"\"\"\\n".format(path.name)
        )

def main() -> int:
    # Top‑level data directories
    data_root = Path("data")
    for sub in ["raw", "processed", "results", "metadata", "figures"]:
        ensure_dir(data_root / sub)

    # Ensure package __init__ files
    for pkg in [Path("code/config"), Path("code/utils")]:
        ensure_dir(pkg)          # in case the folder itself is missing
        ensure_init(pkg)

    # Ensure ``code`` is a package (helps some import styles)
    ensure_init(Path("code"))

    print("Project layout created/verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
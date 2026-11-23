"""
Stand‑alone script to download raw Materials Project alloy data.

The script is deliberately lightweight: it imports the public function
``fetch_materials_project_data`` from ``code._download_logic`` and executes
it.  The resulting JSON file is written to ``data/raw/mp_raw.json``.
Running this script is the concrete verification step for task **T009a**.
"""

import sys
from pathlib import Path

# Ensure the project root is on the Python path so that ``code`` can be imported.
root = Path(__file__).resolve().parents[2]
if str(root) not in sys.path:
    sys.path.append(str(root))

from _download_logic import fetch_materials_project_data

def main() -> None:
    """
    Execute the Materials Project extraction.  Any exception propagates to
    the caller so that the CI system can detect a failure.
    """
    fetch_materials_project_data()

if __name__ == "__main__":
    main()

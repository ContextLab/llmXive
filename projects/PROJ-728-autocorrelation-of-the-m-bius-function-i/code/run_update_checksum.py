"""
Script to (re)compute the SHA‑256 checksum of the packed Möbius array
and ensure it is recorded in the manifest. This is invoked as part of
the T003 implementation to guarantee that the checksum test passes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the checksum updater from the project.
from code.update_mobius_checksum import main as update_checksum

def _main() -> int:
    try:
        update_checksum()
        return 0
    except Exception as exc:
        print(f"Checksum update failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(_main())
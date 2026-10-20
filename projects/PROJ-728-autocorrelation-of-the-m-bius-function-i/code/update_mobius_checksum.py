"""
Thin wrapper used by ``code.sieve.save_mobius_array`` to update the
checksum manifest after the Möbius files are written.
"""

from __future__ import annotations

# Import the compute function from the sibling module.
from .checksum import compute_checksums

def main() -> None:
    """Update the checksum manifest."""
    compute_checksums()

if __name__ == "__main__":
    main()
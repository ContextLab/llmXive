"""
Helper module used by ``code.sieve.save_mobius_array`` to update the
checksum manifest after the Möbius arrays have been written.

The original implementation was missing or broken, which caused the
``data/checksums/manifest.sha256`` verification step in the tests to fail.
This lightweight wrapper simply invokes the checksum‑generation script
defined in ``code.generate_checksum``.
"""

from __future__ import annotations

from .generate_checksum import generate_checksum_manifest

def main() -> None:
    """Entry point called from ``code.sieve.save_mobius_array``."""
    generate_checksum_manifest()

if __name__ == "__main__":
    main()

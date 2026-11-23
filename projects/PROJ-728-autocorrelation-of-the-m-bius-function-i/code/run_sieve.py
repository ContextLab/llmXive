"""run_sieve.py
----------------
Execute the Möbius sieve to generate the raw and packed Möbius arrays,
and compute the SHA‑256 checksum manifest.

This script is used to satisfy task T002 by producing the required
artifacts:
  - data/raw/mobius_array.npy
  - data/raw/mobius_2bit.npy
  - data/checksums/manifest.sha256

It simply invokes the ``main`` entry point of ``code.sieve``.
"""

from __future__ import annotations

from sieve import main


if __name__ == "__main__":
    # Run the sieve with default parameters (N = 10_000_000).
    main()
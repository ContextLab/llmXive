"""
Generate a list of prime numbers up to a given maximum (default 50 000) using
the Sieve of Eratosthenes implementation provided in ``utils.prime_sieve``.
The script writes the primes to ``data/raw/primes_up_to_50000.csv`` with a
single column header ``prime`` and prints the SHA‑256 checksum of the
generated file to stdout.

This utility is used by downstream steps (partition counting,
feature engineering, etc.) and is also invoked directly by the quick‑start
guide via:

    python code/generate_primes.py

The default ``n_max`` matches the project‑wide limit required for all
analyses.
"""

import argparse
import csv
import hashlib
import sys
from pathlib import Path

from utils.prime_sieve import generate_primes
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DEFAULT_N_MAX = 50000
DEFAULT_OUTPUT = paths.data("raw", "primes_up_to_50000.csv")


def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


def write_primes(primes: list[int], output_path: Path) -> None:
    """Write *primes* to *output_path* as a CSV with a ``prime`` header."""
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["prime"])
        for p in primes:
            writer.writerow([p])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate all prime numbers up to a given maximum."
    )
    parser.add_argument(
        "--n-max",
        type=int,
        default=DEFAULT_N_MAX,
        help=f"Maximum integer to test for primality (default: {DEFAULT_N_MAX})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Path to the output CSV file (default: data/raw/primes_up_to_50000.csv)",
    )
    args = parser.parse_args()

    n_max = args.n_max
    output_path = Path(args.output)

    if n_max < 2:
        log.error("n_max must be >= 2 to contain any primes.")
        sys.exit(1)

    log.info(f"Generating primes up to {n_max}...")
    primes = generate_primes(n_max)
    log.info(f"Generated {len(primes)} primes.")

    log.info(f"Writing primes to {output_path}...")
    write_primes(primes, output_path)

    checksum = compute_sha256(output_path)
    print(f"SHA-256 checksum: {checksum}")

    log.info("Prime generation complete.")


if __name__ == "__main__":
    main()

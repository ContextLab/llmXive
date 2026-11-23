"""Verify specification amendment for network topology generation.

This script checks that the specification file contains the required
phrasing indicating a synthetic regular ring lattice of N=500 nodes and
that it does *not* contain the phrase "ca-AstroPh". If both conditions are
satisfied the script exits with status 0. Otherwise it prints an error
identifier and exits with status 1.

Usage:
    python scripts/verify_spec.py
"""
import sys
from pathlib import Path

def main() -> None:
    # Path to the specification markdown file.
    spec_path = Path(__file__).resolve().parents[1] / "specs" / "001-exploring-the-role-of-network-topology-synchronization" / "spec.md"

    if not spec_path.is_file():
        print("SPEC_MISSING")
        sys.exit(1)

    try:
        content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"SPEC_READ_ERROR: {e}")
        sys.exit(1)

    # Condition 1: required text must be present.
    required_phrase = "synthetic regular ring lattice of N=500 nodes"
    if required_phrase not in content:
        print("SPEC_MISSING")
        sys.exit(1)

    # Condition 2: prohibited text must NOT be present.
    prohibited_phrase = "ca-AstroPh"
    if prohibited_phrase in content:
        print("SPEC_CONTRADICTION")
        sys.exit(1)

    # All checks passed.
    sys.exit(0)

if __name__ == "__main__":
    main()
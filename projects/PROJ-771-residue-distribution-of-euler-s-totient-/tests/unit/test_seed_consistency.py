"""
Verify that deterministic seeding produces identical residue files
across repeated runs with the same configuration.
"""

import hashlib
import json
from pathlib import Path

import pytest

# Ensure the project ``code`` package is importable.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from run_analysis import parse_args, pin_orchestration_seed, run_sieve_stage

def _file_hash(path: Path) -> str:
    """Return SHA‑256 hash of the file's bytes."""
    with path.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def test_seed_consistency(tmp_path: Path, monkeypatch):
    """
    Run the sieve stage twice with identical configuration and
    assert that the generated ``data/raw/residues_*.json`` files are
    byte‑identical.

    We use run_sieve_stage instead of run_orchestration to isolate the
    seeding verification from potential failures in the stats or
    visualization stages.
    """
    # Switch the current working directory to a temporary location so that
    # all relative paths (``data/...``) stay inside the temporary directory.
    monkeypatch.chdir(tmp_path)

    # ------------------------------------------------------------------
    # First run
    # ------------------------------------------------------------------
    args = parse_args()
    args.N = 200               # modest size – fast for the test suite
    args.primes = [3, 5]       # two supported primes
    args.seed = 123            # deterministic seed
    config = {
        "N": args.N,
        "primes": args.primes,
        "seed": args.seed,
        "memory_limit_mb": 6000,
        "memory_check_interval": 10_000,
    }

    # Pin the seeds and execute the sieve stage.
    pin_orchestration_seed(config)
    run_sieve_stage(config)

    # Record hashes of the generated residue files.
    hashes_run1 = {}
    for p in args.primes:
        fp = Path("data/raw", f"residues_{p}_{args.N}.json")
        assert fp.is_file(), f"Residue file for prime {p} missing after first run"
        hashes_run1[p] = _file_hash(fp)

    # ------------------------------------------------------------------
    # Second run (same configuration)
    # ------------------------------------------------------------------
    # Re‑pin the seeds to guarantee the RNG state is reset.
    pin_orchestration_seed(config)
    run_sieve_stage(config)

    # Record hashes again.
    hashes_run2 = {}
    for p in args.primes:
        fp = Path("data/raw", f"residues_{p}_{args.N}.json")
        assert fp.is_file(), f"Residue file for prime {p} missing after second run"
        hashes_run2[p] = _file_hash(fp)

    # The hashes must match exactly.
    assert hashes_run1 == hashes_run2, "Residue files differ between runs despite identical seed"

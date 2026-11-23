"""
Integration test for seed consistency (T004).

The full residue-generation pipeline (seed pinning -> linear sieve ->
residue aggregation -> ResidueDataset JSON serialisation) is executed
twice with the same configuration (identical N, primes and seed) and the
resulting ``ResidueDataset`` files are compared byte-for-byte.

Note on scope: the end-to-end CLI orchestrator (``code/run_analysis.py``)
currently cannot be imported because ``code/stats.py`` (task T008, still
open) contains an invalid ``scipy.stats`` import.  The deterministic
data-generation path that seed pinning governs — the sieve and residue
aggregation stages — is exercised here directly in-process, which is
exactly the stage whose output files the task requires to be
byte-identical.  Once T008 repairs ``stats.py`` the same determinism
guarantee extends to the CLI run unchanged, because the CLI calls these
very functions after ``pin_seeds``.
"""

import json
import random
import sys
from pathlib import Path

import numpy as np
import yaml

# Make the sibling modules under code/ importable regardless of the
# working directory pytest was launched from.
CODE_DIR = Path(__file__).resolve().parents[2] / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from seed import pin_seeds, get_seed  # noqa: E402
from sieve import (  # noqa: E402
    compute_phi_linear_sieve,
    compute_residues,
    save_residue_dataset,
)

# Small parameters so the test runs in seconds.
N = 200
PRIMES = [3, 5]
SEED = 12345


def _run_residue_pipeline(out_dir: Path) -> dict:
    """
    Run the deterministic residue-generation pipeline once.

    Pins the global seeds, computes φ(n) for n ≤ N with the linear
    sieve, aggregates the residues for each prime and writes the
    ``ResidueDataset`` JSON artefacts into ``out_dir``.

    Returns
    -------
    dict
    Mapping ``prime -> raw file bytes`` of the written JSON files.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Pin the seeds exactly as the orchestrator does before any
    # stochastic or deterministic computation takes place.
    pin_seeds(SEED)
    assert get_seed() == SEED, "get_seed() must return the pinned seed"

    phi_vals = compute_phi_linear_sieve(N)

    outputs = {}
    for prime in PRIMES:
        counts = compute_residues(phi_vals, prime)
        path = out_dir / f"residues_{prime}_{N}.json"
        save_residue_dataset(counts, prime, N, str(path))
        outputs[prime] = path.read_bytes()
    return outputs


def test_residue_files_are_byte_identical(tmp_path):
    """
    Run the pipeline twice with the same config and verify that the
    raw residue JSON files are identical byte-for-byte.
    """
    first = _run_residue_pipeline(tmp_path / "run1")
    second = _run_residue_pipeline(tmp_path / "run2")

    for prime in PRIMES:
        assert first[prime] == second[prime], (
            f"Residue file for prime {prime} differs between runs "
            "despite identical configuration and pinned seed"
        )

    # Sanity-check the JSON payload itself (real data, not placeholders).
    for prime in PRIMES:
        data = json.loads(first[prime])
        assert data["prime_modulus"] == prime
        assert data["total_count"] == N
        freq = data["frequency_map"]
        assert sum(int(v) for v in freq.values()) == N
        assert set(freq.keys()) == {str(r) for r in range(prime)}

def test_seed_pinning_makes_rng_deterministic():
    """Pinned seeds must yield identical random / NumPy streams."""
    pin_seeds(SEED)
    draw_a = (random.random(), random.random(), float(np.random.random()))
    pin_seeds(SEED)
    draw_b = (random.random(), random.random(), float(np.random.random()))
    assert draw_a == draw_b, "RNG streams differ despite identical seeds"

def test_get_seed_raises_before_pinning():
    """get_seed() must fail loudly when no seed has been pinned yet."""
    import importlib
    import seed as seed_module

    # Reload the module to reset its internal _current_seed to None.
    importlib.reload(seed_module)
    try:
        seed_module.get_seed()
    except RuntimeError:
        return  # expected
    finally:
        # Re-pin so subsequent tests in this session see a valid seed.
        pin_seeds(SEED)
    raise AssertionError("get_seed() should raise RuntimeError before pin_seeds()")

def test_seed_persisted_to_config():
    """pin_seeds must store the seed in code/config.yaml."""
    pin_seeds(SEED)
    cfg_path = CODE_DIR / "config.yaml"
    assert cfg_path.is_file(), "config.yaml must exist after pin_seeds()"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    assert cfg.get("seed") == SEED, "config.yaml must record the pinned seed"
"""
Unit tests for the contract‑validation utility (T019).

The tests create minimal but valid JSON artefacts for a small ``N`` and
a single prime, then invoke :func:`validate_contracts.validate_all` to
ensure that the artefacts pass validation.  A second test mutates one
artefact to violate the schema and checks that a ``ResearchIncompleteError``
is raised.
"""

import json
from pathlib import Path

import pytest

from validate_contracts import validate_all
from exceptions import ResearchIncompleteError

# Helper to write a JSON file under the project's data directory.
def _write_json(relative_path: str, content: dict) -> Path:
    p = Path(__file__).parents[2] / "data" / relative_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2)
    return p

def test_validate_contracts_success(tmp_path):
    """
    Create a valid residue dataset and statistical result, then verify
    that ``validate_all`` succeeds without raising.
    """
    N = 10
    prime = 3

    # Minimal valid dataset matching ``dataset.schema.yaml``.
    dataset = {
        "prime_modulus": prime,
        "total_count": N,
        "frequency_map": {str(r): N // prime for r in range(prime)},
        "computation_seed": 42
    }

    # Minimal valid statistical result matching ``statistical_result.schema.yaml``.
    statistical = {
        "test_type": "chi_squared",
        "test_statistic": 0.0,
        "p_value": 1.0,
        "degrees_of_freedom": prime - 1,
        "method": "asymptotic",
        "expected_counts": [N / prime] * prime,
        "observed_counts": [N // prime] * prime,
        "uniformity_hypothesis": True,
        "metadata": {
            "timestamp": "2026-10-20T00:00:00Z",
            "python_version": "3.11",
            "n_processed": N,
            "peak_memory_mb": 10.0,
            "wall_time_sec": 0.1,
            "limit_reached": False
        }
    }

    # Write artefacts to the expected locations.
    _write_json(f"raw/residues_{prime}_{N}.json", dataset)
    _write_json(f"processed/stats_{prime}_{N}.json", statistical)

    # Should not raise.
    validate_all(N, [prime])

def test_validate_contracts_failure(tmp_path):
    """
    Corrupt a required field and verify that ``ResearchIncompleteError`` is raised.
    """
    N = 10
    prime = 3

    # Valid dataset.
    dataset = {
        "prime_modulus": prime,
        "total_count": N,
        "frequency_map": {str(r): N // prime for r in range(prime)},
        "computation_seed": 42
    }
    _write_json(f"raw/residues_{prime}_{N}.json", dataset)

    # Invalid statistical result: missing required ``test_type`` field.
    invalid_stat = {
        # "test_type": "chi_squared",   # Intentionally omitted
        "test_statistic": 0.0,
        "p_value": 1.0,
        "degrees_of_freedom": prime - 1,
        "method": "asymptotic",
        "expected_counts": [N / prime] * prime,
        "observed_counts": [N // prime] * prime,
        "uniformity_hypothesis": True,
        "metadata": {
            "timestamp": "2026-10-20T00:00:00Z",
            "python_version": "3.11",
            "n_processed": N,
            "peak_memory_mb": 10.0,
            "wall_time_sec": 0.1,
            "limit_reached": False
        }
    }
    _write_json(f"processed/stats_{prime}_{N}.json", invalid_stat)

    with pytest.raises(ResearchIncompleteError) as exc:
        validate_all(N, [prime])

    assert "test_type" in str(exc.value)
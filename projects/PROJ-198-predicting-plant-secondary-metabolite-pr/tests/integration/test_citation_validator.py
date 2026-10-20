"""
Integration test for the citation‑validator script.
"""

import sys
from pathlib import Path

import pytest

# The script exits via sys.exit; capture the SystemExit
def test_citation_validator_success(tmp_path, monkeypatch):
    # Create dummy required artefacts
    aligned = Path("data/processed/aligned_matrix.csv")
    metrics = Path("data/processed/model_metrics.json")
    aligned.parent.mkdir(parents=True, exist_ok=True)
    metrics.parent.mkdir(parents=True, exist_ok=True)
    aligned.write_text("species,feat1,feat2")
    metrics.write_text("{}")

    # Ensure the state file is empty before run
    from utils.artifact import STATE_FILE
    if STATE_FILE.is_file():
        STATE_FILE.unlink()

    # Run the validator – it should exit with code 0
    with pytest.raises(SystemExit) as excinfo:
        import importlib
        import code.utils.citation_validator as cv
        cv.main()
    assert excinfo.value.code == 0

    # After execution the state file must contain hashes for both artefacts
    from utils.artifact import _load_state
    state = _load_state()
    rel_aligned = aligned.resolve().relative_to(Path(__file__).parents[3])
    rel_metrics = metrics.resolve().relative_to(Path(__file__).parents[3])
    assert str(rel_aligned) in state
    assert str(rel_metrics) in state

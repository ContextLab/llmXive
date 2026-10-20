"""
Ensure that the citation validator aborts with a non‑zero exit code when a required
artefact is missing.
"""

import pytest

def test_validator_fails_when_artifact_missing(tmp_path, monkeypatch):
    # Ensure required artefacts do NOT exist
    aligned = Path("data/processed/aligned_matrix.csv")
    metrics = Path("data/processed/model_metrics.json")
    if aligned.is_file():
        aligned.unlink()
    if metrics.is_file():
        metrics.unlink()

    # Run validator and expect SystemExit with non‑zero code
    with pytest.raises(SystemExit) as excinfo:
        import importlib
        import code.utils.citation_validator as cv
        cv.main()
    assert excinfo.value.code != 0

import pathlib

import pytest

from code.main import run_pipeline
from config import get_processed_dir, get_raw_dir

@pytest.mark.integration
def test_us1_small_sample(tmp_path: pathlib.Path, monkeypatch):
    """
    End‑to‑end integration test for US‑1 on a tiny sample.
    The test monkey‑patches the configuration directories to a temporary
    location so the real repository is not polluted.
    """
    # Redirect config directories to the temporary path.
    monkeypatch.setattr("config.get_raw_dir", lambda: tmp_path / "raw")
    monkeypatch.setattr("config.get_processed_dir", lambda: tmp_path / "processed")

    # Ensure the pipeline runs without raising.
    run_pipeline()

    # Verify that both required CSVs exist.
    processed = tmp_path / "processed"
    assert (processed / "clone_metrics.csv").exists()
    assert (processed / "perplexity_scores.csv").exists()
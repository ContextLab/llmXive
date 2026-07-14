"""
Integration test that runs the full pipeline on a very small sample
and checks that the two processed CSV artefacts are produced.
"""
import pathlib

from main import run_pipeline

def test_full_pipeline_small_sample(tmp_path: pathlib.Path, monkeypatch):
    # Redirect data directories to the temporary location.
    monkeypatch.setattr(
        "data_loader.Path", lambda *args, **kwargs: tmp_path / "raw"
    )
    monkeypatch.setattr(
        "ast_cloner.Path", lambda *args, **kwargs: tmp_path / "processed"
    )
    # Run pipeline.
    rc = run_pipeline()
    assert rc == 0
    # Verify artefacts exist.
    assert (tmp_path / "processed" / "clone_metrics.csv").exists()
    assert (tmp_path / "processed" / "perplexity_scores.csv").exists()
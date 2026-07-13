import pathlib

from main import run_pipeline

def test_pipeline_generates_all_outputs(tmp_path, monkeypatch):
    # Ensure a clean environment – remove any existing artefacts
    for p in [
        pathlib.Path("data/raw/github-code-sample.csv"),
        pathlib.Path("data/processed/clone_metrics.csv"),
        pathlib.Path("data/processed/perplexity_scores.csv"),
        pathlib.Path("data/analysis/correlation_results.csv"),
    ]:
        if p.is_file():
            p.unlink()
    # Run the full pipeline
    run_pipeline()
    # Verify that each expected file now exists
    assert pathlib.Path("data/raw/github-code-sample.csv").is_file()
    assert pathlib.Path("data/processed/clone_metrics.csv").is_file()
    assert pathlib.Path("data/processed/perplexity_scores.csv").is_file()
    assert pathlib.Path("data/analysis/correlation_results.csv").is_file()

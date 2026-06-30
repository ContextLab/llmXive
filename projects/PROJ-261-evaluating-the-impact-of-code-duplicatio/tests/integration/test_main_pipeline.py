"""
Integration test that exercises the full US‑1 pipeline via ``code/main.py``.
The test verifies that the two required CSV artefacts are created.
"""

import subprocess
from pathlib import Path


def test_main_pipeline_creates_outputs(tmp_path: Path) -> None:
    """
    Run ``python code/main.py`` in a subprocess and assert that the expected
    CSV files exist after execution.
    """
    # Ensure a clean working directory.
    project_root = Path(__file__).resolve().parents[3]
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"

    # Remove artefacts if they exist from a previous run.
    for p in [raw_dir / "github-code-sample.csv", processed_dir / "clone_metrics.csv", processed_dir / "perplexity_scores.csv"]:
        if p.exists():
            p.unlink()

    # Execute the pipeline.
    result = subprocess.run(
        [sys.executable, "code/main.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify outputs.
    assert (raw_dir / "github-code-sample.csv").exists(), "Raw CSV missing"
    assert (processed_dir / "clone_metrics.csv").exists(), "Clone metrics CSV missing"
    assert (processed_dir / "perplexity_scores.csv").exists(), "Perplexity CSV missing"
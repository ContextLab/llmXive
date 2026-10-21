import subprocess
import sys
from pathlib import Path
import pytest
from llmxive_toolkit import paths

@pytest.mark.timeout(300)
def test_pipeline_runs_and_produces_csv():
    csv_path = paths.data("processed", "diffusion_results.csv")
    if csv_path.exists():
        csv_path.unlink()

    result = subprocess.run(
        [sys.executable, "code/pipeline.py", "--solvent", "water", "--duration", "1", "--seed", "0"],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"
    assert csv_path.is_file(), "CSV not created"
    with csv_path.open() as f:
        lines = f.readlines()
    assert len(lines) >= 2, "CSV missing data"
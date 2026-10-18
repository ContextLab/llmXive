"""Verify the directory structure required by task T001a exists.

The structure follows plan.md: raw data, processed data, models, and
evaluation results directories all live under the project's code/ tree.
"""
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1] / "code"

def test_raw_data_dir_exists():
    assert (CODE_ROOT / "data" / "raw").is_dir()

def test_processed_data_dir_exists():
    assert (CODE_ROOT / "data" / "processed").is_dir()

def test_models_dir_exists():
    assert (CODE_ROOT / "models").is_dir()

def test_evaluation_results_dir_exists():
    assert (CODE_ROOT / "evaluation" / "results").is_dir()

def test_setup_script_runs_idempotently():
    import subprocess
    import sys
    script = CODE_ROOT / "setup_project_structure.py"
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "verified OK" in result.stdout
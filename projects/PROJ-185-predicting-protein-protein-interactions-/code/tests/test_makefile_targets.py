import subprocess
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MAKEFILE_PATH = PROJECT_ROOT / "Makefile"

@pytest.fixture
def make_target():
    def _run_target(target):
        result = subprocess.run(
            ["make", "-C", str(PROJECT_ROOT), target, "-n"],
            capture_output=True,
            text=True
        )
        return result
    return _run_target

def test_makefile_exists():
    assert MAKEFILE_PATH.exists(), "Makefile not found at project root"

def test_help_target(make_target):
    result = make_target("help")
    assert result.returncode == 0
    assert "Available targets:" in result.stdout

def test_all_target_syntax(make_target):
    result = make_target("all")
    assert result.returncode == 0
    assert "Running full pipeline" in result.stdout

def test_evaluate_target_syntax(make_target):
    result = make_target("evaluate")
    assert result.returncode == 0
    assert "Running Evaluation" in result.stdout

def test_enrich_target_syntax(make_target):
    result = make_target("enrich")
    assert result.returncode == 0
    assert "Running Enrichment" in result.stdout

def test_clean_target_syntax(make_target):
    result = make_target("clean")
    assert result.returncode == 0
    assert "Cleaning up" in result.stdout

def test_validate_target_syntax(make_target):
    result = make_target("validate")
    assert result.returncode == 0
    assert "Running Validation" in result.stdout

def test_sensitivity_target_syntax(make_target):
    result = make_target("sensitivity")
    assert result.returncode == 0
    assert "Running Sensitivity Analysis" in result.stdout

def test_reproducibility_check_target_syntax(make_target):
    result = make_target("reproducibility-check")
    assert result.returncode == 0
    assert "Running Reproducibility Check" in result.stdout

def test_makefile_calls_python_scripts():
    """Verify that the Makefile references the expected Python script paths."""
    with open(MAKEFILE_PATH, "r") as f:
        content = f.read()

    expected_scripts = [
        "code/src/pipeline/download.py",
        "code/src/pipeline/batch_correct.py",
        "code/src/pipeline/confound_regression.py",
        "code/src/pipeline/normalize.py",
        "code/src/pipeline/filter.py",
        "code/src/pipeline/correlation_raw.py",
        "code/src/pipeline/fdr_correction.py",
        "code/src/pipeline/correlation_extract.py",
        "code/src/pipeline/mapping.py",
        "code/src/pipeline/export_edges.py",
        "code/src/pipeline/download_string.py",
        "code/src/pipeline/negative_sampling.py",
        "code/src/pipeline/aggregate_metrics.py",
        "code/src/pipeline/evaluate.py",
        "code/src/pipeline/baseline.py",
        "code/src/pipeline/enrichment.py",
        "code/src/pipeline/sensitivity_analysis.py",
        "code/src/pipeline/reproducibility_check.py",
        "code/src/pipeline/validate.py",
    ]

    for script in expected_scripts:
        assert script in content, f"Makefile missing reference to {script}"
import os
from pathlib import Path

def test_project_root_exists():
    """Verify the main project directory exists."""
    root = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    assert root.exists(), f"Project root {root} does not exist"
    assert root.is_dir(), f"{root} is not a directory"

def test_code_directory_exists():
    """Verify the code directory exists."""
    root = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    code_dir = root / "code"
    assert code_dir.exists(), f"Code directory {code_dir} does not exist"

def test_data_directory_structure():
    """Verify data directory subdirectories exist."""
    root = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    data_dir = root / "data"
    assert (data_dir / "raw").exists(), "data/raw missing"
    assert (data_dir / "processed").exists(), "data/processed missing"
    assert (data_dir / "contracts").exists(), "data/contracts missing"

def test_results_directory_structure():
    """Verify results directory subdirectories exist."""
    root = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    results_dir = root / "results"
    assert (results_dir / "metrics").exists(), "results/metrics missing"
    assert (results_dir / "plots").exists(), "results/plots missing"
    assert (results_dir / "artifacts").exists(), "results/artifacts missing"

def test_tests_directory_structure():
    """Verify tests directory subdirectories exist."""
    root = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    tests_dir = root / "tests"
    assert (tests_dir / "unit").exists(), "tests/unit missing"
    assert (tests_dir / "integration").exists(), "tests/integration missing"
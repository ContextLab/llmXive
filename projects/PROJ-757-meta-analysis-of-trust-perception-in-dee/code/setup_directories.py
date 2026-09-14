import os
from pathlib import Path

def setup_directories() -> None:
    """
    Creates the necessary directories for the project.
    """
    base_dir = Path(".")
    code_dir = base_dir / "code"
    data_dir = base_dir / "data"
    results_dir = base_dir / "results"
    tests_dir = base_dir / "tests"

    code_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    search_results_dir = data_dir / "search_results"
    screening_dir = data_dir / "screening"
    harmonized_dir = data_dir / "harmonized"

    search_results_dir.mkdir(parents=True, exist_ok=True)
    screening_dir.mkdir(parents=True, exist_ok=True)
    harmonized_dir.mkdir(parents=True, exist_ok=True)

    unit_tests_dir = tests_dir / "unit"
    integration_tests_dir = tests_dir / "integration"

    unit_tests_dir.mkdir(parents=True, exist_ok=True)
    integration_tests_dir.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    setup_directories()
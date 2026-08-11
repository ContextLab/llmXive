import os
from pathlib import Path

def main():
    """Creates the project directory structure."""
    base_dir = Path(".")  # Current working directory

    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    explanation_tiers_dir = data_dir / "explanation_tiers"
    explanation_tiers_dir.mkdir(parents=True, exist_ok=True)

    simulation_results_dir = data_dir / "simulation_results"
    simulation_results_dir.mkdir(parents=True, exist_ok=True)

    code_dir = base_dir / "code"
    code_dir.mkdir(parents=True, exist_ok=True)

    tests_dir = base_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    docs_dir = base_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()

import os
import sys
from pathlib import Path

def main():
    """Creates the necessary data and artifact directories."""
    base_dir = Path("projects/PROJ-484-the-impact-of-visual-attention-on-recall")
    data_raw = base_dir / "data" / "raw"
    data_processed = base_dir / "data" / "processed"
    artifacts_figures = base_dir / "artifacts" / "figures"
    artifacts_logs = base_dir / "artifacts" / "logs"
    code_dir = base_dir / "code"
    tests_dir = base_dir / "tests"

    for dir in [data_raw, data_processed, artifacts_figures, artifacts_logs, code_dir, tests_dir]:
        dir.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main()
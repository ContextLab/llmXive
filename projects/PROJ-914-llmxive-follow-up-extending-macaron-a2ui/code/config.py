import os
from pathlib import Path
from typing import Final

PROJECT_ROOT = Path(__file__).parent.parent
RANDOM_SEED: Final[int] = 42

def get_raw_data_path() -> Path:
    return PROJECT_ROOT / "data" / "raw"

def get_processed_data_path() -> Path:
    return PROJECT_ROOT / "data" / "processed"

def get_annotated_data_path() -> Path:
    return PROJECT_ROOT / "data" / "annotated" / "labeled.csv"

def get_holdout_data_path() -> Path:
    return PROJECT_ROOT / "data" / "holdout" / "human_scores.json"

def get_figures_path() -> Path:
    return PROJECT_ROOT / "figures"

def ensure_dirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Annotated Data: {get_annotated_data_path()}")
    print(f"Random Seed: {RANDOM_SEED}")

from __future__ import annotations
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from reproducibility.logs import log_operation, get_logger

@log_operation
def load_cleaned_knots() -> pd.DataFrame:
    return pd.read_csv(Path("data/processed/knots_cleaned.csv"))

@log_operation
def count_knots_per_crossing_number(df: pd.DataFrame) -> Dict[int, int]:
    return df["crossing_number"].value_counts().to_dict()

@log_operation
def generate_dataset_counts_report(counts: Dict[int, int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)

def main() -> None:
    logger = get_logger()
    logger.info("Generating dataset counts")
    df = load_cleaned_knots()
    counts = count_knots_per_crossing_number(df)
    generate_dataset_counts_report(counts, Path("data/processed/dataset_counts.json"))
    logger.info("Dataset counts report generated")

if __name__ == "__main__":
    main()

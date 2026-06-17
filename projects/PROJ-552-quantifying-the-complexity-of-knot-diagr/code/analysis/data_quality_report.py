from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd
from reproducibility.logs import log_operation, get_logger

@log_operation
def load_cleaned_knots_data() -> pd.DataFrame:
    return pd.read_csv(Path("data/processed/knots_cleaned.csv"))

@log_operation
def compute_null_percentages(df: pd.DataFrame) -> Dict[str, float]:
    total = len(df)
    return {col: (df[col].isna().sum() / total) * 100 for col in df.columns}

@log_operation
def write_report(nulls: Dict[str, float], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for col, pct in nulls.items():
            f.write(f"{col}: {pct:.2f}% null\n")

def main() -> None:
    logger = get_logger()
    logger.info("Generating data quality report")
    df = load_cleaned_knots_data()
    nulls = compute_null_percentages(df)
    write_report(nulls, Path("data/processed/data_quality_report.txt"))
    logger.info("Data quality report generated")

if __name__ == "__main__":
    main()

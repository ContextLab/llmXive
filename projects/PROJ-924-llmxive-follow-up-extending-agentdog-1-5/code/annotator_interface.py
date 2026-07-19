import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from config import get_path, ensure_directories
from utils import save_csv_file

def stratify_logs(drift_scores_path: Path, top_pct: float = 0.1, bottom_pct: float = 0.1) -> pd.DataFrame:
    """
    Stratify logs based on drift scores.
    Returns a dataframe with bins.
    """
    df = pd.read_csv(drift_scores_path)
    df = df.sort_values("drift_score")

    n = len(df)
    top_n = int(n * top_pct)
    bottom_n = int(n * bottom_pct)

    # Create bins
    df["bin"] = "middle"
    df.loc[:bottom_n-1, "bin"] = "bottom"
    df.loc[-top_n:, "bin"] = "top"

    return df

def export_stratified_bins(df: pd.DataFrame, output_dir: Path) -> None:
    """Export stratified bins as blinded CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for bin_name in ["top", "bottom", "middle"]:
        subset = df[df["bin"] == bin_name].copy()
        # Blind: remove drift_score
        if "drift_score" in subset.columns:
            subset = subset.drop(columns=["drift_score"])

        out_path = output_dir / f"annotation_{bin_name}.csv"
        subset.to_csv(out_path, index=False)
        print(f"Exported {bin_name} bin to {out_path}")

def prepare_annotation_interface(drift_scores_path: Path) -> None:
    """
    Prepare the annotation interface by stratifying and exporting blinded CSVs.
    """
    ensure_directories()
    df = stratify_logs(drift_scores_path)
    export_stratified_bins(df, get_path("output_dir"))

def main():
    """Main entry point."""
    scores_path = get_path("output_dir") / "drift_scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"Drift scores not found: {scores_path}")
    prepare_annotation_interface(scores_path)

if __name__ == "__main__":
    main()

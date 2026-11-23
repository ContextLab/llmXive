"""
Generate labeled trajectories by appending hacking labels to divergence data.

This script reads the aggregated divergence data (output of US1), applies the
hacking detection logic (from T022), and generates the final labeled dataset.

It preserves the separation of concerns:
- US1 (Ingestion): Computes G(t) and Delta G(t)
- US2 (Detection): Computes labels based on thresholds

Output:
    data/processed/trajectories_labeled.csv
"""

import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Import from project modules
from code.config import get_project_root
from code.detector import load_divergence_data, apply_hacking_labels


def main():
    """
    Main entry point for generating labeled trajectories.

    1. Loads divergence data from data/processed/trajectories_divergence.csv
    2. Applies hacking detection logic to generate 'hacked_label'
    3. Saves the result to data/processed/trajectories_labeled.csv
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "trajectories_labeled.csv"

    # Verify input exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Please ensure T015 (US1) has completed successfully.")
        sys.exit(1)

    print(f"Loading divergence data from {input_path}...")
    df = load_divergence_data(input_path)

    if df is None or df.empty:
        print("ERROR: Loaded data is empty or invalid.")
        sys.exit(1)

    # Ensure required columns exist before applying labels
    required_cols = ["G_t", "dG_t", "z_score", "is_contaminated"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns for labeling: {missing_cols}")
        print("Ensure T021 and T022 have run successfully to populate z_score and is_contaminated.")
        sys.exit(1)

    print(f"Applying hacking labels (Threshold tau=3.0, Bonferroni correction)...")
    df_labeled = apply_hacking_labels(df)

    # Verify the label column was added and is boolean
    if "hacked_label" not in df_labeled.columns:
        print("ERROR: Failed to generate 'hacked_label' column.")
        sys.exit(1)

    if df_labeled["hacked_label"].dtype != bool:
        print(f"WARNING: 'hacked_label' column is not boolean type. Converting...")
        df_labeled["hacked_label"] = df_labeled["hacked_label"].astype(bool)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving labeled trajectories to {output_path}...")
    df_labeled.to_csv(output_path, index=False)

    # Summary stats
    total_rows = len(df_labeled)
    hacked_count = df_labeled["hacked_label"].sum()
    hacked_pct = (hacked_count / total_rows * 100) if total_rows > 0 else 0.0

    print(f"Done. Total rows: {total_rows}, Hacked: {hacked_count} ({hacked_pct:.2f}%)")
    print(f"Output saved to: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
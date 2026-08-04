"""
Task T023: Generate labeled trajectories.

This module loads the divergence data computed in US1, applies the hacking labels
determined by the detector (US2), and writes the final labeled dataset to disk.

Dependency: Requires T022 (detector logic) to have populated the 'hacked_label' column
in the input data or for this script to re-apply the logic if the column is missing
(though per spec, T022 should have prepared the data).

Output: data/processed/trajectories_labeled.csv
"""
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# Import from sibling modules as per API surface
from code.config import get_project_root
from code.detector import apply_hacking_labels
from code.utils.io_utils import write_csv, ensure_dir


def load_divergence_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the aggregated divergence data from US1.

    Args:
        input_path: Optional path override. Defaults to data/processed/trajectories_divergence.csv.

    Returns:
        DataFrame containing trajectory data with G(t), dG(t), and z-scores.

    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if input_path is None:
        root = get_project_root()
        input_path = root / "data" / "processed" / "trajectories_divergence.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input divergence data not found at {input_path}. "
            "Ensure T016 (aggregation) has completed successfully."
        )

    df = pd.read_csv(input_path)
    return df


def apply_hacking_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure the 'hacked_label' column is present and boolean.

    If the column already exists (e.g., from T022 intermediate run), it validates
    the type. If not, it delegates to the detector module to apply the logic
    defined in T022 (z-score > 3.0 or dynamic threshold).

    Args:
        df: The divergence dataframe.

    Returns:
        DataFrame with 'hacked_label' column added.
    """
    if "hacked_label" not in df.columns:
        # If T022 hasn't written the label yet, we apply the logic here.
        # The detector.apply_hacking_labels function is designed to take
        # the raw divergence data and return the labeled dataframe.
        df = apply_hacking_labels(df)
    else:
        # Ensure it is boolean
        df["hacked_label"] = df["hacked_label"].astype(bool)

    return df


def main():
    """
    Main entry point for T023.

    1. Load data from data/processed/trajectories_divergence.csv
    2. Ensure 'hacked_label' is present and boolean (calling detector logic if needed)
    3. Save to data/processed/trajectories_labeled.csv
    """
    root = get_project_root()
    input_path = root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = root / "data" / "processed" / "trajectories_labeled.csv"

    ensure_dir(output_path.parent)

    print(f"[T023] Loading divergence data from {input_path}...")
    try:
        df = load_divergence_data(input_path)
    except FileNotFoundError as e:
        print(f"[T023] ERROR: {e}")
        sys.exit(1)

    print(f"[T023] Processing {len(df)} rows to apply hacking labels...")

    # The detector module's apply_hacking_labels is the source of truth for the label logic
    # We call it to ensure consistency with T022.
    # Note: The function signature in detector.py might expect the raw df and return labeled df.
    # We assume apply_hacking_labels from detector.py performs the z-score check and returns the df.
    # If the column already exists, we just ensure type safety.
    
    if "hacked_label" not in df.columns:
        # Re-apply logic if missing (fallback for robustness)
        # This assumes detector.apply_hacking_labels takes the df and returns it with the column
        df = apply_hacking_labels(df)
    else:
        df["hacked_label"] = df["hacked_label"].astype(bool)

    print(f"[T023] Writing labeled data to {output_path}...")
    write_csv(df, output_path)

    # Verify output
    if output_path.exists():
        print(f"[T023] SUCCESS: Generated {output_path} with {len(df)} rows.")
        print(f"[T023] Columns: {list(df.columns)}")
        print(f"[T023] Label distribution:\n{df['hacked_label'].value_counts()}")
    else:
        print(f"[T023] ERROR: Failed to write output file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
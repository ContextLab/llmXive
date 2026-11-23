from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional
import sys
from pathlib import Path

def create_reproducible_subset(
    input_path: str | Path,
    output_path: str | Path,
    subset_size: int = 5000,
    seed: int = 42,
) -> None:
    """
    Create a deterministic subset of molecules from the QM9 dataset.

    This function loads the full QM9 dataset (or a pre-processed version),
    applies a deterministic shuffle using the provided seed, selects the
    first `subset_size` molecules, and saves the result as a Parquet file.

    Args:
        input_path: Path to the input dataset (CSV or Parquet).
        output_path: Path where the subset will be saved (Parquet).
        subset_size: Number of molecules to include in the subset.
        seed: Random seed for reproducibility.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    if input_path.suffix == ".parquet":
        df = pd.read_parquet(input_path)
    elif input_path.suffix == ".csv":
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported input format: {input_path.suffix}")

    # Ensure reproducibility
    np.random.seed(seed)

    # Shuffle deterministically
    df_shuffled = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Select subset
    if len(df_shuffled) < subset_size:
        raise ValueError(
            f"Dataset has {len(df_shuffled)} molecules, but requested subset size is {subset_size}"
        )
    df_subset = df_shuffled.head(subset_size)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save subset
    df_subset.to_parquet(output_path, index=False)
    print(f"Created subset of {subset_size} molecules at {output_path}")

def main() -> None:
    """Main entry point for the subset creation script."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_file = project_root / "data" / "raw" / "qm9_full.parquet"
    output_file = project_root / "data" / "processed" / "subset_final.parquet"

    # Check if input exists; if not, look for CSV fallback
    if not input_file.exists():
        csv_input = project_root / "data" / "raw" / "qm9_full.csv"
        if csv_input.exists():
            input_file = csv_input
        else:
            raise FileNotFoundError(
                f"No input dataset found. Expected {project_root / 'data' / 'raw'} / qm9_full.[parquet|csv]"
            )

    create_reproducible_subset(
        input_path=input_file,
        output_path=output_file,
        subset_size=5000,
        seed=42,
    )

if __name__ == "__main__":
    main()
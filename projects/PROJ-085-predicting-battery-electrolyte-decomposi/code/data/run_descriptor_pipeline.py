"""
Wrapper script that executes the descriptor extraction pipeline.

It reads the raw ingestion CSV (``data/raw/electrolytes_raw.csv``),
extracts electronic and geometric descriptors, and writes the enriched
feature matrix to ``data/processed/electrolyte_features.csv``.
"""

import sys
from pathlib import Path

import pandas as pd

# Ensure project root is on the import path for relative imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.constants import load_reactions
from data.descriptors import run_descriptor_pipeline
from config import get_data_dir, get_processed_dir

def main() -> None:
    raw_dir = Path(get_data_dir()) / "raw"
    processed_dir = Path(get_processed_dir())

    raw_path = raw_dir / "electrolytes_raw.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw ingestion file not found at {raw_path}")

    # Load raw data
    df_raw = pd.read_csv(raw_path)

    # Run the descriptor pipeline (the function handles SMILES parsing,
    # 3‑D conformer generation, and descriptor extraction)
    df_features = run_descriptor_pipeline(df_raw)

    # Persist the processed feature matrix
    output_path = processed_dir / "electrolyte_features.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(output_path, index=False)
    print(f"Descriptor extraction completed. Output written to {output_path}")


if __name__ == "__main__":
    main()

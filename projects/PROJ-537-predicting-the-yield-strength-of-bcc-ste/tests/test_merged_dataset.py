"""
Unit test to ensure that the merged dataset produced by the ingestion pipeline
contains at least 20 rows with non‑null ``yield_strength_MPa`` and ``shear_modulus_GPa``.
"""

import pandas as pd
from pathlib import Path
from config import CONFIG

def test_merged_dataset_row_count():
    merged_path = Path(CONFIG.MERGED_DATA_PATH)
    assert merged_path.is_file(), f"Merged dataset not found at {merged_path}"

    df = pd.read_csv(merged_path)
    # Ensure required columns exist
    assert "yield_strength_MPa" in df.columns
    assert "shear_modulus_GPa" in df.columns

    # Count rows where both columns are non‑null
    valid_rows = df[df["yield_strength_MPa"].notna() & df["shear_modulus_GPa"].notna()]
    assert len(valid_rows) >= 20, f"Expected at least 20 valid rows, found {len(valid_rows)}"

# The test will be executed automatically by the CI runner when this task is
# evaluated. No additional code is required.
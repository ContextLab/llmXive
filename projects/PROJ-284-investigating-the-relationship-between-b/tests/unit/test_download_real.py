import os
import pandas as pd
from pathlib import Path

def test_adhd_phenotype_file_exists():
    """
    Verify that the download step creates a real phenotypic CSV file.
    This test runs after ``code/main.py --step download_preprocess``.
    """
    phenofile = Path(__file__).resolve().parents[2] / "data" / "raw" / "adhd_phenotypic.csv"
    assert phenofile.is_file(), f"Expected phenotypic file at {phenofile}"
    df = pd.read_csv(phenofile)
    # The ADHD dataset has at least 30 records; we check for a sensible count.
    assert len(df) >= 30, "Phenotypic file should contain at least 30 rows"
    # Verify that a known column exists (e.g., 'Subject')
    assert "Subject" in df.columns, "Column 'Subject' missing from phenotypic data"
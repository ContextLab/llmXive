import pytest
import os
from pathlib import Path
from code.ingestion import run_dgp_pipeline

def test_full_pipeline():
    # This test checks that the pipeline runs and creates files
    # Note: In a real CI, this might be skipped due to time
    run_dgp_pipeline()
    assert Path("data/raw/delay_discounting.csv").exists()
    assert Path("data/processed/harmonized_dataset.parquet").exists()
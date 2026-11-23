"""
Integration test for T017: Output Cleaned Data.

Verifies that:
1. The cleaned_data.csv file is created.
2. It contains the required columns.
3. Numeric columns are standardized (0-1 range).
4. Metadata file is created with correct scoring method.
"""
import os
import json
import pandas as pd
import pytest
from pathlib import Path
import sys
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing.output_cleaned_data import run_cleaning_pipeline, STANDARDIZE_COLUMNS, REQUIRED_COLUMNS
from preprocessing.preprocess import run_preprocessing

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

@pytest.fixture(scope="module")
def setup_pipeline():
    """Sets up the environment by running T013 and T014 first."""
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if intermediate data exists (from T014)
    # If not, we might need to mock the source for this test if T013/T014 aren't run in CI
    # However, per instructions, we assume the pipeline runs.
    # For this test to be robust, we will generate a minimal synthetic source if missing
    # to simulate the T013 -> T014 -> T017 flow.
    
    source_path = RAW_DIR / "synthetic_interactions.csv"
    intermediate_path = PROCESSED_DIR / "intermediate_features.csv"
    
    if not source_path.exists():
        # Create minimal synthetic data for testing T017
        data = {
            "participant_id": [f"P{i}" for i in range(10)],
            "latency": [0.1, 0.2, 0.15, 0.3, 0.25, 0.12, 0.18, 0.22, 0.28, 0.35],
            "smoothness": [0.9, 0.8, 0.85, 0.7, 0.75, 0.88, 0.82, 0.78, 0.72, 0.65],
            "lead_time": [0.05, 0.08, 0.06, 0.1, 0.09, 0.07, 0.06, 0.09, 0.11, 0.12],
            "agency_score": [0.8, 0.7, 0.75, 0.6, 0.65, 0.78, 0.72, 0.68, 0.62, 0.55]
        }
        pd.DataFrame(data).to_csv(source_path, index=False)
    
    if not intermediate_path.exists():
        # Run T014
        run_preprocessing(input_path=source_path, output_path=intermediate_path)
        
    yield
    
    # Cleanup
    if intermediate_path.exists():
        intermediate_path.unlink()
    cleaned_path = PROCESSED_DIR / "cleaned_data.csv"
    if cleaned_path.exists():
        cleaned_path.unlink()
    metadata_path = PROCESSED_DIR / "cleaning_metadata.json"
    if metadata_path.exists():
        metadata_path.unlink()

def test_t017_creates_file(setup_pipeline):
    """T017 must create data/processed/cleaned_data.csv"""
    output_path = PROCESSED_DIR / "cleaned_data.csv"
    run_cleaning_pipeline()
    assert output_path.exists(), "cleaned_data.csv was not created"

def test_t017_required_columns(setup_pipeline):
    """T017 output must contain required columns."""
    output_path = PROCESSED_DIR / "cleaned_data.csv"
    run_cleaning_pipeline()
    df = pd.read_csv(output_path)
    
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"

def test_t017_standardization(setup_pipeline):
    """T017 must standardize numeric columns to 0-1 range."""
    output_path = PROCESSED_DIR / "cleaned_data.csv"
    run_cleaning_pipeline()
    df = pd.read_csv(output_path)
    
    for col in STANDARDIZE_COLUMNS:
        if col in df.columns:
            min_val = df[col].min()
            max_val = df[col].max()
            assert min_val >= 0.0 and max_val <= 1.0, f"Column {col} not in [0, 1] range: [{min_val}, {max_val}]"
            # Check if it's actually scaled (unless all values were identical)
            if max_val > min_val:
                assert min_val == 0.0 and max_val == 1.0, f"Column {col} not properly min-max scaled: [{min_val}, {max_val}]"

def test_t017_metadata(setup_pipeline):
    """T017 must create metadata file with scoring method."""
    output_path = PROCESSED_DIR / "cleaned_data.csv"
    metadata_path = PROCESSED_DIR / "cleaning_metadata.json"
    
    run_cleaning_pipeline()
    
    assert metadata_path.exists(), "cleaning_metadata.json was not created"
    
    with open(metadata_path, 'r') as f:
        meta = json.load(f)
    
    assert "scoring_method" in meta, "Metadata missing 'scoring_method'"
    assert "standardization_details" in meta, "Metadata missing 'standardization_details'"
    assert meta["scoring_method"] == "Min-Max Normalization to [0, 1] range"
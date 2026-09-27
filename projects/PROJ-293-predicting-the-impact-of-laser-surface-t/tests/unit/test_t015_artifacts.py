"""
Unit tests for Task T015: Verify artifact generation and hash updates.
"""
import os
import sys
import json
import yaml
import pandas as pd
from pathlib import Path
import pytest

# Add parent to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from hygiene import calculate_md5, load_artifact_hashes

BASE_DIR = Path(__file__).parent.parent.parent
DATA_PROCESSED = BASE_DIR / "data" / "processed"
STATE_DIR = BASE_DIR / "state"
OUTPUT_CSV = DATA_PROCESSED / "aggregated_clean.csv"
HASHES_YAML = STATE_DIR / "artifact_hashes.yaml"

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """Ensure directories exist before tests."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup if necessary (optional)

def test_t015_csv_exists():
    """Verify that data/processed/aggregated_clean.csv exists."""
    assert OUTPUT_CSV.exists(), "T015 Output file data/processed/aggregated_clean.csv does not exist."

def test_t015_csv_schema():
    """Verify the CSV has the required columns."""
    if not OUTPUT_CSV.exists():
        pytest.skip("Output file not generated yet.")
    
    df = pd.read_csv(OUTPUT_CSV)
    required_cols = ['normalization_method']
    # Check for at least the normalization_method column as per T013d/T015
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify normalization_method has expected values
    assert set(df['normalization_method'].unique()).issubset({'raw', 'normalized', 'raw', 'normalized'})

def test_t015_hashes_updated():
    """Verify that state/artifact_hashes.yaml contains the checksum for the CSV."""
    if not HASHES_YAML.exists():
        pytest.skip("Hashes file not generated yet.")
    
    hashes = load_artifact_hashes(HASHES_YAML)
    csv_key = "data/processed/aggregated_clean.csv"
    
    assert csv_key in hashes, f"Hash entry for {csv_key} not found in state/artifact_hashes.yaml."
    
    entry = hashes[csv_key]
    assert 'md5' in entry, "MD5 checksum missing in hash entry."
    
    # Verify the checksum matches the actual file
    actual_md5 = calculate_md5(OUTPUT_CSV)
    assert entry['md5'] == actual_md5, f"MD5 mismatch: stored={entry['md5']}, actual={actual_md5}"
"""
Tests for the synthetic data generator.
"""
import os
import json
import hashlib
import pytest
from pathlib import Path
import pandas as pd

# Add code to path if necessary, assuming standard project structure
# sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.synthetic_data import generate_synthetic_dataset, SEED

DATA_DIR = Path("data/raw")
EXPECTED_FILE = DATA_DIR / "synthetic_arabidopsis_v1.csv"
EXPECTED_MANIFEST = DATA_DIR / "synthetic_arabidopsis_v1.manifest.json"

@pytest.fixture(scope="module")
def generated_dataset():
    """Generate the dataset once for all tests in this module."""
    if not EXPECTED_FILE.exists():
        generate_synthetic_dataset(num_replicates=10)
    return EXPECTED_FILE

def test_file_exists(generated_dataset):
    """Test that the synthetic CSV file is created."""
    assert generated_dataset.exists(), f"Expected file {generated_dataset} not found."

def test_manifest_exists(generated_dataset):
    """Test that the manifest file is created."""
    assert EXPECTED_MANIFEST.exists(), f"Expected manifest {EXPECTED_MANIFEST} not found."

def test_csv_has_correct_columns(generated_dataset):
    """Test that the CSV contains expected columns."""
    df = pd.read_csv(generated_dataset)
    required_columns = [
        "sample_id", "condition", "temperature", "light_intensity", 
        "humidity", "monoterpenes_total", "sesquiterpenes_total", 
        "glv_total", "benzoids_total", "total_voc_flux"
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

def test_csv_has_minimum_rows(generated_dataset):
    """Test that the CSV has at least 50 rows as per requirements."""
    df = pd.read_csv(generated_dataset)
    assert len(df) >= 50, f"Expected at least 50 rows, got {len(df)}"

def test_conditions_present(generated_dataset):
    """Test that all expected conditions are present."""
    df = pd.read_csv(generated_dataset)
    expected_conditions = ["control", "drought", "heat", "cold", "pathogen_attack", "herbivory"]
    for cond in expected_conditions:
        assert cond in df["condition"].values, f"Missing condition: {cond}"

def test_manifest_hash_matches_file(generated_dataset):
    """Test that the manifest hash matches the actual file hash."""
    with open(EXPECTED_MANIFEST, 'r') as f:
        manifest = json.load(f)
    
    file_hash = hashlib.sha256(generated_dataset.read_bytes()).hexdigest()
    manifest_hash = manifest["hash"]
    
    assert file_hash == manifest_hash, f"Hash mismatch: {file_hash} != {manifest_hash}"

def test_data_types_correct(generated_dataset):
    """Test that numeric columns are numeric."""
    df = pd.read_csv(generated_dataset)
    numeric_cols = ["temperature", "light_intensity", "humidity", "monoterpenes_total"]
    for col in numeric_cols:
        assert pd.api.types.is_numeric_dtype(df[col]), f"Column {col} is not numeric"

def test_no_missing_critical_env_data(generated_dataset):
    """Test that critical environmental fields are not missing."""
    df = pd.read_csv(generated_dataset)
    assert not df["temperature"].isnull().any(), "Missing temperature values"
    assert not df["light_intensity"].isnull().any(), "Missing light_intensity values"
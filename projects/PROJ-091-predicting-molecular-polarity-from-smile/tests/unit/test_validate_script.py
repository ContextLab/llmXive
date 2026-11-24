import subprocess
import sys
import json
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def validation_env():
    """Create a temporary environment with a parquet file and a JSON descriptor list."""
    tmp_dir = Path(tempfile.mkdtemp())
    processed_dir = tmp_dir / "processed"
    processed_dir.mkdir(parents=True)

    # 1. Create descriptor_names.json
    desc_names = ["MolWt", "LogP", "NumHDonors", "NumHAcceptors"]
    json_path = processed_dir / "descriptor_names.json"
    with open(json_path, "w") as f:
        json.dump(desc_names, f)

    # 2. Create valid descriptors.parquet
    data = {
        "smiles": ["CCO", "CNC"],
        "target": [1.2, 0.8],
        "stereochemistry_flag": [False, False],
        "flexible_flag": [False, False],
        "desc_MolWt": [46.07, 59.11],
        "desc_LogP": [0.48, 0.12],
        "desc_NumHDonors": [1, 1],
        "desc_NumHAcceptors": [1, 1],
    }
    df = pd.DataFrame(data)
    parquet_path = processed_dir / "descriptors.parquet"
    df.to_parquet(parquet_path)

    yield tmp_dir, parquet_path, json_path
    shutil.rmtree(tmp_dir)

def run_validator(parquet_path: Path):
    """Helper to run the validate.py script via subprocess."""
    script_path = Path("code/data/validate.py")
    result = subprocess.run(
        [sys.executable, str(script_path), str(parquet_path)],
        capture_output=True,
        text=True
    )
    return result

def test_validate_success(validation_env):
    """Verify that a correct file and JSON return exit code 0."""
    tmp_dir, parquet_path, _ = validation_env
    result = run_validator(parquet_path)
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. Error: {result.stderr}"

def test_validate_missing_json(validation_env):
    """Verify that missing descriptor_names.json returns exit code 1."""
    tmp_dir, parquet_path, json_path = validation_env
    json_path.unlink() # Remove the JSON
    result = run_validator(parquet_path)
    assert result.returncode != 0, "Expected non-zero exit when JSON is missing"

def test_validate_column_mismatch(validation_env):
    """Verify that a mismatch in descriptor columns returns exit code 1."""
    tmp_dir, parquet_path, json_path = validation_env
    
    # Corrupt the parquet by removing a descriptor column
    df = pd.read_parquet(parquet_path)
    df = df.drop(columns=["desc_MolWt"])
    df.to_parquet(parquet_path)

    result = run_validator(parquet_path)
    assert result.returncode != 0, "Expected non-zero exit when columns mismatch"
    assert "Descriptor columns mismatch" in result.stderr or "Descriptor columns mismatch" in result.stdout

def test_validate_forbidden_tpsa(validation_env):
    """Verify that TPSA columns trigger a validation failure."""
    tmp_dir, parquet_path, json_path = validation_env
    
    df = pd.read_parquet(parquet_path)
    df["desc_TPSA"] = [20.0, 15.0] # Add forbidden column
    df.to_parquet(parquet_path)

    result = run_validator(parquet_path)
    assert result.returncode != 0, "Expected non-zero exit when TPSA is present"
    assert "Forbidden TPSA-related columns present" in result.stderr or "Forbidden TPSA-related columns present" in result.stdout

def test_validate_invalid_target(validation_env):
    """Verify that non-numeric target triggers failure."""
    tmp_dir, parquet_path, json_path = validation_env
    
    df = pd.read_parquet(parquet_path)
    df["target"] = ["high", "low"] # Non-numeric
    df.to_parquet(parquet_path)

    result = run_validator(parquet_path)
    assert result.returncode != 0, "Expected non-zero exit for non-numeric target"
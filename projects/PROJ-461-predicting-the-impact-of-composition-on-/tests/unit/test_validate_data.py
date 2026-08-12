import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import numpy as np

# Import the module to test
from code.analysis.validate_data import run_validation, validate_missing_values, validate_numeric_types

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def valid_csv(temp_dir):
    data = {
        "composition": ["Fe50Ni50", "Fe60Ni40"],
        "density": [7.8, 7.9],
        "mass_fraction_Fe": [0.5, 0.6],
        "mass_fraction_Ni": [0.5, 0.4]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "test_data.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def missing_target_csv(temp_dir):
    data = {
        "composition": ["Fe50Ni50", "Fe60Ni40"],
        "density": [7.8, np.nan],
        "mass_fraction_Fe": [0.5, 0.6],
        "mass_fraction_Ni": [0.5, 0.4]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "test_missing.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def non_numeric_mass_csv(temp_dir):
    data = {
        "composition": ["Fe50Ni50", "Fe60Ni40"],
        "density": [7.8, 7.9],
        "mass_fraction_Fe": [0.5, "invalid"],
        "mass_fraction_Ni": [0.5, 0.4]
    }
    df = pd.DataFrame(data)
    path = temp_dir / "test_non_numeric.csv"
    df.to_csv(path, index=False)
    return path

def test_validate_missing_values_pass():
    df = pd.DataFrame({"density": [1.0, 2.0, 3.0]})
    result = validate_missing_values(df, "density")
    assert result["status"] == "passed"
    assert result["missing_count"] == 0

def test_validate_missing_values_fail():
    df = pd.DataFrame({"density": [1.0, np.nan, 3.0]})
    result = validate_missing_values(df, "density")
    assert result["status"] == "failed"
    assert result["missing_count"] == 1

def test_validate_numeric_types_pass():
    df = pd.DataFrame({
        "mass_fraction_Fe": [0.5, 0.6],
        "mass_fraction_Ni": [0.5, 0.4]
    })
    result = validate_numeric_types(df, ["mass_fraction_Fe", "mass_fraction_Ni"])
    assert result["all_valid"] is True
    assert len(result["issues"]) == 0

def test_validate_numeric_types_fail_non_numeric():
    df = pd.DataFrame({
        "mass_fraction_Fe": [0.5, "bad"],
        "mass_fraction_Ni": [0.5, 0.4]
    })
    result = validate_numeric_types(df, ["mass_fraction_Fe", "mass_fraction_Ni"])
    assert result["all_valid"] is False
    assert any("non-numeric" in issue for issue in result["issues"])

def test_run_validation_success(valid_csv, temp_dir):
    output_path = temp_dir / "log.json"
    result = run_validation(valid_csv, output_path=output_path)

    assert result["overall_status"] == "passed"
    assert result["row_count"] == 2
    assert result["source_file"] == "test_data.csv"
    
    # Verify file written
    assert output_path.exists()
    with open(output_path) as f:
        log_data = json.load(f)
    assert log_data["overall_status"] == "passed"

def test_run_validation_missing_target(missing_target_csv, temp_dir):
    output_path = temp_dir / "log.json"
    result = run_validation(missing_target_csv, output_path=output_path)

    assert result["overall_status"] == "failed"
    assert result["target_validation"]["status"] == "failed"

def test_run_validation_non_numeric_mass(non_numeric_mass_csv, temp_dir):
    output_path = temp_dir / "log.json"
    result = run_validation(non_numeric_mass_csv, output_path=output_path)

    assert result["overall_status"] == "failed"
    assert result["type_validation"]["all_valid"] is False

def test_run_validation_file_not_found(temp_dir):
    fake_path = temp_dir / "nonexistent.csv"
    output_path = temp_dir / "log.json"
    
    result = run_validation(fake_path, output_path=output_path)
    
    assert result["status"] == "failed"
    assert "not found" in result["error"].lower()

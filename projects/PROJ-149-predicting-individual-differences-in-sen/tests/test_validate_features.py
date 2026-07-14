"""
Unit tests for code/06_validate_features.py
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# We will mock the config import or patch it if necessary, 
# but for unit testing the logic, we can pass explicit paths.
# The validate_schema function is the target.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from code import code  # Import the module directly if possible, or reload
# Since the script is code/06_validate_features.py, we import the function
# by adding the code directory to path and importing the module.

# Re-import strategy for testing
import importlib.util
spec = importlib.util.spec_from_file_location("validate_features", "code/06_validate_features.py")
validate_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_mod)

validate_schema = validate_mod.validate_schema

def create_temp_csv(data, filename="test_features.csv"):
    """Helper to create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    os.close(fd)
    return path

def test_missing_file():
    """Test that validation fails if file does not exist."""
    result = validate_schema("/nonexistent/path/file.csv")
    assert result is False

def test_missing_columns():
    """Test that validation fails if required columns are missing."""
    data = {"participant_id": [1], "other_col": [2]}
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is False
    finally:
        os.remove(path)

def test_null_values():
    """Test that validation fails if critical columns have nulls."""
    data = {
        "participant_id": [1, None],
        "median_rt_ms": [250.0, 300.0],
        "delta_rel_power": [0.1, 0.2],
        "theta_rel_power": [0.1, 0.2],
        "alpha_rel_power": [0.1, 0.2],
        "beta_low_rel_power": [0.1, 0.2],
        "beta_high_rel_power": [0.1, 0.2],
        "gamma_rel_power": [0.1, 0.2]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is False
    finally:
        os.remove(path)

def test_rt_out_of_range_low():
    """Test validation fails for RT < 100ms."""
    data = {
        "participant_id": [1],
        "median_rt_ms": [50.0], # Too low
        "delta_rel_power": [0.1],
        "theta_rel_power": [0.1],
        "alpha_rel_power": [0.1],
        "beta_low_rel_power": [0.1],
        "beta_high_rel_power": [0.1],
        "gamma_rel_power": [0.1]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is False
    finally:
        os.remove(path)

def test_rt_out_of_range_high():
    """Test validation fails for RT > 2000ms."""
    data = {
        "participant_id": [1],
        "median_rt_ms": [2500.0], # Too high
        "delta_rel_power": [0.1],
        "theta_rel_power": [0.1],
        "alpha_rel_power": [0.1],
        "beta_low_rel_power": [0.1],
        "beta_high_rel_power": [0.1],
        "gamma_rel_power": [0.1]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is False
    finally:
        os.remove(path)

def test_negative_power():
    """Test validation fails for negative power values."""
    data = {
        "participant_id": [1],
        "median_rt_ms": [250.0],
        "delta_rel_power": [-0.1], # Negative
        "theta_rel_power": [0.1],
        "alpha_rel_power": [0.1],
        "beta_low_rel_power": [0.1],
        "beta_high_rel_power": [0.1],
        "gamma_rel_power": [0.1]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is False
    finally:
        os.remove(path)

def test_valid_data():
    """Test validation passes with correct data."""
    data = {
        "participant_id": [1, 2, 3],
        "median_rt_ms": [250.0, 300.0, 150.0],
        "delta_rel_power": [0.1, 0.2, 0.15],
        "theta_rel_power": [0.1, 0.2, 0.15],
        "alpha_rel_power": [0.1, 0.2, 0.15],
        "beta_low_rel_power": [0.1, 0.2, 0.15],
        "beta_high_rel_power": [0.1, 0.2, 0.15],
        "gamma_rel_power": [0.1, 0.2, 0.15]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is True
    finally:
        os.remove(path)

def test_boundary_rt_values():
    """Test validation passes exactly at boundaries (100 and 2000)."""
    data = {
        "participant_id": [1, 2],
        "median_rt_ms": [100.0, 2000.0],
        "delta_rel_power": [0.1, 0.2],
        "theta_rel_power": [0.1, 0.2],
        "alpha_rel_power": [0.1, 0.2],
        "beta_low_rel_power": [0.1, 0.2],
        "beta_high_rel_power": [0.1, 0.2],
        "gamma_rel_power": [0.1, 0.2]
    }
    path = create_temp_csv(data)
    try:
        result = validate_schema(path)
        assert result is True
    finally:
        os.remove(path)

import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from power_analysis import (
    calculate_cohen_d,
    interpret_effect_size,
    check_dataset_power,
    run_power_analysis_from_csv,
    LARGE_THRESHOLD,
    SMALL_THRESHOLD
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def small_dataset_csv(temp_dir):
    """Create a small dataset CSV (n < 50)."""
    csv_path = Path(temp_dir) / "small_dataset.csv"
    data = {
        "smiles": ["C" * 10 for _ in range(30)],
        "degradation_label": ["hydrolysis"] * 15 + ["oxidation"] * 15,
        "temperature": [25.0] * 30,
        "ph": [7.0] * 30
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def medium_dataset_csv(temp_dir):
    """Create a medium dataset CSV (50 <= n <= 150)."""
    csv_path = Path(temp_dir) / "medium_dataset.csv"
    n = 100
    data = {
        "smiles": ["C" * 10 for _ in range(n)],
        "degradation_label": ["hydrolysis"] * (n // 2) + ["oxidation"] * (n - n // 2),
        "temperature": [25.0] * n,
        "ph": [7.0] * n
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def large_dataset_csv(temp_dir):
    """Create a large dataset CSV (n > 150)."""
    csv_path = Path(temp_dir) / "large_dataset.csv"
    n = 200
    data = {
        "smiles": ["C" * 10 for _ in range(n)],
        "degradation_label": ["hydrolysis"] * (n // 2) + ["oxidation"] * (n - n // 2),
        "temperature": [25.0] * n,
        "ph": [7.0] * n
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_cohen_d_calculation():
    """Test Cohen's d calculation."""
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
    
    d = calculate_cohen_d(group1, group2)
    assert isinstance(d, float)
    # Expected d should be around -1.0 (mean diff = -1, std ~ 1.41)
    assert -2.0 < d < 0.0

def test_interpret_effect_size():
    """Test effect size interpretation."""
    assert interpret_effect_size(0.1) == "negligible"
    assert interpret_effect_size(0.3) == "small"
    assert interpret_effect_size(0.6) == "medium"
    assert interpret_effect_size(1.0) == "large"
    assert interpret_effect_size(-0.5) == "small"

def test_check_dataset_power():
    """Test dataset power check."""
    is_sufficient, required = check_dataset_power(200)
    assert is_sufficient is True
    assert required == 128
    
    is_sufficient, required = check_dataset_power(100)
    assert is_sufficient is False
    assert required == 128

def test_power_analysis_small_dataset(small_dataset_csv, temp_dir):
    """Test power analysis with small dataset (n < 50)."""
    # Set up paths for trigger and report
    state_dir = Path(temp_dir) / "state"
    state_dir.mkdir()
    reports_dir = Path(temp_dir) / "data/reports"
    reports_dir.mkdir(parents=True)
    
    # Temporarily override paths by mocking or using environment
    # For this test, we'll just check the logic directly
    
    result = run_power_analysis_from_csv(small_dataset_csv)
    
    assert result["n"] == 30
    assert result["action"] == "subsampling"
    assert result["power_warning"] is True
    assert "reason" in result["details"]
    assert "critical" in result["details"]["reason"].lower()

def test_power_analysis_medium_dataset(medium_dataset_csv, temp_dir):
    """Test power analysis with medium dataset (50 <= n <= 150)."""
    result = run_power_analysis_from_csv(medium_dataset_csv)
    
    assert result["n"] == 100
    assert result["action"] == "augment"
    assert result["power_warning"] is False
    assert "reason" in result["details"]
    assert "acceptable range" in result["details"]["reason"].lower()

def test_power_analysis_large_dataset(large_dataset_csv, temp_dir):
    """Test power analysis with large dataset (n > 150)."""
    result = run_power_analysis_from_csv(large_dataset_csv)
    
    assert result["n"] == 200
    assert result["action"] == "subsampling"
    assert result["power_warning"] is False
    assert "reason" in result["details"]
    assert "exceeds threshold" in result["details"]["reason"].lower()

def test_power_analysis_missing_file():
    """Test power analysis with missing input file."""
    with pytest.raises(FileNotFoundError):
        run_power_analysis_from_csv("/nonexistent/path.csv")

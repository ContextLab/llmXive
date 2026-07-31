import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from power_analysis import (
    calculate_cohen_d,
    interpret_effect_size,
    check_dataset_power,
    run_power_analysis_from_csv,
    THRESHOLD_HIGH,
    THRESHOLD_LOW
)
from utils import get_project_paths

@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file with test data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a small test dataset
        data = {
            'smiles': ['CCO', 'CC(=O)O', 'CCCC', 'C1CCCCC1', 'CCO'],
            'degradation_pathway': ['hydrolysis', 'oxidation', 'hydrolysis', 'thermal', 'hydrolysis'],
            'temperature': [25, 30, 25, 40, 25],
            'ph': [7.0, 6.5, 7.0, 5.0, 7.0],
            'uv_exposure': [0, 1, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_project_paths():
    """Create temporary directories for project structure."""
    temp_dir = tempfile.mkdtemp()
    paths = {
        "root": temp_dir,
        "code": os.path.join(temp_dir, "code"),
        "data": os.path.join(temp_dir, "data"),
        "raw": os.path.join(temp_dir, "data", "raw"),
        "processed": os.path.join(temp_dir, "data", "processed"),
        "reports": os.path.join(temp_dir, "data", "reports"),
        "state": os.path.join(temp_dir, "state"),
        "tests": os.path.join(temp_dir, "tests")
    }
    
    # Create directories
    for path in paths.values():
        os.makedirs(path, exist_ok=True)
    
    yield paths
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_cohen_d_calculation():
    """Test Cohen's d calculation with known values."""
    group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
    
    d = calculate_cohen_d(group1, group2)
    
    # Mean1 = 3, Mean2 = 4, Pooled std ≈ 1.58
    # d = (3-4)/1.58 ≈ -0.63
    assert abs(d - (-0.632)) < 0.01

def test_cohen_d_empty_groups():
    """Test Cohen's d with empty groups."""
    assert calculate_cohen_d([], []) == 0.0
    assert calculate_cohen_d([1, 2], []) == 0.0
    assert calculate_cohen_d([], [1, 2]) == 0.0

def test_effect_size_interpretation():
    """Test effect size interpretation."""
    assert interpret_effect_size(0.1) == "negligible"
    assert interpret_effect_size(0.3) == "small"
    assert interpret_effect_size(0.6) == "medium"
    assert interpret_effect_size(1.0) == "large"
    assert interpret_effect_size(-0.5) == "small"
    assert interpret_effect_size(-0.9) == "large"

def test_check_dataset_power():
    """Test power calculation function."""
    # Large sample should have high power
    result = check_dataset_power(200, effect_size=0.5)
    assert result["n"] == 200
    assert result["power"] > 0.8
    assert result["status"] == "sufficient"
    
    # Small sample should have low power
    result = check_dataset_power(20, effect_size=0.5)
    assert result["n"] == 20
    assert result["power"] < 0.5
    assert result["status"] == "insufficient"
    
    # Zero sample
    result = check_dataset_power(0)
    assert result["power"] == 0.0
    assert result["status"] == "insufficient"

def test_run_power_analysis_high_sample(temp_csv_file, temp_project_paths):
    """Test power analysis with high sample count (>150)."""
    # Create a large dataset
    large_data = {
        'smiles': [f'C{i}' for i in range(200)],
        'degradation_pathway': ['hydrolysis' if i % 2 == 0 else 'oxidation' for i in range(200)],
        'temperature': [25 + (i % 10) for i in range(200)],
        'ph': [7.0 + (i % 5) * 0.1 for i in range(200)],
        'uv_exposure': [i % 2 for i in range(200)]
    }
    large_df = pd.DataFrame(large_data)
    large_csv = os.path.join(temp_project_paths["processed"], "processed_graph_dataset.csv")
    large_df.to_csv(large_csv, index=False)
    
    result = run_power_analysis_from_csv(large_csv)
    
    assert result["n"] == 200
    assert result["action"] == "none"
    assert result["power_warning"] == False
    assert result["should_halt"] == False
    
    # Verify files were created
    assert os.path.exists(os.path.join(temp_project_paths["state"], "augmentation_trigger.json"))
    assert os.path.exists(os.path.join(temp_project_paths["reports"], "power_analysis_report.json"))
    
    # Check trigger file content
    with open(os.path.join(temp_project_paths["state"], "augmentation_trigger.json")) as f:
        trigger = json.load(f)
        assert trigger["n"] == 200
        assert trigger["action"] == "none"

def test_run_power_analysis_medium_sample(temp_csv_file, temp_project_paths):
    """Test power analysis with medium sample count (50-150)."""
    # Create a medium dataset
    medium_data = {
        'smiles': [f'C{i}' for i in range(100)],
        'degradation_pathway': ['hydrolysis' if i % 2 == 0 else 'oxidation' for i in range(100)],
        'temperature': [25 + (i % 10) for i in range(100)],
        'ph': [7.0 + (i % 5) * 0.1 for i in range(100)],
        'uv_exposure': [i % 2 for i in range(100)]
    }
    medium_df = pd.DataFrame(medium_data)
    medium_csv = os.path.join(temp_project_paths["processed"], "processed_graph_dataset.csv")
    medium_df.to_csv(medium_csv, index=False)
    
    result = run_power_analysis_from_csv(medium_csv)
    
    assert result["n"] == 100
    assert result["action"] == "augment"
    assert result["power_warning"] == True
    assert result["should_halt"] == False
    
    # Verify warning file was created
    warning_path = os.path.join(temp_project_paths["reports"], "power_analysis_warning.txt")
    assert os.path.exists(warning_path)
    with open(warning_path) as f:
        content = f.read()
        assert "augment" in content.lower()

def test_run_power_analysis_low_sample(temp_csv_file, temp_project_paths):
    """Test power analysis with low sample count (<50)."""
    # Create a small dataset
    small_data = {
        'smiles': [f'C{i}' for i in range(30)],
        'degradation_pathway': ['hydrolysis' if i % 2 == 0 else 'oxidation' for i in range(30)],
        'temperature': [25 + (i % 10) for i in range(30)],
        'ph': [7.0 + (i % 5) * 0.1 for i in range(30)],
        'uv_exposure': [i % 2 for i in range(30)]
    }
    small_df = pd.DataFrame(small_data)
    small_csv = os.path.join(temp_project_paths["processed"], "processed_graph_dataset.csv")
    small_df.to_csv(small_csv, index=False)
    
    result = run_power_analysis_from_csv(small_csv)
    
    assert result["n"] == 30
    assert result["action"] == "augment_aggressive"
    assert result["power_warning"] == True
    assert result["should_halt"] == True
    
    # Verify warning file exists and contains critical message
    warning_path = os.path.join(temp_project_paths["reports"], "power_analysis_warning.txt")
    assert os.path.exists(warning_path)
    with open(warning_path) as f:
        content = f.read()
        assert "CRITICAL" in content
        assert "augment_aggressive" in content.lower()

def test_run_power_analysis_missing_file():
    """Test power analysis with missing input file."""
    with pytest.raises(FileNotFoundError):
        run_power_analysis_from_csv("/nonexistent/path/file.csv")
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

import config
from generate_research_report import generate_research_report, load_json_safe, check_data_gap_status

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure simulating the project root."""
    temp_dir = tempfile.mkdtemp()
    # Setup minimal structure
    data_models = Path(temp_dir) / "data" / "models"
    data_models.mkdir(parents=True)
    return temp_dir

@pytest.fixture
def cleanup_temp_project_root(temp_project_root):
    yield temp_project_root
    shutil.rmtree(temp_project_root, ignore_errors=True)

def test_load_json_safe_exists(cleanup_temp_project_root):
    """Test loading an existing JSON file."""
    test_file = Path(cleanup_temp_project_root) / "test.json"
    data = {"key": "value"}
    with open(test_file, 'w') as f:
        json.dump(data, f)

    result = load_json_safe(test_file)
    assert result == data

def test_load_json_safe_missing_default(cleanup_temp_project_root):
    """Test loading a missing JSON file with default."""
    missing_file = Path(cleanup_temp_project_root) / "missing.json"
    default_data = {"default": "value"}

    result = load_json_safe(missing_file, default=default_data)
    assert result == default_data

def test_load_json_safe_missing_no_default(cleanup_temp_project_root):
    """Test loading a missing JSON file without default raises error."""
    missing_file = Path(cleanup_temp_project_root) / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_json_safe(missing_file)

def test_check_data_gap_status_verified(cleanup_temp_project_root):
    """Test data gap status when no report exists (assumed verified)."""
    # Simulate project root in temp dir
    # Note: In real usage, config.PROJECT_ROOT would be set, but here we mock the file check
    # by passing a specific path logic if we were refactoring, but for now we test the logic
    # assuming the function checks relative to a known path.
    # Since the function uses config.PROJECT_ROOT, we rely on the fixture not having the file.
    # We need to ensure config.PROJECT_ROOT points to our temp dir for this test to be accurate
    # or mock the file existence.
    # For simplicity in this unit test, we assume the function logic is correct if file doesn't exist.
    
    # Temporarily override PROJECT_ROOT for this test
    original_root = config.PROJECT_ROOT
    config.PROJECT_ROOT = cleanup_temp_project_root
    
    try:
        status = check_data_gap_status()
        assert status["verified"] is True
        assert status["halt_flag"] is False
        assert status["report_exists"] is False
    finally:
        config.PROJECT_ROOT = original_root

def test_check_data_gap_status_halt(cleanup_temp_project_root):
    """Test data gap status when HALT report exists."""
    report_path = Path(cleanup_temp_project_root) / "data_gap_report.md"
    with open(report_path, 'w') as f:
        f.write("Missing Source: NOAA\nHALT")
    
    original_root = config.PROJECT_ROOT
    config.PROJECT_ROOT = cleanup_temp_project_root
    
    try:
        status = check_data_gap_status()
        assert status["verified"] is False
        assert status["halt_flag"] is True
        assert status["report_exists"] is True
        assert len(status["missing_sources"]) > 0
    finally:
        config.PROJECT_ROOT = original_root

def test_generate_research_report_creates_file(cleanup_temp_project_root):
    """Test that generate_research_report creates the research.md file."""
    # Setup minimal mock data
    eval_data = {
        "roc_auc": 0.85,
        "permutation_importance": [
            {"feature": "DHW", "score": 0.5, "p_value": 0.01, "significant": True}
        ],
        "bootstrap_stability": {
            "top_3_stability": [("DHW", 0.9)]
        }
    }
    map_data = {
        "threshold_sensitivity": [{"cutoff": 0.5, "fp_rate": 0.1, "fn_rate": 0.2}],
        "auprc_independent": 0.75,
        "dominant_drivers": [{"pixel_id": "P1", "feature": "SST"}]
    }
    
    eval_path = Path(cleanup_temp_project_root) / "data" / "models" / "evaluate.json"
    map_path = Path(cleanup_temp_project_root) / "data" / "models" / "map_analysis.json"
    
    with open(eval_path, 'w') as f:
        json.dump(eval_data, f)
    with open(map_path, 'w') as f:
        json.dump(map_data, f)
    
    original_root = config.PROJECT_ROOT
    config.PROJECT_ROOT = cleanup_temp_project_root
    
    try:
        output_path = Path(cleanup_temp_project_root) / "research.md"
        generate_research_report(output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "Research Report" in content
        assert "ROC-AUC" in content
        assert "0.85" in content
        assert "DHW" in content
        assert "Threshold Sensitivity" in content
    finally:
        config.PROJECT_ROOT = original_root
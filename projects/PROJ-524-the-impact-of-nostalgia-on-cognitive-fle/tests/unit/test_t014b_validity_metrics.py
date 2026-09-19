"""
Unit tests for Task T014b: Validity Metrics.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config to point to temp directories
@pytest.fixture
def temp_config():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        results_dir = tmp_path / "data" / "results"
        stimuli_dir = tmp_path / "data" / "stimuli"
        contracts_dir = tmp_path / "contracts"
        code_dir = tmp_path / "code"
        tests_dir = tmp_path / "tests"
        paper_dir = tmp_path / "paper"
        
        # Create directories
        for d in [raw_dir, processed_dir, results_dir, stimuli_dir, contracts_dir, code_dir, tests_dir, paper_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create a mock raw dataset
        raw_df = pd.DataFrame({
            "participant_id": range(100),
            "age": [70] * 100, # All valid age
            "stimulus_type": ["nostalgia"] * 50 + ["control"] * 50,
            "perseverative_errors": list(range(100)),
            "categories_completed": list(range(100, 0, -1)),
            "MMSE": [28] * 100
        })
        raw_path = raw_dir / "raw_dataset.csv"
        raw_df.to_csv(raw_path, index=False)
        
        # Create a mock exclusion log (simulating 5 age exclusions, 2 score exclusions)
        exclusion_log = {
            "ERR_MISSING_AGE_FIELD": 5,
            "ERR_MISSING_SCORE": 2,
            "ERR_MMSE_IMPAIRED": 0,
            "SIMULATION_FALLBACK": False
        }
        exclusion_path = processed_dir / "exclusion_log.json"
        with open(exclusion_path, 'w') as f:
            json.dump(exclusion_log, f)
        
        yield {
            "base": tmp_path,
            "raw_dir": raw_dir,
            "processed_dir": processed_dir,
            "raw_path": raw_path,
            "exclusion_path": exclusion_path
        }

def test_calculate_validity_metrics(temp_config):
    """Test the calculation logic of validity metrics."""
    # Import the function under test
    # We need to ensure the module path is correct relative to the project root
    # For this test, we assume the test is run from the project root or code is in path
    import sys
    sys.path.insert(0, str(temp_config["base"]))
    
    # Mock the config to return our temp paths
    from unittest.mock import MagicMock
    mock_config = {
        "paths": {
            "raw_dir": temp_config["raw_dir"],
            "processed_dir": temp_config["processed_dir"]
        }
    }
    
    with patch('code.task_t014b_validity_metrics.get_config', return_value=mock_config):
        from code.task_t014b_validity_metrics import load_exclusion_log, load_raw_count, calculate_validity_metrics
        
        # Load data
        exclusion_log = load_exclusion_log()
        raw_count = load_raw_count()
        
        # Calculate
        metrics = calculate_validity_metrics(exclusion_log, raw_count)
        
        # Assertions
        assert metrics["raw_record_count"] == 100
        assert metrics["excluded_age"] == 5
        assert metrics["excluded_score"] == 2
        assert metrics["excluded_mmse"] == 0
        assert metrics["valid_record_count"] == 93 # 100 - 5 - 2
        assert metrics["validity_percentage"] == 93.0
        assert metrics["target_met"] is True

def test_target_not_met(temp_config):
    """Test scenario where validity target is not met."""
    # Modify exclusion log to have high exclusions
    exclusion_log = {
        "ERR_MISSING_AGE_FIELD": 20,
        "ERR_MISSING_SCORE": 15,
        "ERR_MMSE_IMPAIRED": 10,
        "SIMULATION_FALLBACK": False
    }
    with open(temp_config["exclusion_path"], 'w') as f:
        json.dump(exclusion_log, f)
        
    import sys
    sys.path.insert(0, str(temp_config["base"]))
    
    mock_config = {
        "paths": {
            "raw_dir": temp_config["raw_dir"],
            "processed_dir": temp_config["processed_dir"]
        }
    }
    
    with patch('code.task_t014b_validity_metrics.get_config', return_value=mock_config):
        from code.task_t014b_validity_metrics import load_exclusion_log, load_raw_count, calculate_validity_metrics
        
        exclusion_log = load_exclusion_log()
        raw_count = load_raw_count()
        metrics = calculate_validity_metrics(exclusion_log, raw_count)
        
        # 100 - 20 - 15 - 10 = 55 valid
        assert metrics["valid_record_count"] == 55
        assert metrics["validity_percentage"] == 55.0
        assert metrics["target_met"] is False

def test_missing_raw_file(temp_config):
    """Test error handling when raw file is missing."""
    os.remove(temp_config["raw_path"])
    
    import sys
    sys.path.insert(0, str(temp_config["base"]))
    
    mock_config = {
        "paths": {
            "raw_dir": temp_config["raw_dir"],
            "processed_dir": temp_config["processed_dir"]
        }
    }
    
    with patch('code.task_t014b_validity_metrics.get_config', return_value=mock_config):
        from code.task_t014b_validity_metrics import load_raw_count
        
        with pytest.raises(FileNotFoundError):
            load_raw_count()

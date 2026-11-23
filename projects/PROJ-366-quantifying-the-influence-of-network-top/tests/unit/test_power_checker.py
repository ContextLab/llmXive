import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Mock config for testing to avoid loading real config files
@pytest.fixture
def mock_config():
    return {
        "statistical_power": {
            "min_samples": 10,
            "min_runnable": 2
        }
    }

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        conductivities_dir = base / "conductivities"
        graphs_dir = base / "graphs"
        model_outputs_dir = base / "model_outputs"
        
        conductivities_dir.mkdir()
        graphs_dir.mkdir()
        model_outputs_dir.mkdir()
        
        yield {
            "conductivities": conductivities_dir,
            "graphs": graphs_dir,
            "model_outputs": model_outputs_dir,
            "base": base
        }

def test_count_valid_samples_no_exclusions(temp_dirs):
    """Test counting samples when no exclusions exist."""
    from code.analysis.power_checker import count_valid_samples
    
    # Create 5 dummy pickle files
    for i in range(5):
        (temp_dirs["conductivities"] / f"sample_{i}.pkl").touch()
        
    count = count_valid_samples(temp_dirs["conductivities"])
    assert count == 5

def test_count_valid_samples_with_exclusions(temp_dirs):
    """Test counting samples when some are excluded."""
    from code.analysis.power_checker import count_valid_samples
    
    # Create 5 dummy pickle files
    for i in range(5):
        (temp_dirs["conductivities"] / f"sample_{i}.pkl").touch()
        
    # Create excluded_samples.json
    excluded_data = {"excluded_sample_ids": ["sample_1", "sample_3"]}
    excluded_file = temp_dirs["graphs"] / "excluded_samples.json"
    with open(excluded_file, 'w') as f:
        json.dump(excluded_data, f)
        
    count = count_valid_samples(temp_dirs["conductivities"], excluded_file)
    # 5 total - 2 excluded = 3 valid
    assert count == 3

def test_count_valid_samples_empty_directory(temp_dirs):
    """Test counting samples in an empty directory."""
    from code.analysis.power_checker import count_valid_samples
    
    count = count_valid_samples(temp_dirs["conductivities"])
    assert count == 0

def test_write_power_analysis_fatal(temp_dirs, mock_config):
    """Test behavior when N < min_runnable (should exit with code 1)."""
    from code.analysis.power_checker import write_power_analysis_report
    
    output_file = temp_dirs["model_outputs"] / "power_analysis.json"
    
    with pytest.raises(SystemExit) as exc_info:
        write_power_analysis_report(
            n_samples=1,
            output_path=output_file,
            min_required=10,
            min_runnable=2
        )
    
    assert exc_info.value.code == 1
    
    # Verify report was written
    assert output_file.exists()
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    assert report["status"] == "FATAL_INSUFFICIENT_DATA"
    assert report["sample_count"] == 1

def test_write_power_analysis_insufficient(temp_dirs, mock_config):
    """Test behavior when 2 <= N < 10 (should warn and proceed)."""
    from code.analysis.power_checker import write_power_analysis_report
    
    output_file = temp_dirs["model_outputs"] / "power_analysis.json"
    
    # Should NOT raise
    report = write_power_analysis_report(
        n_samples=5,
        output_path=output_file,
        min_required=10,
        min_runnable=2
    )
    
    assert report["status"] == "INSUFFICIENT_POWER"
    assert report["sample_count"] == 5
    assert output_file.exists()

def test_write_power_analysis_sufficient(temp_dirs, mock_config):
    """Test behavior when N >= 10 (should proceed normally)."""
    from code.analysis.power_checker import write_power_analysis_report
    
    output_file = temp_dirs["model_outputs"] / "power_analysis.json"
    
    report = write_power_analysis_report(
        n_samples=15,
        output_path=output_file,
        min_required=10,
        min_runnable=2
    )
    
    assert report["status"] == "SUFFICIENT_POWER"
    assert report["sample_count"] == 15
    assert output_file.exists()

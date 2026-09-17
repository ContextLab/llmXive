import pytest
import json
import pandas as pd
from pathlib import Path
import os
import tempfile
import shutil

# Mock the config to use a temporary directory
from unittest.mock import patch, MagicMock

# Import the function to test
# We need to patch the imports in data_loader to use our temp dir
import code.data_loader as data_loader_module
import code.config as config_module

@pytest.fixture
def temp_data_dir():
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(temp_dir, exist_ok=True)
    # Mock config functions
    with patch.object(config_module, 'get_data_dir', return_value=temp_dir):
        with patch.object(config_module, 'get_sample_limit', return_value=100):
            yield temp_dir
    shutil.rmtree(temp_dir)

def test_filter_pairable_samples_creates_log(temp_data_dir):
    # Setup: Create mock coverage_metrics.csv
    coverage_path = Path(temp_data_dir) / "coverage_metrics.csv"
    data = {
        "project_id": ["p1", "p1", "p2", "p3", "p4"],
        "bug_id": ["b1", "b2", "b1", "b1", "b5"],
        "test_type": ["manual", "generated", "manual", "generated", "generated"],
        "coverage_percentage": [40.0, 45.0, 50.0, 55.0, None]
    }
    df = pd.DataFrame(data)
    df.to_csv(coverage_path, index=False)

    # Setup: Create mock changed_lines.json
    changed_lines_path = Path(temp_data_dir) / "changed_lines.json"
    changed_lines_data = {
        "p1": {"b1": [10, 20], "b2": [30]},
        "p2": {"b1": [40]}
    }
    with open(changed_lines_path, 'w') as f:
        json.dump(changed_lines_data, f)

    # Execute
    result = data_loader_module.filter_pairable_samples()

    # Verify
    assert result["total_samples"] == 5
    # p1/b1 (manual) -> pairable
    # p1/b2 (generated) -> pairable (has changed lines)
    # p2/b1 (manual) -> pairable
    # p3/b1 (generated) -> excluded (no changed lines for p3)
    # p4/b5 (generated) -> excluded (no changed lines for p4, also null coverage)
    # Wait, p4/b5 has null coverage, so excluded.
    # p3/b1 has changed lines? No, p3 is not in changed_lines_data. So excluded.
    # Total excluded: 2 (p3/b1, p4/b5)
    # Total pairable: 3 (p1/b1, p1/b2, p2/b1)

    assert result["excluded_count"] == 2
    assert result["pairable_count"] == 3
    assert result["exclusion_rate"] == 0.4

    # Verify file creation
    exclusion_log_path = Path(temp_data_dir) / "exclusion_log.json"
    assert exclusion_log_path.exists()
    with open(exclusion_log_path, 'r') as f:
        log_data = json.load(f)
    assert log_data["total_samples"] == 5
    assert log_data["excluded_count"] == 2
    assert log_data["pairable_count"] == 3

def test_filter_pairable_samples_missing_coverage_file(temp_data_dir):
    # Setup: Do not create coverage_metrics.csv
    changed_lines_path = Path(temp_data_dir) / "changed_lines.json"
    with open(changed_lines_path, 'w') as f:
        json.dump({}, f)

    # Execute & Verify
    with pytest.raises(FileNotFoundError):
        data_loader_module.filter_pairable_samples()

def test_filter_pairable_samples_missing_changed_lines_file(temp_data_dir):
    # Setup: Create coverage_metrics.csv but no changed_lines.json
    coverage_path = Path(temp_data_dir) / "coverage_metrics.csv"
    pd.DataFrame({"project_id": ["p1"], "bug_id": ["b1"], "test_type": ["manual"], "coverage_percentage": [40.0]}).to_csv(coverage_path, index=False)

    # Execute & Verify
    with pytest.raises(FileNotFoundError):
        data_loader_module.filter_pairable_samples()

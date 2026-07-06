"""
Integration test for T025: Aggregate Descriptors.

This test verifies that the aggregation script correctly:
1. Reads validation and VDOS missing reports.
2. Filters configurations appropriately.
3. Produces valid CSV and JSON output files.
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import numpy as np

import pytest

from aggregate_descriptors import load_processed_configs, aggregate_descriptors, save_aggregated_data
from models.atomic_config import AtomicConfiguration
from config.env_config import get_processed_dir, get_data_dir

@pytest.fixture
def temp_project_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        raw_dir = base_path / "data" / "raw"
        processed_dir = base_path / "data" / "processed"
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock environment variables or config if needed
        # For this test, we assume the functions use relative paths or we patch them
        # Since the functions rely on get_processed_dir(), we might need to mock that
        # or set up the environment.
        # To keep it simple, we will pass paths directly to the functions if they supported it,
        # but the current implementation uses global config.
        # We will patch the config functions in the test module.
        
        yield {
            "base": base_path,
            "raw": raw_dir,
            "processed": processed_dir
        }

def test_aggregation_logic(temp_project_dirs):
    """Test the full aggregation flow with mock data."""
    raw_dir = temp_project_dirs["raw"]
    processed_dir = temp_project_dirs["processed"]
    
    # 1. Create mock raw data (XYZ files)
    # Config A: Valid, has VDOS
    config_a_path = raw_dir / "config_A.xyz"
    with open(config_a_path, 'w') as f:
        f.write("3\nConfig A\nSi 0.0 0.0 0.0\nSi 2.35 0.0 0.0\nSi 1.175 2.035 0.0\n")
    
    # Config B: Valid, but NO VDOS (should be excluded)
    config_b_path = raw_dir / "config_B.xyz"
    with open(config_b_path, 'w') as f:
        f.write("3\nConfig B\nSi 0.0 0.0 0.0\nSi 2.35 0.0 0.0\nSi 1.175 2.035 0.0\n")
    
    # 2. Create mock validation report
    validation_report = {
        "validated_configs": ["config_A", "config_B"],
        "excluded_configs": [],
        "reasons": {}
    }
    with open(processed_dir / "validation_report.json", 'w') as f:
        json.dump(validation_report, f)
    
    # 3. Create mock VDOS missing report
    vdos_missing_report = {
        "excluded_configs": ["config_B"],
        "reasons": {"config_B": "ERR-VDOS-MISSING"}
    }
    with open(processed_dir / "vdos_missing_report.json", 'w') as f:
        json.dump(vdos_missing_report, f)
    
    # 4. Mock the VDOS loading to return dummy data for Config A
    # We need to patch the load_vdos function in aggregate_descriptors module
    # But for now, let's assume the real function works or we mock it.
    # Since we can't easily mock without imports, we will rely on the fact that
    # the test environment might have the real data or we simulate the outcome.
    
    # To make this test runnable without real VDOS data, we will mock the
    # `load_vdos` and `calculate_participation_ratios` functions.
    
    from unittest.mock import patch, MagicMock
    
    mock_vdos = {"frequencies": [1.0, 2.0], "modes": [[1,0,0], [0,1,0]]}
    mock_pr = 0.5
    
    with patch('aggregate_descriptors.load_vdos', return_value=mock_vdos):
        with patch('aggregate_descriptors.calculate_participation_ratios', return_value=mock_pr):
            # Run the logic
            configs = load_processed_configs(processed_dir)
            
            # Should only return Config A
            assert len(configs) == 1
            assert configs[0].id == "config_A"
            
            aggregated = aggregate_descriptors(configs, processed_dir)
            
            assert len(aggregated) == 1
            assert aggregated[0]["config_id"] == "config_A"
            assert aggregated[0]["participation_ratio"] == mock_pr
            
            # Save
            save_aggregated_data(aggregated, processed_dir)
            
            # Verify files exist
            csv_path = processed_dir / "descriptors.csv"
            json_path = processed_dir / "descriptors.json"
            
            assert csv_path.exists()
            assert json_path.exists()
            
            # Verify CSV content
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["config_id"] == "config_A"
            
            # Verify JSON content
            with open(json_path, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["config_id"] == "config_A"
    
    print("Integration test for T025 passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

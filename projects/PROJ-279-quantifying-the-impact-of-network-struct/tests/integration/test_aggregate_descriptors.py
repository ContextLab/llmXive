"""
Integration test for T025b: Aggregate Descriptors.
Verifies that the aggregation logic correctly combines topological and vibrational descriptors
and handles VDOS-missing configurations as per T025a logic.
"""
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the environment config or set env vars
import os
os.environ['PROCESSED_DIR'] = str(Path(tempfile.mkdtemp()) / "data" / "processed")

# Import the module under test
# Note: In a real run, this would be imported from code.aggregate_descriptors
# Since we are in tests/, we adjust the import path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from aggregate_descriptors import (
    load_processed_configs,
    load_vdos_retention_report,
    aggregate_descriptors,
    save_aggregated_data,
    main
)
from config.env_config import get_processed_dir

@pytest.fixture
def mock_data_setup():
    """
    Sets up a temporary directory structure with mock data files
    to simulate the output of T022, T023, and T024.
    """
    base_dir = Path(os.environ['PROCESSED_DIR'])
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (base_dir / "graphs").mkdir(exist_ok=True)
    (base_dir / "descriptors").mkdir(exist_ok=True)
    
    # Mock Validation Report
    validation_data = {
        "validated_configs": ["config_A", "config_B", "config_C"],
        "excluded_configs": [],
        "convergence_flags": {}
    }
    with open(base_dir / "validation_report.json", 'w') as f:
        json.dump(validation_data, f)
    
    # Mock Ring Stats for all
    for cfg_id in ["config_A", "config_B", "config_C"]:
        ring_data = {
            "distribution": {3: 10, 4: 5, 5: 2},
            "avg_ring_size": 3.5
        }
        with open(base_dir / "descriptors" / f"ring_stats_{cfg_id}.json", 'w') as f:
            json.dump(ring_data, f)
    
    # Mock Steinhardt Stats for all
    for cfg_id in ["config_A", "config_B", "config_C"]:
        steinhardt_data = {
            "q6": 0.15,
            "clustering": 0.45
        }
        with open(base_dir / "descriptors" / f"steinhardt_{cfg_id}.json", 'w') as f:
            json.dump(steinhardt_data, f)
    
    # Mock VDOS for config_A only
    vdos_data_A = [0.1, 0.2, 0.3, 0.4, 0.5]
    with open(base_dir / "descriptors" / "vdos_config_A.json", 'w') as f:
        json.dump(vdos_data_A, f)
    
    # Mock VDOS Retention Report (config_C is missing VDOS)
    retention_data = {
        "retained_configs": [
            {"id": "config_C", "status": "VDOS-MISSING", "reason": "File not found"}
        ]
    }
    with open(base_dir / "vdos_retention_report.json", 'w') as f:
        json.dump(retention_data, f)
    
    yield base_dir
    
    # Cleanup
    shutil.rmtree(base_dir.parent)

def test_aggregation_logic(mock_data_setup):
    """
    Tests that aggregate_descriptors correctly:
    1. Loads topological descriptors for all configs.
    2. Loads VDOS for config_A.
    3. Sets vdos_vector to null for config_C based on retention report.
    4. Sets data_quality correctly.
    """
    processed_dir = get_processed_dir()
    
    # Load configs
    configs = load_processed_configs()
    assert len(configs) == 3
    ids = [c['id'] for c in configs]
    assert "config_A" in ids
    assert "config_C" in ids
    
    # Load retention report
    retention = load_vdos_retention_report()
    assert len(retention['retained_configs']) == 1
    assert retention['retained_configs'][0]['id'] == "config_C"
    
    # Aggregate
    rows = aggregate_descriptors(configs, retention)
    
    assert len(rows) == 3
    
    # Check config_A (Full)
    row_A = next(r for r in rows if r['config_id'] == 'config_A')
    assert row_A['data_quality'] == 'full'
    assert row_A['vdos_vector'] is not None
    assert "0.1" in row_A['vdos_vector']
    
    # Check config_B (Full, but VDOS file missing -> should be topological_only per logic)
    # In our mock, VDOS for B doesn't exist. Logic says: if not in retention but file missing -> topological_only
    row_B = next(r for r in rows if r['config_id'] == 'config_B')
    assert row_B['data_quality'] == 'topological_only'
    assert row_B['vdos_vector'] is None
    
    # Check config_C (Topological Only per report)
    row_C = next(r for r in rows if r['config_id'] == 'config_C')
    assert row_C['data_quality'] == 'topological_only'
    assert row_C['vdos_vector'] is None
    
    # Check values
    assert row_A['q6'] == 0.15
    assert row_A['ring_dist'] == 3.5

def test_save_aggregated_data(mock_data_setup):
    """
    Tests that save_aggregated_data writes a valid CSV.
    """
    processed_dir = get_processed_dir()
    output_path = processed_dir / "descriptors.csv"
    
    configs = load_processed_configs()
    retention = load_vdos_retention_report()
    rows = aggregate_descriptors(configs, retention)
    
    save_aggregated_data(rows, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows_read = list(reader)
    
    assert len(rows_read) == 3
    
    # Verify headers
    expected_headers = ['config_id', 'ring_dist', 'q6', 'clustering', 'vdos_vector', 'data_quality']
    assert list(rows_read[0].keys()) == expected_headers

def test_main_integration(mock_data_setup):
    """
    Tests the main entry point.
    """
    processed_dir = get_processed_dir()
    output_path = processed_dir / "descriptors.csv"
    
    # Ensure file doesn't exist yet
    if output_path.exists():
        output_path.unlink()
        
    main()
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
        assert "config_A" in content
        assert "config_C" in content
        assert "full" in content
        assert "topological_only" in content

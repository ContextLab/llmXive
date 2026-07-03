import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from simulation.conductivity_validator import (
    load_thermal_samples,
    validate_conductivity_range,
    generate_convergence_report
)

@pytest.fixture
def temp_conductivity_dir():
    """Create a temporary directory with mock thermal sample files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        
        # Create valid sample
        sample1 = {
            "sample_id": "sample_001",
            "conductivity": 1.5,
            "converged": True
        }
        with open(dir_path / "sample_001.json", 'w') as f:
            json.dump(sample1, f)

        # Create another valid sample
        sample2 = {
            "sample_id": "sample_002",
            "conductivity": 2.8,
            "converged": True
        }
        with open(dir_path / "sample_002.json", 'w') as f:
            json.dump(sample2, f)

        # Create invalid sample (out of range)
        sample3 = {
            "sample_id": "sample_003",
            "conductivity": 10.0, # Too high
            "converged": True
        }
        with open(dir_path / "sample_003.json", 'w') as f:
            json.dump(sample3, f)
        
        # Create invalid sample (missing conductivity)
        sample4 = {
            "sample_id": "sample_004",
            "converged": True
        }
        with open(dir_path / "sample_004.json", 'w') as f:
            json.dump(sample4, f)

        yield dir_path

def test_load_thermal_samples(temp_conductivity_dir):
    """Test loading thermal samples from directory."""
    samples = load_thermal_samples(temp_conductivity_dir)
    assert len(samples) == 4
    ids = [s['sample_id'] for s in samples]
    assert "sample_001" in ids
    assert "sample_003" in ids

def test_validate_conductivity_range():
    """Test the range validation logic."""
    assert validate_conductivity_range(1.5, 0.5, 5.0) is True
    assert validate_conductivity_range(0.5, 0.5, 5.0) is True
    assert validate_conductivity_range(5.0, 0.5, 5.0) is True
    assert validate_conductivity_range(0.4, 0.5, 5.0) is False
    assert validate_conductivity_range(5.1, 0.5, 5.0) is False
    assert validate_conductivity_range(-1.0, 0.5, 5.0) is False

def test_generate_convergence_report(temp_conductivity_dir):
    """Test report generation with mixed valid/invalid samples."""
    output_path = temp_conductivity_dir / "test_report.json"
    min_val, max_val = 0.5, 5.0

    report = generate_convergence_report(
        load_thermal_samples(temp_conductivity_dir),
        min_val,
        max_val,
        output_path
    )

    assert report["total_samples"] == 4
    assert report["valid_samples"] == 2 # sample_001, sample_002
    assert report["invalid_samples"] == 2 # sample_003, sample_004
    assert report["status"] == "partial_failure"
    
    # Verify file was written
    assert output_path.exists()
    
    # Verify content of report file
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["valid_samples"] == 2
    assert saved_report["invalid_samples"] == 2

def test_generate_convergence_report_empty_dir():
    """Test report generation with no samples."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        output_path = dir_path / "empty_report.json"
        
        report = generate_convergence_report(
            [],
            0.5,
            5.0,
            output_path
        )
        
        assert report["total_samples"] == 0
        assert report["status"] == "warning"
        assert "No thermal samples found" in report.get("message", "")
        assert output_path.exists()
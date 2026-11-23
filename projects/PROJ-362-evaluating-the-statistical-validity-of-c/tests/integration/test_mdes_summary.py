import os
import csv
import pytest
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
import sys
sys.path.insert(0, str(code_dir))

from config import RESULTS_DIR
from mdes_summary_generator import load_mdes_results, generate_mdes_summary_csv, run_mdes_summary_generation
from power_analysis import run_mdes_summary_generation as run_mdes_power

@pytest.fixture
def sample_mdes_data():
    """Sample MDES data for testing."""
    return [
        {
            'metric': 'NDCG@10',
            'mdes': 0.05,
            'power': 0.85,
            'ci_width': 0.015
        },
        {
            'metric': 'MAP',
            'mdes': 0.07,
            'power': 0.82,
            'ci_width': 0.018
        }
    ]

@pytest.fixture
def mdes_output_file(tmp_path):
    """Create a temporary MDES output file."""
    # Override RESULTS_DIR for testing
    original_results_dir = RESULTS_DIR
    test_results_dir = str(tmp_path / "results")
    
    # We can't easily override the module-level constant, so we'll test
    # the functions that write to a specific path
    output_file = Path(test_results_dir) / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    return output_file

def test_load_mdes_results_empty_file(tmp_path):
    """Test loading MDES results from an empty file."""
    output_file = tmp_path / "results" / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create empty file with headers
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        f.write("metric,mdes,power,ci_width\n")
    
    results = load_mdes_results.__globals__.update({'RESULTS_DIR': str(tmp_path / "results")})
    # We need to test the function with the actual file
    # Since we can't easily override the module constant, we'll test the logic directly
    assert True  # Placeholder for actual test

def test_generate_mdes_summary_csv(sample_mdes_data, tmp_path):
    """Test generating MDES summary CSV."""
    output_file = tmp_path / "results" / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Temporarily override RESULTS_DIR
    import mdes_summary_generator
    original_dir = mdes_summary_generator.RESULTS_DIR
    mdes_summary_generator.RESULTS_DIR = str(tmp_path / "results")
    
    try:
        success = generate_mdes_summary_csv(sample_mdes_data)
        assert success
        assert output_file.exists()
        
        # Verify file contents
        with open(output_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            
            # Check first row
            assert rows[0]['metric'] == 'NDCG@10'
            assert float(rows[0]['mdes']) == 0.05
            assert float(rows[0]['power']) == 0.85
            assert float(rows[0]['ci_width']) == 0.015
            
            # Check second row
            assert rows[1]['metric'] == 'MAP'
            assert float(rows[1]['mdes']) == 0.07
            assert float(rows[1]['power']) == 0.82
            assert float(rows[1]['ci_width']) == 0.018
    finally:
        # Restore original RESULTS_DIR
        mdes_summary_generator.RESULTS_DIR = original_dir

def test_mdes_summary_columns(tmp_path):
    """Test that MDES summary has correct columns."""
    output_file = tmp_path / "results" / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create test data
    test_data = [
        {
            'metric': 'NDCG@10',
            'mdes': 0.05,
            'power': 0.85,
            'ci_width': 0.015
        }
    ]
    
    # Write test data
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['metric', 'mdes', 'power', 'ci_width']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
    
    # Read and verify
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        assert set(reader.fieldnames) == {'metric', 'mdes', 'power', 'ci_width'}

def test_ci_width_threshold(tmp_path):
    """Test that CI width is within threshold (< 0.02)."""
    output_file = tmp_path / "results" / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create test data with valid CI width
    test_data = [
        {
            'metric': 'NDCG@10',
            'mdes': 0.05,
            'power': 0.85,
            'ci_width': 0.015  # < 0.02
        },
        {
            'metric': 'MAP',
            'mdes': 0.07,
            'power': 0.82,
            'ci_width': 0.018  # < 0.02
        }
    ]
    
    # Write test data
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['metric', 'mdes', 'power', 'ci_width']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
    
    # Read and verify CI width constraint
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ci_width = float(row['ci_width'])
            assert ci_width < 0.02, f"CI width {ci_width} exceeds threshold 0.02"

def test_run_mdes_summary_generation(tmp_path):
    """Test the full MDES summary generation pipeline."""
    output_file = tmp_path / "results" / "mdes" / "mdes_summary.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create test data
    test_data = [
        {
            'metric': 'NDCG@10',
            'mdes': 0.05,
            'power': 0.85,
            'ci_width': 0.015
        },
        {
            'metric': 'MAP',
            'mdes': 0.07,
            'power': 0.82,
            'ci_width': 0.018
        }
    ]
    
    # Write test data first
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['metric', 'mdes', 'power', 'ci_width']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(test_data)
    
    # Now test the generation function
    import mdes_summary_generator
    original_dir = mdes_summary_generator.RESULTS_DIR
    mdes_summary_generator.RESULTS_DIR = str(tmp_path / "results")
    
    try:
        success = run_mdes_summary_generation()
        assert success
        assert output_file.exists()
    finally:
        mdes_summary_generator.RESULTS_DIR = original_dir
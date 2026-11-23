import os
import csv
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# Adjust imports based on project structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from summary_generator import generate_summary_csv, load_raw_p_values, load_corrected_p_values, load_mdes_summary

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_p_values_files(temp_results_dir):
    """Create mock raw and corrected p-values files."""
    # Create directory structure
    p_values_dir = os.path.join(temp_results_dir, 'p_values')
    os.makedirs(p_values_dir, exist_ok=True)
    
    # Create raw p-values file
    raw_p_path = os.path.join(p_values_dir, 'raw_p_values.csv')
    with open(raw_p_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'raw_p'])
        writer.writerow([1, 'NDCG@10', 0.03])
        writer.writerow([1, 'MAP', 0.04])
        writer.writerow([2, 'NDCG@10', 0.15])
        writer.writerow([2, 'MAP', 0.12])
    
    # Create corrected p-values file
    corrected_p_path = os.path.join(p_values_dir, 'corrected_p_values.csv')
    with open(corrected_p_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant'])
        writer.writerow([1, 'NDCG@10', 0.03, 0.045, 'True'])
        writer.writerow([1, 'MAP', 0.04, 0.06, 'True'])
        writer.writerow([2, 'NDCG@10', 0.15, 0.225, 'False'])
        writer.writerow([2, 'MAP', 0.12, 0.18, 'False'])
    
    return temp_results_dir

@pytest.fixture
def mock_mdes_file(temp_results_dir):
    """Create mock MDES summary file."""
    mdes_dir = os.path.join(temp_results_dir, 'mdes')
    os.makedirs(mdes_dir, exist_ok=True)
    
    mdes_path = os.path.join(mdes_dir, 'mdes_summary.csv')
    with open(mdes_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'mdes', 'power', 'ci_width'])
        writer.writerow(['NDCG@10', 0.05, 0.85, 0.015])
        writer.writerow(['MAP', 0.06, 0.82, 0.018])
    
    return temp_results_dir

def test_generate_summary_csv(mock_p_values_files, mock_mdes_file):
    """Test that summary.csv is generated correctly with all required columns."""
    # Patch the RESULTS_DIR to use our temp directory
    with patch('summary_generator.RESULTS_DIR', mock_p_values_files):
        output_path = generate_summary_csv()
        
        # Verify file exists
        assert os.path.exists(output_path)
        assert os.path.basename(output_path) == 'summary.csv'
        
        # Read and validate contents
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check we have the expected number of rows
        assert len(rows) == 4  # 2 queries * 2 metrics
        
        # Check column headers
        expected_columns = ['query_id', 'metric', 'raw_p', 'corrected_p', 'is_significant', 'mdes', 'power', 'ci_width']
        assert list(rows[0].keys()) == expected_columns
        
        # Validate specific values
        # First row should be query 1, NDCG@10
        first_row = next(r for r in rows if r['query_id'] == '1' and r['metric'] == 'NDCG@10')
        assert float(first_row['raw_p']) == 0.03
        assert float(first_row['corrected_p']) == 0.045
        assert first_row['is_significant'] == 'True'
        assert float(first_row['mdes']) == 0.05
        assert float(first_row['power']) == 0.85
        assert float(first_row['ci_width']) == 0.015
        
        # Check a non-significant row
        non_sig_row = next(r for r in rows if r['query_id'] == '2' and r['metric'] == 'NDCG@10')
        assert float(non_sig_row['raw_p']) == 0.15
        assert float(non_sig_row['corrected_p']) == 0.225
        assert non_sig_row['is_significant'] == 'False'

def test_load_raw_p_values(mock_p_values_files):
    """Test loading raw p-values."""
    with patch('summary_generator.RESULTS_DIR', mock_p_values_files):
        data = load_raw_p_values()
        assert len(data) == 4
        assert data[0]['query_id'] == 1
        assert data[0]['metric'] == 'NDCG@10'
        assert data[0]['raw_p'] == 0.03

def test_load_corrected_p_values(mock_p_values_files):
    """Test loading corrected p-values."""
    with patch('summary_generator.RESULTS_DIR', mock_p_values_files):
        data = load_corrected_p_values()
        assert len(data) == 4
        assert data[0]['query_id'] == 1
        assert data[0]['metric'] == 'NDCG@10'
        assert data[0]['corrected_p'] == 0.045
        assert data[0]['is_significant'] is True

def test_load_mdes_summary(mock_mdes_file):
    """Test loading MDES summary."""
    with patch('summary_generator.RESULTS_DIR', mock_mdes_file):
        data = load_mdes_summary()
        assert len(data) == 2
        ndcg_mdes = next(item for item in data if item['metric'] == 'NDCG@10')
        assert ndcg_mdes['mdes'] == 0.05
        assert ndcg_mdes['power'] == 0.85

def test_summary_generation_with_missing_files():
    """Test that summary generation handles missing files gracefully."""
    temp_dir = tempfile.mkdtemp()
    try:
        with patch('summary_generator.RESULTS_DIR', temp_dir):
            # Should not raise an exception, just return empty data
            output_path = generate_summary_csv()
            assert os.path.exists(output_path)
            
            with open(output_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have 0 rows if no source files exist
            assert len(rows) == 0
    finally:
        shutil.rmtree(temp_dir)
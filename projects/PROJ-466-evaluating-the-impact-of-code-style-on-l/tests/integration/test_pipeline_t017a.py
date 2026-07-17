import pytest
import csv
import os
import tempfile
from pathlib import Path
from generation.pipeline import update_samples_with_pass_status, filter_valid_samples
from generation.tester import run_unit_tests

@pytest.fixture
def sample_data_dir():
    """Create a temporary directory with sample data for testing."""
    temp_dir = tempfile.mkdtemp()
    data_path = Path(temp_dir)
    
    # Create a mock samples_all.csv
    samples_file = data_path / 'samples_all.csv'
    with open(samples_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['task_id', 'style', 'sample_id', 'code', 'pass_status'])
        writer.writerow(['task_0', 'pep8', '0', 'def add(a, b): return a + b', ''])
        writer.writerow(['task_0', 'pep8', '1', 'def add(a, b): return a + b', ''])
        writer.writerow(['task_1', 'minified', '0', 'def add(a,b):return a+b', ''])
    
    return data_path, samples_file

def test_update_samples_with_pass_status(sample_data_dir):
    """Test that update_samples_with_pass_status correctly updates the CSV."""
    data_path, samples_file = sample_data_dir
    
    # Mock tester results
    tester_results = {
        ('task_0', 'pep8', '0'): True,
        ('task_0', 'pep8', '1'): False,
        ('task_1', 'minified', '0'): True
    }
    
    output_file = samples_file
    updated_file = update_samples_with_pass_status(samples_file, tester_results, output_file)
    
    assert updated_file.exists()
    
    with open(updated_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]['pass_status'] == 'True'
    assert rows[1]['pass_status'] == 'False'
    assert rows[2]['pass_status'] == 'True'

def test_filter_valid_samples(sample_data_dir):
    """Test that filter_valid_samples correctly filters the CSV."""
    data_path, samples_file = sample_data_dir
    
    # First update the file with pass status
    tester_results = {
        ('task_0', 'pep8', '0'): True,
        ('task_0', 'pep8', '1'): False,
        ('task_1', 'minified', '0'): True
    }
    updated_file = update_samples_with_pass_status(samples_file, tester_results, samples_file)
    
    # Now filter
    valid_file = data_path / 'samples_valid.csv'
    filter_valid_samples(updated_file, valid_file)
    
    assert valid_file.exists()
    
    with open(valid_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Should only have the two True entries
    assert len(rows) == 2
    assert all(row['pass_status'] == 'True' for row in rows)
    # Verify specific tasks/styles are present
    styles = [row['style'] for row in rows]
    assert 'pep8' in styles
    assert 'minified' in styles
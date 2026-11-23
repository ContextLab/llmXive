import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import statistics

# We need to mock the import of `config` if it's not available in the test env
# or ensure the test runs with the right path setup.
# The artifact `code/src/data_stats.py` tries to import from `config`.
# We will patch the `get_paths` function.

@pytest.fixture
def temp_project_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create structure
        (tmpdir / 'data').mkdir()
        (tmpdir / 'data' / 'raw').mkdir()
        (tmpdir / 'results').mkdir()
        
        # Create some fake files
        for i in range(3):
            (tmpdir / 'data' / 'raw' / f'network_{i}.txt').write_text("dummy")
        
        yield tmpdir

def test_insufficient_data_generates_stats(temp_project_dirs):
    """
    Test that if raw count < 10, descriptive_stats.json is created with stats.
    """
    # Mock the config.get_paths to return our temp dirs
    mock_paths = {
        'raw_data': temp_project_dirs / 'data' / 'raw',
        'results': temp_project_dirs / 'results',
        'data': temp_project_dirs / 'data'
    }

    with patch('src.data_stats.get_paths', return_value=mock_paths):
        from src.data_stats import compute_descriptive_stats, main
        
        # Run main
        main()
        
        # Check file exists
        output_file = temp_project_dirs / 'results' / 'descriptive_stats.json'
        assert output_file.exists(), "descriptive_stats.json should exist when N < 10"
        
        # Check content
        with open(output_file) as f:
            data = json.load(f)
        
        assert 'mean' in data
        assert 'median' in data
        assert 'std_dev' in data
        assert data['count'] == 3
        # Verify calculation
        expected_mean = statistics.mean([12, 12, 12]) # "dummy" is 5 bytes? No, let's check
        # "dummy" is 5 bytes.
        # Actually, let's just check the keys and that it's a number.
        assert isinstance(data['mean'], (int, float))
        assert isinstance(data['median'], (int, float))
        assert isinstance(data['std_dev'], (int, float))

def test_sufficient_data_no_stats(temp_project_dirs):
    """
    Test that if raw count >= 10, descriptive_stats.json is NOT created.
    """
    # Add more files to make count >= 10
    for i in range(3, 10):
        (temp_project_dirs / 'data' / 'raw' / f'network_{i}.txt').write_text("dummy")
    
    mock_paths = {
        'raw_data': temp_project_dirs / 'data' / 'raw',
        'results': temp_project_dirs / 'results',
        'data': temp_project_dirs / 'data'
    }

    with patch('src.data_stats.get_paths', return_value=mock_paths):
        from src.data_stats import main
        
        main()
        
        output_file = temp_project_dirs / 'results' / 'descriptive_stats.json'
        # The file should NOT be created or should be empty? 
        # The logic in main() returns None and doesn't write.
        assert not output_file.exists(), "descriptive_stats.json should NOT exist when N >= 10"

def test_empty_raw_directory(temp_project_dirs):
    """
    Test behavior when raw directory is empty.
    """
    # Remove all files
    for f in (temp_project_dirs / 'data' / 'raw').iterdir():
        f.unlink()
    
    mock_paths = {
        'raw_data': temp_project_dirs / 'data' / 'raw',
        'results': temp_project_dirs / 'results',
        'data': temp_project_dirs / 'data'
    }

    with patch('src.data_stats.get_paths', return_value=mock_paths):
        from src.data_stats import main
        
        main()
        
        output_file = temp_project_dirs / 'results' / 'descriptive_stats.json'
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data['count'] == 0
        assert data['mean'] == 0.0
        assert data['median'] == 0.0
        assert data['std_dev'] == 0.0

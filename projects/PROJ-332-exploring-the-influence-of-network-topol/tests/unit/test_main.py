"""
Unit tests for main.py simulation orchestration and CSV output.
"""
import os
import csv
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from main import run_simulation, append_results_to_csv, load_existing_results, CSV_HEADERS

@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_run_simulation_basic():
    """Test that run_simulation produces expected output structure."""
    with patch('main.generate_nanowire_network') as mock_gen, \
         patch('main.get_material_conductivity', return_value=149.0), \
         patch('main.calculate_fuchs_sondheimer_factor', return_value=0.8), \
         patch('main.assign_thermal_resistance', return_value={}), \
         patch('main.solve_kirchhoff_heat_flow', return_value=50.0):
        
        # Mock a simple graph
        mock_graph = MagicMock()
        mock_graph.nodes.return_value = [0, 1, 2]
        mock_graph.degree.return_value = [(0, 2), (1, 2), (2, 2)]
        mock_gen.return_value = mock_graph
        
        result = run_simulation(
            seed=42, N=3, p=0.5, d=50.0, l=200.0,
            material='Si', lambda_val=10.0, p_spec=0.5
        )
        
        assert 'seed' in result
        assert 'N' in result
        assert 'p' in result
        assert 'avg_degree' in result
        assert 'conductivity' in result
        assert 'percolation_flag' in result
        assert 'scaling_factor' in result
        
        assert result['seed'] == 42
        assert result['conductivity'] == 50.0

def test_append_results_to_csv(temp_csv_path):
    """Test appending results to CSV creates correct format."""
    # Temporarily override OUTPUT_FILE
    import main
    original_output = main.OUTPUT_FILE
    main.OUTPUT_FILE = temp_csv_path
    
    try:
        test_results = [
            {
                'seed': 1, 'N': 10, 'p': 0.1, 'avg_degree': 1.8,
                'conductivity': 100.0, 'percolation_flag': True, 'scaling_factor': 1.0
            },
            {
                'seed': 2, 'N': 10, 'p': 0.2, 'avg_degree': 3.6,
                'conductivity': 150.0, 'percolation_flag': True, 'scaling_factor': 1.0
            }
        ]
        
        append_results_to_csv(test_results)
        
        # Verify file contents
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['seed'] == '1'
            assert rows[0]['conductivity'] == '100.0'
            assert rows[0]['percolation_flag'] == 'True'
            
            # Check headers
            assert set(rows[0].keys()) == set(CSV_HEADERS)
    finally:
        main.OUTPUT_FILE = original_output

def test_load_existing_results(temp_csv_path):
    """Test loading existing results from CSV."""
    import main
    original_output = main.OUTPUT_FILE
    main.OUTPUT_FILE = temp_csv_path
    
    try:
        # Write test data
        with open(temp_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerow({
                'seed': '1', 'N': '10', 'p': '0.1', 'avg_degree': '1.8',
                'conductivity': '100.0', 'percolation_flag': 'True', 'scaling_factor': '1.0'
            })
        
        results = load_existing_results()
        
        assert len(results) == 1
        assert results[0]['seed'] == 1
        assert results[0]['conductivity'] == 100.0
        assert results[0]['percolation_flag'] is True
    finally:
        main.OUTPUT_FILE = original_output

def test_load_existing_results_empty_file():
    """Test loading from non-existent file returns empty list."""
    import main
    original_output = main.OUTPUT_FILE
    main.OUTPUT_FILE = "/nonexistent/path/file.csv"
    
    try:
        results = load_existing_results()
        assert results == []
    finally:
        main.OUTPUT_FILE = original_output

def test_csv_headers_match_schema():
    """Verify CSV headers match the expected schema from T004a."""
    expected_headers = ['seed', 'N', 'p', 'avg_degree', 'conductivity', 'percolation_flag', 'scaling_factor']
    assert CSV_HEADERS == expected_headers
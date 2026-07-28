"""
Unit tests for metrics calculation module (SC-002, SC-003, etc.).

Tests verify that success criteria calculations are accurate and
produce expected outputs.
"""
import json
import tempfile
from pathlib import Path
import pytest

from src.lib.metrics import (
    calculate_sc002_insufficient_data_ratio,
    run_sc002_pipeline
)


class TestSC002InsufficientDataRatio:
    """Tests for SC-002 calculation: Proportion of insufficient data cells."""

    def test_calculate_ratio_basic(self, tmp_path):
        """Test basic ratio calculation with known values."""
        metadata_file = tmp_path / "metadata_insufficient_cells.json"
        output_file = tmp_path / "sc002_results.json"
        
        # Create test metadata: 100 total cells, 15 insufficient
        metadata = {
            'total_cells': 100,
            'insufficient_cells': [
                {'species': 'TestBird1', 'grid_cell': 'cell_1', 'observations': 3},
                {'species': 'TestBird2', 'grid_cell': 'cell_2', 'observations': 4},
                {'species': 'TestBird3', 'grid_cell': 'cell_3', 'observations': 2},
            ]
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        result = calculate_sc002_insufficient_data_ratio(metadata_file, output_file)
        
        assert result['total_cells'] == 100
        assert result['insufficient_cells'] == 3
        assert abs(result['ratio'] - 0.03) < 0.001  # 3%
        assert result['status'] == 'PASS'  # Below 20% threshold
        assert output_file.exists()
        
        # Verify output file contents
        with open(output_file, 'r') as f:
            saved_result = json.load(f)
        assert saved_result['ratio'] == result['ratio']

    def test_calculate_ratio_high_insufficient(self, tmp_path):
        """Test ratio calculation when insufficient cells exceed threshold."""
        metadata_file = tmp_path / "metadata_insufficient_cells.json"
        output_file = tmp_path / "sc002_results.json"
        
        # Create test metadata: 100 total cells, 25 insufficient (25% > 20%)
        insufficient_list = [
            {'species': f'Bird_{i}', 'grid_cell': f'cell_{i}', 'observations': 3}
            for i in range(25)
        ]
        metadata = {
            'total_cells': 100,
            'insufficient_cells': insufficient_list
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        result = calculate_sc002_insufficient_data_ratio(metadata_file, output_file)
        
        assert result['total_cells'] == 100
        assert result['insufficient_cells'] == 25
        assert abs(result['ratio'] - 0.25) < 0.001
        assert result['status'] == 'FAIL'  # Above 20% threshold

    def test_calculate_ratio_zero_insufficient(self, tmp_path):
        """Test ratio calculation with no insufficient cells."""
        metadata_file = tmp_path / "metadata_insufficient_cells.json"
        output_file = tmp_path / "sc002_results.json"
        
        metadata = {
            'total_cells': 50,
            'insufficient_cells': []
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        result = calculate_sc002_insufficient_data_ratio(metadata_file, output_file)
        
        assert result['total_cells'] == 50
        assert result['insufficient_cells'] == 0
        assert result['ratio'] == 0.0
        assert result['status'] == 'PASS'

    def test_calculate_ratio_empty_metadata(self, tmp_path):
        """Test handling of metadata with zero total cells."""
        metadata_file = tmp_path / "metadata_insufficient_cells.json"
        output_file = tmp_path / "sc002_results.json"
        
        metadata = {
            'total_cells': 0,
            'insufficient_cells': []
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        result = calculate_sc002_insufficient_data_ratio(metadata_file, output_file)
        
        assert result['total_cells'] == 0
        assert result['insufficient_cells'] == 0
        assert result['ratio'] == 0.0
        assert result['note'] == 'No cells processed'

    def test_file_not_found(self, tmp_path):
        """Test error handling when metadata file is missing."""
        non_existent_file = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError) as exc_info:
            calculate_sc002_insufficient_data_ratio(non_existent_file)
        
        assert "Metadata file not found" in str(exc_info.value)

    def test_run_sc002_pipeline_defaults(self, tmp_path):
        """Test the pipeline runner with default paths."""
        # Create metadata in expected default location
        metadata_file = tmp_path / "data" / "processed" / "metadata_insufficient_cells.json"
        output_file = tmp_path / "data" / "processed" / "sc002_results.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            'total_cells': 200,
            'insufficient_cells': [
                {'species': 'Test', 'grid_cell': 'cell_1', 'observations': 4}
            ]
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        # Run pipeline with custom base path
        result = run_sc002_pipeline(metadata_file, output_file)
        
        assert result['total_cells'] == 200
        assert result['insufficient_cells'] == 1
        assert abs(result['ratio'] - 0.005) < 0.001
        assert output_file.exists()

    def test_output_contains_expected_keys(self, tmp_path):
        """Verify output dictionary contains all required keys."""
        metadata_file = tmp_path / "metadata.json"
        output_file = tmp_path / "output.json"
        
        metadata = {
            'total_cells': 100,
            'insufficient_cells': [{'species': 'Test', 'grid_cell': 'c1', 'observations': 3}]
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        result = calculate_sc002_insufficient_data_ratio(metadata_file, output_file)
        
        required_keys = ['total_cells', 'insufficient_cells', 'ratio', 'status']
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Verify types
        assert isinstance(result['total_cells'], int)
        assert isinstance(result['insufficient_cells'], int)
        assert isinstance(result['ratio'], float)
        assert isinstance(result['status'], str)
        assert result['status'] in ['PASS', 'FAIL']
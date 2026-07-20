import pytest
import pandas as pd
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.output_metrics import process_image_file, run_output_pipeline

class TestOutputMetrics:
    
    def test_process_image_file_valid(self):
        """Test that valid metadata produces a record with all required fields."""
        metadata = {
            'brain_region': 'Hippocampus',
            'pathology_status': 'Normal'
        }
        
        record = process_image_file(
            image_path="/data/raw/test.tif",
            metadata=metadata,
            branch_points=10,
            total_length=400.0,
            soma_area=100.0,
            sholl_intersections=5
        )
        
        assert record is not None
        assert record['brain_region'] == 'Hippocampus'
        assert record['pathology_status'] == 'Normal'
        assert record['branch_points'] == 10
        assert record['total_length'] == 400.0
        assert record['soma_area'] == 100.0
        assert record['sholl_intersections'] == 5
        assert 'file_path' in record

    def test_process_image_file_missing_region(self):
        """Test that missing brain_region results in an empty record."""
        metadata = {
            'brain_region': None,
            'pathology_status': 'Normal'
        }
        
        record = process_image_file(
            image_path="/data/raw/test.tif",
            metadata=metadata,
            branch_points=10,
            total_length=400.0,
            soma_area=100.0,
            sholl_intersections=5
        )
        
        assert record == {}

    def test_run_output_pipeline_creates_csv(self, tmp_path):
        """Test that run_output_pipeline writes a CSV with correct columns."""
        data = [
            {
                'file_path': '/data/raw/1.tif',
                'brain_region': 'Hippocampus',
                'pathology_status': 'Normal',
                'branch_points': 10,
                'total_length': 400.0,
                'soma_area': 100.0,
                'sholl_intersections': 5
            },
            {
                'file_path': '/data/raw/2.tif',
                'brain_region': 'Prefrontal Cortex',
                'pathology_status': 'Early AD',
                'branch_points': 15,
                'total_length': 500.0,
                'soma_area': 120.0,
                'sholl_intersections': 8
            }
        ]
        
        output_file = tmp_path / "test_output.csv"
        
        # Mock get_path to use tmp_path
        with patch('code.output_metrics.get_path', return_value=str(output_file)):
            with patch('code.output_metrics.ensure_dirs'):
                result_path = run_output_pipeline(data, output_filename="test_output.csv")
        
        assert result_path == str(output_file)
        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        assert 'branch_points' in df.columns
        assert 'total_length' in df.columns
        assert 'soma_area' in df.columns
        assert 'sholl_intersections' in df.columns
        assert 'brain_region' in df.columns
        assert len(df) == 2

    def test_run_output_pipeline_empty_data(self):
        """Test that empty data returns None and logs warning."""
        with patch('code.output_metrics.logger') as mock_logger:
            result = run_output_pipeline([])
            assert result is None
            mock_logger.warning.assert_called()
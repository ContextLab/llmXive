"""
Integration test for generating graph_metrics.csv from processed calibration data.
"""
import os
import csv
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from generate_graph_metrics_csv import load_processed_calibration, compute_device_metrics

class TestGraphMetricsCSVGeneration:
    @pytest.fixture
    def sample_raw_calibration(self, tmp_path):
        """Create a temporary raw_calibration.csv file with valid test data."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        file_path = data_dir / "raw_calibration.csv"

        # Sample data mimicking T017 output
        # coupling_map is stored as a string representation of a list of tuples
        sample_data = [
            {
                'device_id': 'test_device_1',
                'coupling_map': '[[0, 1], [1, 2], [2, 3]]', # Line graph 0-1-2-3
                't1': 100.5,
                't2': 80.2,
                'gate_error': 0.001,
                'readout_error': 0.02
            },
            {
                'device_id': 'test_device_2',
                'coupling_map': '[[0, 1], [1, 2], [0, 2]]', # Triangle (0,1,2)
                't1': 150.0,
                't2': 120.0,
                'gate_error': 0.0005,
                'readout_error': 0.015
            }
        ]

        df = pd.DataFrame(sample_data)
        df.to_csv(file_path, index=False)
        return file_path

    def test_load_processed_calibration(self, sample_raw_calibration):
        """Test that load_processed_calibration reads the CSV correctly."""
        df = load_processed_calibration(str(sample_raw_calibration))
        
        assert len(df) == 2
        assert 'device_id' in df.columns
        assert 'coupling_map' in df.columns
        assert df.iloc[0]['device_id'] == 'test_device_1'

    def test_compute_device_metrics_line_graph(self, sample_raw_calibration):
        """Test metric computation for a line graph (test_device_1)."""
        df = load_processed_calibration(str(sample_raw_calibration))
        metrics = compute_device_metrics(df)

        device_1_metrics = [m for m in metrics if m['device_id'] == 'test_device_1']
        
        # Check that we got some metrics
        assert len(device_1_metrics) > 0

        # Check for specific expected metrics
        metric_names = [m['metric_name'] for m in device_1_metrics]
        
        # A line graph of 4 nodes has a diameter of 3
        assert any('diameter' in name for name in metric_names)
        
        # Clustering coefficient for a line graph (no triangles) should be 0
        clustering_metrics = [m for m in device_1_metrics if 'clustering' in m['metric_name']]
        for m in clustering_metrics:
            assert m['value'] == 0.0 or m['value'] == 0

    def test_compute_device_metrics_triangle_graph(self, sample_raw_calibration):
        """Test metric computation for a triangle graph (test_device_2)."""
        df = load_processed_calibration(str(sample_raw_calibration))
        metrics = compute_device_metrics(df)

        device_2_metrics = [m for m in metrics if m['device_id'] == 'test_device_2']
        
        # Check that we got some metrics
        assert len(device_2_metrics) > 0

        # A triangle has a diameter of 1
        diameter_metric = next((m for m in device_2_metrics if 'diameter' in m['metric_name']), None)
        assert diameter_metric is not None
        assert diameter_metric['value'] == 1.0

        # Clustering coefficient for a triangle should be 1.0
        clustering_metrics = [m for m in device_2_metrics if 'clustering' in m['metric_name']]
        for m in clustering_metrics:
            # Depending on implementation, might be global or local average
            # For a complete graph, it should be 1.0
            assert m['value'] == 1.0 or m['value'] == 1

    def test_output_structure(self, sample_raw_calibration):
        """Test that the output structure matches requirements: device_id, metric_name, value, is_finite."""
        df = load_processed_calibration(str(sample_raw_calibration))
        metrics = compute_device_metrics(df)

        if not metrics:
            pytest.skip("No metrics computed, skipping structure check")

        required_keys = {'device_id', 'metric_name', 'value', 'is_finite'}
        for m in metrics:
            assert required_keys.issubset(m.keys()), f"Missing keys in metric: {m.keys()}"
            assert isinstance(m['device_id'], str)
            assert isinstance(m['metric_name'], str)
            assert isinstance(m['is_finite'], bool)
            # Value can be float or None
            assert m['value'] is None or isinstance(m['value'], (int, float))

    def test_finite_flag_logic(self, sample_raw_calibration):
        """Test that is_finite is True for valid numbers and False for NaN/Inf."""
        # This is implicitly tested by the compute logic, but we can verify the output
        df = load_processed_calibration(str(sample_raw_calibration))
        metrics = compute_device_metrics(df)

        for m in metrics:
            if m['value'] is not None:
                assert m['is_finite'] == (m['value'] == m['value']) # NaN check
                if m['value'] is not None:
                    import math
                    assert m['is_finite'] == (not math.isinf(m['value']))
            else:
                assert m['is_finite'] == False
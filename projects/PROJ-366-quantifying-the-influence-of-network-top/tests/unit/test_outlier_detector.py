import json
import os
import pickle
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
from analysis.outlier_detector import (
    load_graph_metrics,
    extract_node_degrees,
    calculate_defect_ratio,
    detect_outliers,
    write_excluded_samples
)
from config import get_config, get_paths

class TestCalculateDefectRatio:
    def test_no_defects(self):
        degrees = [4, 4, 4, 4, 4]
        ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
        assert ratio == 0.0

    def test_all_defects_low(self):
        degrees = [2, 2, 2]
        ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
        assert ratio == 1.0

    def test_all_defects_high(self):
        degrees = [7, 8, 7]
        ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
        assert ratio == 1.0

    def test_mixed(self):
        degrees = [4, 2, 4, 7, 4] # 2 defects out of 5
        ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
        assert ratio == 0.4

    def test_empty_list(self):
        ratio = calculate_defect_ratio([])
        assert ratio == 0.0

class TestDetectOutliers:
    @pytest.fixture
    def mock_metrics_data(self, tmp_path):
        # Create mock graph files
        data = {}
        # Sample A: 100 atoms, all 4-coord (0% defect) -> Not outlier
        deg_a = [4] * 100
        file_a = tmp_path / "sample_A.pkl"
        with open(file_a, 'wb') as f:
            pickle.dump({"node_degrees": deg_a}, f)
        
        # Sample B: 100 atoms, 20 are defects (20% defect) -> Outlier (>15%)
        deg_b = [4] * 80 + [2] * 20
        file_b = tmp_path / "sample_B.pkl"
        with open(file_b, 'wb') as f:
            pickle.dump({"node_degrees": deg_b}, f)

        # Sample C: 100 atoms, 10 are defects (10% defect) -> Not outlier
        deg_c = [4] * 90 + [7] * 10
        file_c = tmp_path / "sample_C.pkl"
        with open(file_c, 'wb') as f:
            pickle.dump({"node_degrees": deg_c}, f)

        return tmp_path

    def test_detects_outliers(self, mock_metrics_data):
        metrics = load_graph_metrics(mock_metrics_data)
        outliers = detect_outliers(metrics, threshold=0.15)
        
        assert "sample_B" in outliers
        assert "sample_A" not in outliers
        assert "sample_C" not in outliers

    def test_threshold_boundary(self, mock_metrics_data):
        # Sample B is exactly 20%. If threshold is 0.20, it should NOT be an outlier (> not >=)
        metrics = load_graph_metrics(mock_metrics_data)
        outliers = detect_outliers(metrics, threshold=0.20)
        assert "sample_B" not in outliers

        # If threshold is 0.19, it SHOULD be an outlier
        outliers = detect_outliers(metrics, threshold=0.19)
        assert "sample_B" in outliers

class TestWriteExcludedSamples:
    def test_writes_correct_json(self, tmp_path):
        outlier_ids = {"sample_B", "sample_D"}
        output_file = tmp_path / "excluded_samples.json"
        
        write_excluded_samples(outlier_ids, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "excluded_samples" in data
        assert set(data["excluded_samples"]) == outlier_ids
        assert data["count"] == 2
        assert "reason" in data

    def test_writes_empty_list(self, tmp_path):
        output_file = tmp_path / "excluded_empty.json"
        write_excluded_samples(set(), output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert data["excluded_samples"] == []
        assert data["count"] == 0
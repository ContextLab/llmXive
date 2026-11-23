"""
Unit tests for T022: Collapse Points Generation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from collapse_points_generator import detect_collapse_point, load_baselines

class TestDetectCollapsePoint:
    def test_collapse_detected(self):
        """Test that collapse is detected when SSS drops and WER spikes."""
        # Create mock data: intensity 0 (clean) -> intensity 5 (collapse)
        data = {
            'model_id': ['m1', 'm1', 'm1', 'm1'],
            'scenario_id': ['s1', 's1', 's1', 's1'],
            'intensity_level': [0, 1, 2, 3],
            'sss_score': [0.9, 0.8, 0.4, 0.3], # Drops below 0.5 * 0.9 = 0.45 at index 2
            'wer_score': [0.05, 0.1, 0.3, 0.6]  # Spikes above 2 * 0.05 = 0.1 at index 2
        }
        df = pd.DataFrame(data)
        
        baseline_sss = 0.9
        baseline_wer = 0.05
        
        result = detect_collapse_point(df, baseline_sss, baseline_wer)
        
        assert result is not None
        assert result['status'] == 'collapsed'
        assert result['collapse_intensity'] == 2
        assert result['sss_at_collapse'] == 0.4
        assert result['wer_at_collapse'] == 0.3

    def test_no_collapse(self):
        """Test that no collapse is detected if thresholds are never met."""
        data = {
            'model_id': ['m1', 'm1', 'm1'],
            'scenario_id': ['s1', 's1', 's1'],
            'intensity_level': [0, 1, 2],
            'sss_score': [0.9, 0.8, 0.7], # Never drops below 0.45
            'wer_score': [0.05, 0.1, 0.15] # Never spikes above 0.1 (2*0.05)
        }
        df = pd.DataFrame(data)
        
        baseline_sss = 0.9
        baseline_wer = 0.05
        
        result = detect_collapse_point(df, baseline_sss, baseline_wer)
        
        assert result is not None
        assert result['status'] == 'no_collapse'
        assert result['collapse_intensity'] == 2 # Max tested

    def test_zero_baseline_sss(self):
        """Test handling of zero baseline SSS."""
        data = {
            'model_id': ['m1'],
            'scenario_id': ['s1'],
            'intensity_level': [0],
            'sss_score': [0.0],
            'wer_score': [0.0]
        }
        df = pd.DataFrame(data)
        
        result = detect_collapse_point(df, 0.0, 0.05)
        
        assert result is None

class TestLoadBaselines:
    def test_load_baselines_success(self, tmp_path):
        """Test loading baseline files."""
        # Create temp files
        sss_data = {"m1": {"s1": 0.9}}
        wer_data = {"m1": {"s1": 0.05}}
        
        sss_file = tmp_path / "baseline_sss.json"
        wer_file = tmp_path / "baseline_wer.json"
        
        with open(sss_file, 'w') as f:
            json.dump(sss_data, f)
        with open(wer_file, 'w') as f:
            json.dump(wer_data, f)
        
        # Mock paths
        import collapse_points_generator as cp_module
        original_paths = cp_module.get_default_paths
        
        def mock_paths():
            p = original_paths()
            p['data_derived'] = tmp_path
            return p
        
        cp_module.get_default_paths = mock_paths
        
        try:
            baselines = load_baselines({})
            assert 'm1' in baselines
            assert baselines['m1']['s1']['baseline_sss'] == 0.9
            assert baselines['m1']['s1']['baseline_wer'] == 0.05
        finally:
            cp_module.get_default_paths = original_paths

    def test_load_baselines_missing(self, tmp_path):
        """Test error when baseline files are missing."""
        import collapse_points_generator as cp_module
        original_paths = cp_module.get_default_paths
        
        def mock_paths():
            p = original_paths()
            p['data_derived'] = tmp_path
            return p
        
        cp_module.get_default_paths = mock_paths
        
        try:
            with pytest.raises(FileNotFoundError):
                load_baselines({})
        finally:
            cp_module.get_default_paths = original_paths

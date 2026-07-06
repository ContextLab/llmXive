"""
Unit tests for the report generation module (T034).

Tests verify:
- Correct framing determination based on metadata
- Report generation with various input scenarios
- Proper handling of missing data
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.report import determine_framing, generate_report, load_metadata
from code.config import Config


class TestDetermineFraming:
    """Tests for the determine_framing function."""
    
    def test_randomized_string_true(self):
        """Test that randomized study_design string returns causal."""
        metadata = {"study_design": "randomized", "randomized": False}
        assert determine_framing(metadata) == "causal"
    
    def test_randomized_string_uppercase(self):
        """Test case-insensitive check for randomized string."""
        metadata = {"study_design": "RANDOMIZED", "randomized": False}
        assert determine_framing(metadata) == "causal"
    
    def test_randomized_bool_true(self):
        """Test that randomized boolean true returns causal."""
        metadata = {"study_design": "observational", "randomized": True}
        assert determine_framing(metadata) == "causal"
    
    def test_both_randomized(self):
        """Test when both conditions indicate randomized."""
        metadata = {"study_design": "randomized", "randomized": True}
        assert determine_framing(metadata) == "causal"
    
    def test_neither_randomized(self):
        """Test when neither condition indicates randomized."""
        metadata = {"study_design": "observational", "randomized": False}
        assert determine_framing(metadata) == "associational"
    
    def test_missing_study_design(self):
        """Test when study_design is missing."""
        metadata = {"randomized": False}
        assert determine_framing(metadata) == "associational"
    
    def test_missing_randomized(self):
        """Test when randomized is missing."""
        metadata = {"study_design": "observational"}
        assert determine_framing(metadata) == "associational"
    
    def test_empty_metadata(self):
        """Test with completely empty metadata."""
        metadata = {}
        assert determine_framing(metadata) == "associational"
    
    def test_none_randomized(self):
        """Test when randomized is None."""
        metadata = {"study_design": "observational", "randomized": None}
        assert determine_framing(metadata) == "associational"


class TestGenerateReport:
    """Tests for the generate_report function."""
    
    @pytest.fixture
    def mock_config(self, tmp_path):
        """Create a mock config with necessary directories."""
        config = MagicMock(spec=Config)
        config.PROCESSED_DATA_DIR = tmp_path / "data" / "processed"
        config.METRICS_DIR = tmp_path / "data" / "metrics"
        config.REPORTS_DIR = tmp_path / "reports"
        
        # Create directories
        config.PROCESSED_DATA_DIR.mkdir(parents=True)
        config.METRICS_DIR.mkdir(parents=True)
        config.REPORTS_DIR.mkdir(parents=True)
        
        return config
    
    def test_report_contains_framing(self, mock_config):
        """Test that report includes the correct framing."""
        metadata = {"study_design": "observational", "randomized": False}
        
        report = generate_report(mock_config, metadata=metadata)
        
        assert "ASSOCIATIONAL" in report
        assert "causal" not in report.upper() or "causal claims cannot be made" in report.lower()
    
    def test_report_contains_causal_framing(self, mock_config):
        """Test that report correctly identifies causal design."""
        metadata = {"study_design": "randomized", "randomized": False}
        
        report = generate_report(mock_config, metadata=metadata)
        
        assert "CAUSAL" in report or "causal" in report.lower()
    
    def test_report_contains_power_analysis(self, mock_config):
        """Test that report includes power analysis section."""
        metadata = {"study_design": "observational", "randomized": False, "n_subjects": 10}
        stats_results = pd.DataFrame({
            'metric': ['modularity'],
            'coefficient': [0.5],
            'p_value': [0.03],
            'fdr_p_value': [0.06],
            'vif': [1.2],
            'effect_size': [0.4],
            'min_n_required': [24]
        })
        
        report = generate_report(mock_config, metadata=metadata, stats_results=stats_results)
        
        assert "Power Analysis" in report
        assert "Minimum sample size" in report
        assert "24" in report
    
    def test_report_handles_empty_stats(self, mock_config):
        """Test report generation with empty statistical results."""
        metadata = {"study_design": "observational", "randomized": False}
        stats_results = pd.DataFrame()
        
        report = generate_report(mock_config, metadata=metadata, stats_results=stats_results)
        
        assert "No statistical results were generated" in report
    
    def test_report_contains_network_metrics(self, mock_config):
        """Test that report includes network metrics summary."""
        metadata = {"study_design": "observational", "randomized": False}
        network_metrics = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'modularity': [0.4, 0.5, 0.45],
            'global_efficiency': [0.3, 0.35, 0.32],
            'local_efficiency': [0.35, 0.4, 0.38]
        })
        
        report = generate_report(mock_config, metadata=metadata, network_metrics=network_metrics)
        
        assert "Network Metrics Summary" in report
        assert "modularity" in report
        assert "global_efficiency" in report
    
    def test_report_contains_sensitivity_analysis(self, mock_config):
        """Test that report includes sensitivity analysis section."""
        metadata = {"study_design": "observational", "randomized": False}
        
        report = generate_report(mock_config, metadata=metadata)
        
        assert "Sensitivity Analysis" in report
        assert "2mm" in report
        assert "3mm" in report
    
    def test_report_contains_limitations(self, mock_config):
        """Test that report includes limitations section."""
        metadata = {"study_design": "observational", "randomized": False}
        
        report = generate_report(mock_config, metadata=metadata)
        
        assert "Limitations" in report
        assert "Sample Size" in report
        assert "Observational Design" in report


class TestLoadMetadata:
    """Tests for the load_metadata function."""
    
    def test_load_existing_metadata(self, tmp_path):
        """Test loading metadata from existing file."""
        metadata_dir = tmp_path / "data" / "processed" / "metadata"
        metadata_dir.mkdir(parents=True)
        
        metadata_file = metadata_dir / "study_design.json"
        metadata = {
            "study_design": "randomized",
            "randomized": True,
            "dataset_source": "OpenNeuro",
            "n_subjects": 50
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        config = MagicMock(spec=Config)
        config.PROCESSED_DATA_DIR = tmp_path / "data" / "processed"
        
        loaded = load_metadata(config)
        
        assert loaded["study_design"] == "randomized"
        assert loaded["randomized"] is True
        assert loaded["dataset_source"] == "OpenNeuro"
    
    def test_load_missing_metadata(self, tmp_path):
        """Test loading metadata when file doesn't exist."""
        config = MagicMock(spec=Config)
        config.PROCESSED_DATA_DIR = tmp_path / "data" / "processed"
        
        loaded = load_metadata(config)
        
        assert loaded["study_design"] == "observational"
        assert loaded["randomized"] is False
        assert loaded["dataset_source"] == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
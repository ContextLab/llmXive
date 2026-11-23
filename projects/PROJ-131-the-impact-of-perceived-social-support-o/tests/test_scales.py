"""
Unit tests for scale scoring logic.
Verifies that scoring functions in code/analysis/scales.py match definitions in code/config/scales.yaml.
"""
import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5, apply_scale_scoring


class TestScaleConfig:
    """Tests for loading and validating scale configuration."""

    def test_scale_config_exists(self):
        """Test that the scale configuration file exists."""
        config_path = project_root / "code" / "config" / "scales.yaml"
        assert config_path.exists(), f"Configuration file not found at {config_path}"

    def test_scale_config_valid_yaml(self):
        """Test that the scale configuration is valid YAML."""
        config_path = project_root / "code" / "config" / "scales.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "Configuration must be a dictionary"
        assert 'CES-D' in config or 'CES-D' in config.keys(), "Configuration must contain CES-D"
        assert 'GAD-7' in config or 'GAD-7' in config.keys(), "Configuration must contain GAD-7"
        assert 'PCL-5' in config or 'PCL-5' in config.keys(), "Configuration must contain PCL-5"

    def test_scale_config_structure(self):
        """Test that each scale has required keys."""
        config = load_scale_config(project_root / "code" / "config" / "scales.yaml")
        for scale_name in ['CES-D', 'GAD-7', 'PCL-5']:
            assert scale_name in config, f"Scale {scale_name} missing from config"
            scale_def = config[scale_name]
            assert 'variable' in scale_def, f"Scale {scale_name} missing 'variable' key"
            assert 'type' in scale_def, f"Scale {scale_name} missing 'type' key"
            assert scale_def['type'] in ['aggregate_score', 'raw_items'], \
                f"Scale {scale_name} has invalid type: {scale_def['type']}"


class TestScaleScoringFunctions:
    """Tests for individual scale scoring functions."""

    @pytest.fixture
    def mock_cesd_data(self):
        """Create mock data for CES-D scoring."""
        # CES-D typically has 20 items, scored 0-3
        data = {
            'CESD_1': [1, 2, 0, 3, 1],
            'CESD_2': [0, 1, 2, 1, 0],
            'CESD_3': [2, 0, 1, 2, 3],
            'CESD_4': [1, 1, 0, 0, 2],
            'CESD_5': [0, 2, 1, 1, 1],
            'CESD_6': [3, 1, 2, 0, 1],
            'CESD_7': [1, 0, 3, 2, 0],
            'CESD_8': [2, 3, 0, 1, 2],
            'CESD_9': [0, 1, 1, 3, 1],
            'CESD_10': [1, 2, 2, 0, 0],
            'CESD_11': [3, 0, 1, 1, 2],
            'CESD_12': [0, 1, 3, 2, 1],
            'CESD_13': [2, 2, 0, 0, 3],
            'CESD_14': [1, 0, 2, 1, 0],
            'CESD_15': [0, 3, 1, 2, 1],
            'CESD_16': [2, 1, 0, 3, 2],
            'CESD_17': [1, 2, 3, 0, 1],
            'CESD_18': [0, 0, 1, 2, 3],
            'CESD_19': [3, 1, 2, 1, 0],
            'CESD_20': [1, 3, 0, 0, 2],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_gad7_data(self):
        """Create mock data for GAD-7 scoring."""
        # GAD-7 has 7 items, scored 0-3
        data = {
            'GAD_1': [0, 1, 2, 3, 1],
            'GAD_2': [1, 0, 1, 2, 0],
            'GAD_3': [2, 1, 0, 1, 2],
            'GAD_4': [0, 2, 1, 0, 1],
            'GAD_5': [1, 0, 2, 1, 0],
            'GAD_6': [3, 1, 0, 2, 1],
            'GAD_7': [0, 2, 1, 0, 2],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_pcl5_data(self):
        """Create mock data for PCL-5 scoring."""
        # PCL-5 has 20 items, scored 0-4
        data = {
            'PCL5_1': [0, 1, 2, 3, 1],
            'PCL5_2': [1, 0, 1, 2, 0],
            'PCL5_3': [2, 1, 0, 1, 2],
            'PCL5_4': [0, 2, 1, 0, 1],
            'PCL5_5': [1, 0, 2, 1, 0],
            'PCL5_6': [3, 1, 0, 2, 1],
            'PCL5_7': [0, 2, 1, 0, 2],
            'PCL5_8': [1, 1, 2, 3, 0],
            'PCL5_9': [2, 0, 1, 1, 3],
            'PCL5_10': [0, 3, 2, 0, 1],
            'PCL5_11': [1, 2, 0, 2, 0],
            'PCL5_12': [3, 1, 1, 0, 2],
            'PCL5_13': [0, 0, 3, 1, 1],
            'PCL5_14': [2, 2, 0, 2, 0],
            'PCL5_15': [1, 1, 1, 0, 3],
            'PCL5_16': [0, 3, 2, 1, 1],
            'PCL5_17': [2, 0, 0, 3, 2],
            'PCL5_18': [1, 2, 3, 0, 1],
            'PCL5_19': [0, 1, 1, 2, 0],
            'PCL5_20': [3, 0, 2, 1, 2],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_aggregate_data(self):
        """Create mock data with pre-aggregated scores."""
        return pd.DataFrame({
            'depression': [15, 22, 8, 30, 12],
            'anxiety': [5, 10, 3, 15, 7],
            'ptsd': [20, 35, 10, 50, 25],
        })

    def test_score_cesd_aggregate(self, mock_aggregate_data):
        """Test CES-D scoring with pre-aggregated data."""
        config = {
            'CES-D': {
                'variable': 'depression',
                'type': 'aggregate_score'
            }
        }
        df = mock_aggregate_data.copy()
        result = score_cesd(df, config)
        assert 'depression' in result.columns, "Result should contain depression column"
        # Verify values match input (since it's aggregate)
        pd.testing.assert_series_equal(result['depression'], mock_aggregate_data['depression'])

    def test_score_cesd_raw_items(self, mock_cesd_data):
        """Test CES-D scoring with raw items."""
        config = {
            'CES-D': {
                'variable': 'depression',
                'type': 'raw_items'
            }
        }
        df = mock_cesd_data.copy()
        result = score_cesd(df, config)
        assert 'depression' in result.columns, "Result should contain depression column"
        # Verify all scores are within valid range (0-60 for CES-D)
        assert result['depression'].min() >= 0
        assert result['depression'].max() <= 60

    def test_score_gad7_aggregate(self, mock_aggregate_data):
        """Test GAD-7 scoring with pre-aggregated data."""
        config = {
            'GAD-7': {
                'variable': 'anxiety',
                'type': 'aggregate_score'
            }
        }
        df = mock_aggregate_data.copy()
        result = score_gad7(df, config)
        assert 'anxiety' in result.columns, "Result should contain anxiety column"
        pd.testing.assert_series_equal(result['anxiety'], mock_aggregate_data['anxiety'])

    def test_score_gad7_raw_items(self, mock_gad7_data):
        """Test GAD-7 scoring with raw items."""
        config = {
            'GAD-7': {
                'variable': 'anxiety',
                'type': 'raw_items'
            }
        }
        df = mock_gad7_data.copy()
        result = score_gad7(df, config)
        assert 'anxiety' in result.columns, "Result should contain anxiety column"
        # Verify all scores are within valid range (0-21 for GAD-7)
        assert result['anxiety'].min() >= 0
        assert result['anxiety'].max() <= 21

    def test_score_pcl5_aggregate(self, mock_aggregate_data):
        """Test PCL-5 scoring with pre-aggregated data."""
        config = {
            'PCL-5': {
                'variable': 'ptsd',
                'type': 'aggregate_score'
            }
        }
        df = mock_aggregate_data.copy()
        result = score_pcl5(df, config)
        assert 'ptsd' in result.columns, "Result should contain ptsd column"
        pd.testing.assert_series_equal(result['ptsd'], mock_aggregate_data['ptsd'])

    def test_score_pcl5_raw_items(self, mock_pcl5_data):
        """Test PCL-5 scoring with raw items."""
        config = {
            'PCL-5': {
                'variable': 'ptsd',
                'type': 'raw_items'
            }
        }
        df = mock_pcl5_data.copy()
        result = score_pcl5(df, config)
        assert 'ptsd' in result.columns, "Result should contain ptsd column"
        # Verify all scores are within valid range (0-80 for PCL-5)
        assert result['ptsd'].min() >= 0
        assert result['ptsd'].max() <= 80


class TestApplyScaleScoring:
    """Tests for the main scoring application function."""

    def test_apply_scale_scoring_aggregate(self):
        """Test apply_scale_scoring with aggregate scores."""
        config_path = project_root / "code" / "config" / "scales.yaml"
        config = load_scale_config(config_path)
        
        # Create mock data with aggregate scores
        data = pd.DataFrame({
            'depression': [15, 22, 8, 30, 12],
            'anxiety': [5, 10, 3, 15, 7],
            'ptsd': [20, 35, 10, 50, 25],
        })
        
        result = apply_scale_scoring(data, config)
        assert 'depression' in result.columns
        assert 'anxiety' in result.columns
        assert 'ptsd' in result.columns
        assert len(result) == 5

    def test_apply_scale_scoring_with_missing_scale(self):
        """Test apply_scale_scoring when a scale is not in config."""
        config = {
            'CES-D': {
                'variable': 'depression',
                'type': 'aggregate_score'
            }
            # GAD-7 and PCL-5 missing
        }
        data = pd.DataFrame({
            'depression': [15, 22, 8],
            'anxiety': [5, 10, 3],
            'ptsd': [20, 35, 10],
        })
        
        # Should not raise an error, just score what's available
        result = apply_scale_scoring(data, config)
        assert 'depression' in result.columns
        # anxiety and ptsd should not be added if not in config
        # (unless they were already in the input)
        assert len(result.columns) >= 1

    def test_apply_scale_scoring_handles_missing_values(self):
        """Test that scoring handles missing values appropriately."""
        config = {
            'CES-D': {
                'variable': 'depression',
                'type': 'aggregate_score'
            }
        }
        data = pd.DataFrame({
            'depression': [15, np.nan, 8, 30, np.nan],
        })
        
        result = apply_scale_scoring(data, config)
        assert 'depression' in result.columns
        # NaN values should remain NaN
        assert pd.isna(result['depression'].iloc[1])
        assert pd.isna(result['depression'].iloc[4])


class TestScaleScoringIntegration:
    """Integration tests for the full scoring pipeline."""

    def test_full_scoring_workflow(self):
        """Test the complete scoring workflow from config to output."""
        config_path = project_root / "code" / "config" / "scales.yaml"
        
        # Verify config exists and is valid
        assert config_path.exists()
        config = load_scale_config(config_path)
        
        # Create comprehensive mock data
        data = {
            # CES-D items (20)
            'CESD_1': [1, 2, 0, 3, 1],
            'CESD_2': [0, 1, 2, 1, 0],
            'CESD_3': [2, 0, 1, 2, 3],
            'CESD_4': [1, 1, 0, 0, 2],
            'CESD_5': [0, 2, 1, 1, 1],
            'CESD_6': [3, 1, 2, 0, 1],
            'CESD_7': [1, 0, 3, 2, 0],
            'CESD_8': [2, 3, 0, 1, 2],
            'CESD_9': [0, 1, 1, 3, 1],
            'CESD_10': [1, 2, 2, 0, 0],
            'CESD_11': [3, 0, 1, 1, 2],
            'CESD_12': [0, 1, 3, 2, 1],
            'CESD_13': [2, 2, 0, 0, 3],
            'CESD_14': [1, 0, 2, 1, 0],
            'CESD_15': [0, 3, 1, 2, 1],
            'CESD_16': [2, 1, 0, 3, 2],
            'CESD_17': [1, 2, 3, 0, 1],
            'CESD_18': [0, 0, 1, 2, 3],
            'CESD_19': [3, 1, 2, 1, 0],
            'CESD_20': [1, 3, 0, 0, 2],
            # GAD-7 items (7)
            'GAD_1': [0, 1, 2, 3, 1],
            'GAD_2': [1, 0, 1, 2, 0],
            'GAD_3': [2, 1, 0, 1, 2],
            'GAD_4': [0, 2, 1, 0, 1],
            'GAD_5': [1, 0, 2, 1, 0],
            'GAD_6': [3, 1, 0, 2, 1],
            'GAD_7': [0, 2, 1, 0, 2],
            # PCL-5 items (20)
            'PCL5_1': [0, 1, 2, 3, 1],
            'PCL5_2': [1, 0, 1, 2, 0],
            'PCL5_3': [2, 1, 0, 1, 2],
            'PCL5_4': [0, 2, 1, 0, 1],
            'PCL5_5': [1, 0, 2, 1, 0],
            'PCL5_6': [3, 1, 0, 2, 1],
            'PCL5_7': [0, 2, 1, 0, 2],
            'PCL5_8': [1, 1, 2, 3, 0],
            'PCL5_9': [2, 0, 1, 1, 3],
            'PCL5_10': [0, 3, 2, 0, 1],
            'PCL5_11': [1, 2, 0, 2, 0],
            'PCL5_12': [3, 1, 1, 0, 2],
            'PCL5_13': [0, 0, 3, 1, 1],
            'PCL5_14': [2, 2, 0, 2, 0],
            'PCL5_15': [1, 1, 1, 0, 3],
            'PCL5_16': [0, 3, 2, 1, 1],
            'PCL5_17': [2, 0, 0, 3, 2],
            'PCL5_18': [1, 2, 3, 0, 1],
            'PCL5_19': [0, 1, 1, 2, 0],
            'PCL5_20': [3, 0, 2, 1, 2],
        }
        df = pd.DataFrame(data)
        
        # Apply scoring
        result = apply_scale_scoring(df, config)
        
        # Verify all three scales were scored
        assert 'depression' in result.columns
        assert 'anxiety' in result.columns
        assert 'ptsd' in result.columns
        
        # Verify no negative scores
        assert result['depression'].min() >= 0
        assert result['anxiety'].min() >= 0
        assert result['ptsd'].min() >= 0
"""
Tests for the preprocessing module (T016).

These tests verify:
1. Salience assignment logic.
2. Mapping logic from story IDs to blend shapes.
3. Filtering of invalid data.
4. Log file generation (vr_mapping.log).
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import yaml

# Add code to path if needed, though imports usually handle this
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocess import (
    assign_salience_level,
    map_to_blend_shapes,
    process_salience_mapping,
    load_blend_shape_config,
    run_preprocessing_pipeline
)
from utils.logging_utils import get_vr_mapping_log_path

class TestSalienceAssignment:
    """Tests for assign_salience_level function."""

    def test_high_salience_assignment(self):
        """Test that a known high salience story returns 'high'."""
        config = {
            "mappings": {
                "story_001": {
                    "salience_level": "high",
                    "blend_shape_params": {"jawOpen": 0.8}
                }
            }
        }
        salience, params = assign_salience_level("story_001", config)
        assert salience == "high"
        assert params["jawOpen"] == 0.8

    def test_low_salience_assignment(self):
        """Test that a known low salience story returns 'low'."""
        config = {
            "mappings": {
                "story_006": {
                    "salience_level": "low",
                    "blend_shape_params": {"jawOpen": 0.1}
                }
            }
        }
        salience, params = assign_salience_level("story_006", config)
        assert salience == "low"
        assert params["jawOpen"] == 0.1

    def test_missing_story_id_fallback(self):
        """Test fallback behavior for missing story IDs."""
        config = {"mappings": {}}
        salience, params = assign_salience_level("unknown_story", config)
        # Should assign based on hash or default
        assert salience in ["low", "high"]
        assert isinstance(params, dict)

    def test_invalid_salience_level_defaults(self):
        """Test that invalid salience levels default to 'low'."""
        config = {
            "mappings": {
                "story_bad": {
                    "salience_level": "invalid",
                    "blend_shape_params": {}
                }
            }
        }
        salience, params = assign_salience_level("story_bad", config)
        assert salience == "low"

class TestMappingLogic:
    """Tests for map_to_blend_shapes function."""

    def test_mapping_dataframe(self):
        """Test that mapping adds correct columns to dataframe."""
        df = pd.DataFrame({
            "story_id": ["story_001", "story_006"],
            "other_col": [1, 2]
        })
        config = {
            "mappings": {
                "story_001": {"salience_level": "high", "blend_shape_params": {"a": 1}},
                "story_006": {"salience_level": "low", "blend_shape_params": {"a": 2}}
            }
        }
        
        result = map_to_blend_shapes(df, config)
        
        assert "salience_level" in result.columns
        assert "blend_shape_params" in result.columns
        assert result.loc[0, "salience_level"] == "high"
        assert result.loc[1, "salience_level"] == "low"

    def test_missing_story_in_config(self):
        """Test handling of story IDs not in config."""
        df = pd.DataFrame({
            "story_id": ["story_001", "story_missing"],
            "other_col": [1, 2]
        })
        config = {
            "mappings": {
                "story_001": {"salience_level": "high", "blend_shape_params": {"a": 1}}
            }
        }
        
        result = map_to_blend_shapes(df, config)
        
        assert result.loc[0, "salience_level"] == "high"
        assert pd.isna(result.loc[1, "salience_level"])

class TestFiltering:
    """Tests for data filtering and handling."""

    def test_missing_story_id_handling(self):
        """Test that rows with missing story IDs are handled gracefully."""
        df = pd.DataFrame({
            "story_id": [None, "story_001"],
            "other_col": [1, 2]
        })
        config = {
            "mappings": {
                "story_001": {"salience_level": "high", "blend_shape_params": {}}
            }
        }
        
        result = map_to_blend_shapes(df, config)
        
        assert pd.isna(result.loc[0, "salience_level"])
        assert result.loc[1, "salience_level"] == "high"

class TestLogGeneration:
    """Tests for VR mapping log generation."""

    def test_process_salience_mapping_creates_entries(self):
        """Test that process_salience_mapping creates valid log entries."""
        df = pd.DataFrame({
            "story_id": ["story_001", "story_006"],
            "salience_level": ["high", "low"],
            "blend_shape_params": ['{"a": 1}', '{"b": 2}']
        })
        
        entries = process_salience_mapping(df)
        
        assert len(entries) == 2
        assert entries[0]["story_id"] == "story_001"
        assert entries[0]["salience_level"] == "high"
        assert entries[1]["story_id"] == "story_006"
        assert entries[1]["salience_level"] == "low"

    def test_log_file_written(self):
        """Test that the VR mapping log file is actually written to disk."""
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data_dir = tmp_path / "data"
            data_dir.mkdir()
            logs_dir = data_dir / "logs"
            logs_dir.mkdir()
            processed_dir = data_dir / "processed"
            processed_dir.mkdir()
            
            # Mock the paths
            with patch('data.preprocess.MERGED_DATA_PATH', processed_dir / "merged_dataset.csv"):
                with patch('data.preprocess.CONFIG_PATH', tmp_path / "config.yaml"):
                    with patch('data.preprocess.PREPROCESSED_DATA_PATH', processed_dir / "preprocessed_dataset.csv"):
                        with patch('utils.logging_utils.get_vr_mapping_log_path', return_value=logs_dir / "vr_mapping.log"):
                            with patch('utils.logging_utils.get_logger'):
                                # Create mock merged data
                                mock_df = pd.DataFrame({
                                    "story_id": ["story_001"],
                                    "val": [1]
                                })
                                mock_df.to_csv(processed_dir / "merged_dataset.csv", index=False)
                                
                                # Create mock config
                                config = {
                                    "mappings": {
                                        "story_001": {
                                            "salience_level": "high",
                                            "blend_shape_params": {"jawOpen": 0.5}
                                        }
                                    }
                                }
                                with open(tmp_path / "config.yaml", 'w') as f:
                                    yaml.dump(config, f)
                                
                                # Run the pipeline
                                from data.preprocess import run_preprocessing_pipeline
                                run_preprocessing_pipeline()
                                
                                # Verify log file exists
                                log_path = logs_dir / "vr_mapping.log"
                                assert log_path.exists(), "VR mapping log file was not created."
                                
                                # Verify content
                                with open(log_path, 'r') as f:
                                    content = f.read()
                                    assert "story_001" in content
                                    assert "high" in content

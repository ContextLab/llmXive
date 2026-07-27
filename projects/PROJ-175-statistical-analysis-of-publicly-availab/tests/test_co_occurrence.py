"""
Tests for Task T015: Co-occurrence Matrix Construction
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data.co_occurrence import (
    load_epsilon_config,
    load_ingredient_pairs,
    build_cooccurrence_matrix,
    save_output
)


class TestLoadEpsilonConfig:
    """Tests for loading epsilon configuration."""

    def test_load_epsilon_existing_config(self, tmp_path):
        """Test loading epsilon from existing config file."""
        # Create temporary config
        config_dir = tmp_path / "data"
        config_dir.mkdir()
        config_path = config_dir / "zero_handling_log.json"
        
        config_data = {"epsilon": 0.001, "zero_pair_count": 100}
        with open(config_path, "w") as f:
            json.dump(config_data, f)
        
        # Temporarily modify the function to use our temp path
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            epsilon = load_epsilon_config()
            assert epsilon == 0.001
        finally:
            co_module.PROJECT_ROOT = original_path

    def test_missing_config_file(self, tmp_path):
        """Test that missing config file raises FileNotFoundError."""
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            with pytest.raises(FileNotFoundError):
                load_epsilon_config()
        finally:
            co_module.PROJECT_ROOT = original_path

    def test_missing_epsilon_key(self, tmp_path):
        """Test that missing epsilon key raises ValueError."""
        config_dir = tmp_path / "data"
        config_dir.mkdir()
        config_path = config_dir / "zero_handling_log.json"
        
        with open(config_path, "w") as f:
            json.dump({"zero_pair_count": 100}, f)
        
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            with pytest.raises(ValueError):
                load_epsilon_config()
        finally:
            co_module.PROJECT_ROOT = original_path


class TestLoadIngredientPairs:
    """Tests for loading ingredient pairs."""

    def test_load_from_parquet(self, tmp_path):
        """Test loading ingredient pairs from parquet file."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create test data
        data = {
            "ingredient_a": ["salt", "pepper", "sugar"],
            "ingredient_b": ["pepper", "sugar", "salt"],
            "co_occurrence_count": [10, 20, 15]
        }
        df = pd.DataFrame(data)
        parquet_path = processed_dir / "ingredient_pairs.parquet"
        df.to_parquet(parquet_path)
        
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            loaded_df = load_ingredient_pairs()
            assert len(loaded_df) == 3
            assert "log_co_occurrence" not in loaded_df.columns  # Should be raw data
        finally:
            co_module.PROJECT_ROOT = original_path

    def test_load_from_csv(self, tmp_path):
        """Test loading ingredient pairs from CSV file."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        data = {
            "ingredient_a": ["salt", "pepper"],
            "ingredient_b": ["pepper", "sugar"],
            "co_occurrence_count": [10, 20]
        }
        df = pd.DataFrame(data)
        csv_path = processed_dir / "ingredient_pairs.csv"
        df.to_csv(csv_path, index=False)
        
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            loaded_df = load_ingredient_pairs()
            assert len(loaded_df) == 2
        finally:
            co_module.PROJECT_ROOT = original_path

    def test_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            with pytest.raises(FileNotFoundError):
                load_ingredient_pairs()
        finally:
            co_module.PROJECT_ROOT = original_path

    def test_missing_required_columns(self, tmp_path):
        """Test that missing required columns raises ValueError."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        data = {
            "ingredient_a": ["salt", "pepper"],
            "wrong_column": [10, 20]
        }
        df = pd.DataFrame(data)
        parquet_path = processed_dir / "ingredient_pairs.parquet"
        df.to_parquet(parquet_path)
        
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            with pytest.raises(ValueError):
                load_ingredient_pairs()
        finally:
            co_module.PROJECT_ROOT = original_path


class TestBuildCooccurrenceMatrix:
    """Tests for building the co-occurrence matrix."""

    def test_basic_matrix_building(self):
        """Test basic co-occurrence matrix building."""
        data = {
            "ingredient_a": ["salt", "pepper", "sugar", "salt"],
            "ingredient_b": ["pepper", "sugar", "salt", "pepper"],
            "co_occurrence_count": [10, 20, 15, 5]
        }
        df = pd.DataFrame(data)
        
        epsilon = 0.001
        result = build_cooccurrence_matrix(df, epsilon)
        
        assert "ingredient_a" in result.columns
        assert "ingredient_b" in result.columns
        assert "raw_co_occurrence" in result.columns
        assert "log_co_occurrence" in result.columns
        
        # Check log transform was applied
        assert all(result["log_co_occurrence"] > 0)
        assert all(result["log_co_occurrence"] == np.log(result["raw_co_occurrence"] + epsilon))

    def test_symmetric_pairs_merged(self):
        """Test that symmetric pairs are properly merged."""
        data = {
            "ingredient_a": ["salt", "pepper"],
            "ingredient_b": ["pepper", "salt"],
            "co_occurrence_count": [10, 20]
        }
        df = pd.DataFrame(data)
        
        result = build_cooccurrence_matrix(df, 0.001)
        
        # Should have only one row for the pair (salt, pepper)
        assert len(result) == 1
        # Counts should be summed
        assert result["raw_co_occurrence"].iloc[0] == 30

    def test_zero_counts_skipped(self):
        """Test that zero counts are skipped."""
        data = {
            "ingredient_a": ["salt", "pepper"],
            "ingredient_b": ["pepper", "sugar"],
            "co_occurrence_count": [10, 0]
        }
        df = pd.DataFrame(data)
        
        result = build_cooccurrence_matrix(df, 0.001)
        
        # Should have only one row (zero count skipped)
        assert len(result) == 1
        assert result["raw_co_occurrence"].iloc[0] == 10

    def test_log_transform_correctness(self):
        """Test that log transform is correctly applied."""
        data = {
            "ingredient_a": ["salt"],
            "ingredient_b": ["pepper"],
            "co_occurrence_count": [100]
        }
        df = pd.DataFrame(data)
        
        epsilon = 0.001
        result = build_cooccurrence_matrix(df, epsilon)
        
        expected_log = np.log(100 + epsilon)
        assert abs(result["log_co_occurrence"].iloc[0] - expected_log) < 1e-6


class TestSaveOutput:
    """Tests for saving the output."""

    def test_save_parquet_creates_file(self, tmp_path):
        """Test that save_output creates a parquet file."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        data = {
            "ingredient_a": ["salt"],
            "ingredient_b": ["pepper"],
            "raw_co_occurrence": [10],
            "log_co_occurrence": [2.302]
        }
        df = pd.DataFrame(data)
        
        output_path = processed_dir / "co_occurrence_matrix.parquet"
        save_output(df, output_path)
        
        assert output_path.exists()
        
        # Verify metadata file was created
        metadata_path = processed_dir / "co_occurrence_matrix_metadata.json"
        assert metadata_path.exists()
        
        # Verify metadata content
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        assert metadata["num_pairs"] == 1
        assert "log_co_occurrence_stats" in metadata

    def test_save_creates_directory(self, tmp_path):
        """Test that save_output creates parent directories if needed."""
        deep_dir = tmp_path / "data" / "processed" / "subdir"
        
        data = {
            "ingredient_a": ["salt"],
            "ingredient_b": ["pepper"],
            "raw_co_occurrence": [10],
            "log_co_occurrence": [2.302]
        }
        df = pd.DataFrame(data)
        
        output_path = deep_dir / "co_occurrence_matrix.parquet"
        save_output(df, output_path)
        
        assert output_path.exists()


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_t015_workflow(self, tmp_path):
        """Test the complete T015 workflow."""
        # Setup directory structure
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create T049 config
        config_data = {"epsilon": 0.001, "zero_pair_count": 5}
        with open(data_dir / "zero_handling_log.json", "w") as f:
            json.dump(config_data, f)
        
        # Create ingredient pairs
        pairs_data = {
            "ingredient_a": ["salt", "pepper", "sugar", "salt", "butter"],
            "ingredient_b": ["pepper", "sugar", "salt", "pepper", "salt"],
            "co_occurrence_count": [10, 20, 15, 5, 8]
        }
        pairs_df = pd.DataFrame(pairs_data)
        pairs_df.to_parquet(processed_dir / "ingredient_pairs.parquet")
        
        # Run T015 functions
        import code.data.co_occurrence as co_module
        original_path = co_module.PROJECT_ROOT
        co_module.PROJECT_ROOT = tmp_path
        
        try:
            epsilon = load_epsilon_config()
            assert epsilon == 0.001
            
            pairs = load_ingredient_pairs()
            assert len(pairs) == 5
            
            matrix = build_cooccurrence_matrix(pairs, epsilon)
            assert len(matrix) > 0
            assert "log_co_occurrence" in matrix.columns
            
            output_path = processed_dir / "co_occurrence_matrix.parquet"
            save_output(matrix, output_path)
            
            assert output_path.exists()
            
            # Verify output can be read back
            result_df = pd.read_parquet(output_path)
            assert len(result_df) == len(matrix)
            assert all(result_df.columns == matrix.columns)
        finally:
            co_module.PROJECT_ROOT = original_path

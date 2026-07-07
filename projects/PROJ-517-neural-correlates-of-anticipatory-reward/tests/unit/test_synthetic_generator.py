"""
Unit tests for the synthetic data generator.
"""
import os
import pandas as pd
import pytest
from pathlib import Path

# Import the generator function
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from code.synthetic_generator import generate_synthetic_dataset


class TestSyntheticGenerator:
    def test_output_file_exists(self, tmp_path):
        """Test that the generator creates the output file."""
        output_file = tmp_path / "synthetic_test.csv"
        schema_file = tmp_path / "schema.yaml"
        
        # Create a minimal valid schema for the test
        schema_content = """
        type: object
        properties:
          trial_id:
            type: string
          neuron_id:
            type: string
          spike_timestamps:
            type: array
          reward_magnitude:
            type: number
          cue_timestamps:
            type: array
          spike_sorting_metadata:
            type: object
        """
        schema_file.write_text(schema_content)
        
        generate_synthetic_dataset(
            seed=42,
            n_neurons=2,
            n_trials_per_neuron=10,
            output_path=str(output_file),
            schema_path=str(schema_file)
        )
        
        assert output_file.exists()
    
    def test_dataframe_structure(self, tmp_path):
        """Test that the output DataFrame has the expected columns."""
        output_file = tmp_path / "synthetic_test.csv"
        schema_file = tmp_path / "schema.yaml"
        
        schema_content = """
        type: object
        properties:
          trial_id:
            type: string
          neuron_id:
            type: string
          spike_timestamps:
            type: array
          reward_magnitude:
            type: number
          cue_timestamps:
            type: array
          spike_sorting_metadata:
            type: object
        """
        schema_file.write_text(schema_content)
        
        generate_synthetic_dataset(
            seed=42,
            n_neurons=2,
            n_trials_per_neuron=10,
            output_path=str(output_file),
            schema_path=str(schema_file)
        )
        
        df = pd.read_csv(output_file)
        
        expected_columns = [
            "trial_id", "neuron_id", "spike_timestamps", 
            "reward_magnitude", "cue_timestamps", "spike_sorting_metadata"
        ]
        
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
    
    def test_reward_levels_distribution(self, tmp_path):
        """Test that data is generated for multiple reward levels."""
        output_file = tmp_path / "synthetic_test.csv"
        schema_file = tmp_path / "schema.yaml"
        
        schema_content = """
        type: object
        properties:
          trial_id:
            type: string
          neuron_id:
            type: string
          spike_timestamps:
            type: array
          reward_magnitude:
            type: number
          cue_timestamps:
            type: array
          spike_sorting_metadata:
            type: object
        """
        schema_file.write_text(schema_content)
        
        generate_synthetic_dataset(
            seed=42,
            n_neurons=2,
            n_trials_per_neuron=30,
            output_path=str(output_file),
            schema_path=str(schema_file)
        )
        
        df = pd.read_csv(output_file)
        
        # Check that we have multiple distinct reward magnitudes
        unique_rewards = df["reward_magnitude"].unique()
        assert len(unique_rewards) >= 2, "Expected at least 2 distinct reward levels"
    
    def test_trial_id_uniqueness(self, tmp_path):
        """Test that trial IDs are unique."""
        output_file = tmp_path / "synthetic_test.csv"
        schema_file = tmp_path / "schema.yaml"
        
        schema_content = """
        type: object
        properties:
          trial_id:
            type: string
          neuron_id:
            type: string
          spike_timestamps:
            type: array
          reward_magnitude:
            type: number
          cue_timestamps:
            type: array
          spike_sorting_metadata:
            type: object
        """
        schema_file.write_text(schema_content)
        
        generate_synthetic_dataset(
            seed=42,
            n_neurons=2,
            n_trials_per_neuron=10,
            output_path=str(output_file),
            schema_path=str(schema_file)
        )
        
        df = pd.read_csv(output_file)
        
        assert df["trial_id"].is_unique, "Trial IDs must be unique"
    
    def test_spike_sorting_metadata_validity(self, tmp_path):
        """Test that spike sorting metadata contains expected fields."""
        output_file = tmp_path / "synthetic_test.csv"
        schema_file = tmp_path / "schema.yaml"
        
        schema_content = """
        type: object
        properties:
          trial_id:
            type: string
          neuron_id:
            type: string
          spike_timestamps:
            type: array
          reward_magnitude:
            type: number
          cue_timestamps:
            type: array
          spike_sorting_metadata:
            type: object
        """
        schema_file.write_text(schema_content)
        
        generate_synthetic_dataset(
            seed=42,
            n_neurons=2,
            n_trials_per_neuron=10,
            output_path=str(output_file),
            schema_path=str(schema_file)
        )
        
        df = pd.read_csv(output_file)
        
        # Check first row's metadata
        metadata_str = df.iloc[0]["spike_sorting_metadata"]
        # It should be a string representation of a dict or JSON
        assert isinstance(metadata_str, str)
        assert "snr" in metadata_str
        assert "isolation_distance" in metadata_str
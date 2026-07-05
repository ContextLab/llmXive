"""
Unit tests for visualization module (T033, T034).
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Mock config for testing if necessary, or rely on real config if directories exist
# We will use a temporary directory for output to avoid polluting the project
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from viz.plots import generate_interaction_plot, generate_coefficient_table_from_df


@pytest.fixture
def sample_interaction_data():
    """Create a mock DataFrame for interaction plot testing."""
    data = {
        'prime_valence': ['Positive', 'Positive', 'Negative', 'Negative'],
        'mean_response_time': [500, 520, 600, 650],
        'stimulus_ambiguity_group': ['Low', 'High', 'Low', 'High']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_table_data():
    """Create a mock DataFrame for table generation testing."""
    data = {
        'Parameter': ['Intercept', 'prime_valence[T.Negative]', 'stimulus_ambiguity_group[T.High]', 'prime_valence[T.Negative]:stimulus_ambiguity_group[T.High]'],
        'Coefficient': [500.0, 100.0, 20.0, 15.0],
        'Std. Error': [10.0, 15.0, 5.0, 8.0],
        'P>|z|': [0.001, 0.002, 0.05, 0.08],
        '95% CI Low': [480.0, 70.0, 10.0, -5.0],
        '95% CI High': [520.0, 130.0, 30.0, 35.0]
    }
    return pd.DataFrame(data)


def test_generate_interaction_plot(tmp_path, sample_interaction_data):
    """Test T033: Interaction plot generation."""
    output_file = tmp_path / "test_interaction.png"
    
    # Run the function
    result_path = generate_interaction_plot(
        df=sample_interaction_data,
        output_path=output_file,
        title="Test Interaction Plot"
    )
    
    # Assertions
    assert result_path.exists(), f"Output file {result_path} was not created."
    assert result_path.suffix == ".png", "Output file is not a PNG."
    assert result_path.stat().st_size > 0, "Output file is empty."


def test_generate_coefficient_table_from_df(tmp_path, sample_table_data):
    """Test T034: Coefficient table generation from DataFrame."""
    output_file = tmp_path / "test_table.png"
    
    # Run the function
    result_path = generate_coefficient_table_from_df(
        df=sample_table_data,
        output_path=output_file,
        title="Test Coefficient Table"
    )
    
    # Assertions
    assert result_path.exists(), f"Output file {result_path} was not created."
    assert result_path.suffix == ".png", "Output file is not a PNG."
    assert result_path.stat().st_size > 0, "Output file is empty."


def test_empty_dataframe_interaction_plot(tmp_path):
    """Test that empty DataFrame raises ValueError."""
    empty_df = pd.DataFrame(columns=['prime_valence', 'mean_response_time', 'stimulus_ambiguity_group'])
    
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        generate_interaction_plot(df=empty_df, output_path=tmp_path / "fail.png")
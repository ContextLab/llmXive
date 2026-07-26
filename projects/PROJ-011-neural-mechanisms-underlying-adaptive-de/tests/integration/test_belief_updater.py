"""
Integration tests for the belief updater model.

These tests verify that the hierarchical Bayesian model can:
1. Load and prepare data correctly
2. Build the model without errors
3. Run sampling and produce valid results
4. Save outputs in the expected format
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import set_config, reset_config, set_seed
from utils.io import save_csv, save_json, ensure_dir
from modeling.belief_updater import (
    load_behavioral_data,
    prepare_model_data,
    build_hierarchical_model,
    extract_posterior_samples,
    save_model_results
)
from modeling.synthetic_data_generator import generate_synthetic_dataset


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_behavioral_data(temp_data_dir):
    """Generate sample behavioral data for testing."""
    # Generate synthetic dataset
    df = generate_synthetic_dataset(
        n_participants=10,
        n_trials_per_participant=50,
        seed=42
    )

    # Save to temp directory
    data_path = temp_data_dir / "processed"
    ensure_dir(data_path)
    output_file = data_path / "behavioral.csv"
    save_csv(output_file, df)

    return df, output_file


@pytest.fixture
def test_config(temp_data_dir):
    """Create a test configuration."""
    config = {
        "paths": {
            "processed_behavioral": str(temp_data_dir / "processed" / "behavioral.csv"),
            "model_output": str(temp_data_dir / "models")
        },
        "modeling": {
            "n_chains": 2,
            "draws": 100,
            "tune": 50,
            "target_accept": 0.9,
            "seed": 42
        }
    }
    set_config(config)
    return config


def test_load_behavioral_data(sample_behavioral_data, test_config, temp_data_dir):
    """Test loading of behavioral data."""
    df, _ = sample_behavioral_data

    # Update config with actual path
    test_config["paths"]["processed_behavioral"] = str(temp_data_dir / "processed" / "behavioral.csv")

    loaded_df = load_behavioral_data(test_config)

    assert len(loaded_df) == len(df)
    assert set(loaded_df.columns) == set(df.columns)
    assert "participant_id" in loaded_df.columns
    assert "choice" in loaded_df.columns
    assert "feedback" in loaded_df.columns
    assert "discrepancy" in loaded_df.columns


def test_prepare_model_data(sample_behavioral_data):
    """Test data preparation for the model."""
    df, _ = sample_behavioral_data

    data = prepare_model_data(df)

    assert "n_participants" in data
    assert "n_trials" in data
    assert "participant_idx" in data
    assert "choices" in data
    assert "feedback" in data
    assert "discrepancy" in data

    assert data["n_participants"] == len(df["participant_id"].unique())
    assert data["n_trials"] == len(df)
    assert len(data["participant_idx"]) == data["n_trials"]
    assert len(data["choices"]) == data["n_trials"]


def test_build_hierarchical_model(sample_behavioral_data):
    """Test that the hierarchical model builds correctly."""
    df, _ = sample_behavioral_data
    data = prepare_model_data(df)

    model = build_hierarchical_model(data)

    # Check that key variables exist in the model
    assert "alpha_mu" in model.named_vars
    assert "alpha_sigma" in model.named_vars
    assert "alpha_raw" in model.named_vars
    assert "beta_mu" in model.named_vars
    assert "beta_sigma" in model.named_vars
    assert "beta_raw" in model.named_vars
    assert "obs" in model.named_vars


def test_extract_posterior_samples(test_config):
    """Test extraction of posterior samples from a mock trace."""
    # Create mock trace data
    n_participants = 10
    n_chains = 2
    draws = 50

    mock_trace = MagicMock()
    mock_trace.__getitem__ = lambda self, key: {
        "alpha_transformed": np.random.rand(n_chains, draws, n_participants),
        "beta": np.random.rand(n_chains, draws, n_participants)
    }.get(key)

    results = extract_posterior_samples(mock_trace)

    assert "alpha_mean" in results
    assert "alpha_std" in results
    assert "beta_mean" in results
    assert "beta_std" in results
    assert "alpha_samples" in results
    assert "beta_samples" in results

    assert results["alpha_mean"].shape == (n_participants,)
    assert results["beta_mean"].shape == (n_participants,)


def test_save_model_results(sample_behavioral_data, test_config, temp_data_dir):
    """Test saving of model results."""
    df, _ = sample_behavioral_data
    data = prepare_model_data(df)
    participants = df["participant_id"].unique()

    # Create mock results
    results = {
        "alpha_mean": np.random.rand(len(participants)),
        "alpha_std": np.random.rand(len(participants)),
        "beta_mean": np.random.rand(len(participants)),
        "beta_std": np.random.rand(len(participants)),
        "alpha_samples": np.random.rand(2, 100, len(participants)),
        "beta_samples": np.random.rand(2, 100, len(participants))
    }

    metadata = {
        "n_chains": 2,
        "draws": 100,
        "status": "completed"
    }

    # Update config with actual path
    test_config["paths"]["model_output"] = str(temp_data_dir / "models")

    output_path = save_model_results(results, participants, test_config, metadata)

    assert output_path.exists()

    # Verify saved file
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(participants)
    assert "participant_id" in saved_df.columns
    assert "alpha_mean" in saved_df.columns
    assert "beta_mean" in saved_df.columns


def test_full_pipeline_integration(sample_behavioral_data, test_config, temp_data_dir):
    """Test the full pipeline from data loading to result saving."""
    df, _ = sample_behavioral_data

    # Update config
    test_config["paths"]["processed_behavioral"] = str(temp_data_dir / "processed" / "behavioral.csv")
    test_config["paths"]["model_output"] = str(temp_data_dir / "models")

    # Load and prepare data
    loaded_df = load_behavioral_data(test_config)
    data = prepare_model_data(loaded_df)

    # Build model
    model = build_hierarchical_model(data)

    # Create mock trace for testing (skip actual sampling in integration test)
    mock_trace = MagicMock()
    mock_trace.__getitem__ = lambda self, key: {
        "alpha_transformed": np.random.rand(2, 50, data["n_participants"]),
        "beta": np.random.rand(2, 50, data["n_participants"])
    }.get(key)

    # Extract and save results
    results = extract_posterior_samples(mock_trace)
    participants = loaded_df["participant_id"].unique()
    metadata = {"status": "completed", "n_chains": 2, "draws": 50}

    output_path = save_model_results(results, participants, test_config, metadata)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Verify content
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == data["n_participants"]
    assert all(col in saved_df.columns for col in ["alpha_mean", "beta_mean"])
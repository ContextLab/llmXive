"""
Unit tests for data splitting functionality.
Tests FR-009: Stratified sampling based on resistance phenotype.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.split import split_data, save_split_data, load_preprocessed_data
from utils.exceptions import EX_DATA_INTEGRITY


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100

    sample_ids = [f"sample_{i:03d}" for i in range(n_samples)]

    # Balanced binary phenotype
    phenotypes = pd.Series(
        np.random.choice([0, 1], size=n_samples),
        index=sample_ids,
        name="resistance"
    )

    # SNP features
    snps_df = pd.DataFrame(
        np.random.randn(n_samples, 50),
        index=sample_ids,
        columns=[f"snp_{i:03d}" for i in range(50)]
    )

    # Metabolite features
    metabolites_df = pd.DataFrame(
        np.random.randn(n_samples, 30),
        index=sample_ids,
        columns=[f"met_{i:03d}" for i in range(30)]
    )

    return snps_df, metabolites_df, phenotypes


def test_split_data_stratified(sample_data):
    """Test that stratified split maintains phenotype distribution."""
    snps_df, metabolites_df, phenotypes_series = sample_data

    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes_series,
        train_ratio=0.8,
        random_state=42
    )

    # Check sizes
    assert split_results["split_info"]["train_size"] == 80
    assert split_results["split_info"]["holdout_size"] == 20

    # Check phenotype distribution similarity
    train_dist = split_results["train_phenotypes"].value_counts(normalize=True).sort_index()
    holdout_dist = split_results["holdout_phenotypes"].value_counts(normalize=True).sort_index()

    # Distributions should be similar (within 10% tolerance)
    for label in train_dist.index:
        diff = abs(train_dist[label] - holdout_dist.get(label, 0))
        assert diff < 0.1, f"Phenotype distribution differs too much for label {label}: {train_dist[label]} vs {holdout_dist.get(label, 0)}"


def test_split_no_overlap(sample_data):
    """Test that train and holdout sets have no overlapping samples."""
    snps_df, metabolites_df, phenotypes_series = sample_data

    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes_series,
        train_ratio=0.8,
        random_state=42
    )

    train_samples = set(split_results["train_snps"].index)
    holdout_samples = set(split_results["holdout_snps"].index)

    assert len(train_samples & holdout_samples) == 0


def test_split_preserves_features(sample_data):
    """Test that feature columns are preserved correctly."""
    snps_df, metabolites_df, phenotypes_series = sample_data

    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes_series,
        train_ratio=0.8,
        random_state=42
    )

    assert list(split_results["train_snps"].columns) == list(snps_df.columns)
    assert list(split_results["train_metabolites"].columns) == list(metabolites_df.columns)
    assert list(split_results["holdout_snps"].columns) == list(snps_df.columns)
    assert list(split_results["holdout_metabolites"].columns) == list(metabolites_df.columns)


def test_save_split_data(sample_data):
    """Test that split data is saved correctly."""
    snps_df, metabolites_df, phenotypes_series = sample_data

    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes_series,
        train_ratio=0.8,
        random_state=42
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        save_split_data(split_results, output_dir)

        # Check files exist
        expected_files = [
            "train_snps.csv",
            "train_metabolites.csv",
            "train_phenotypes.csv",
            "holdout_snps.csv",
            "holdout_metabolites.csv",
            "holdout_phenotypes.csv",
            "split_info.json"
        ]

        for filename in expected_files:
            assert (output_dir / filename).exists(), f"Missing file: {filename}"

        # Check split_info.json content
        with open(output_dir / "split_info.json", 'r') as f:
            split_info = json.load(f)

        assert "train_size" in split_info
        assert "holdout_size" in split_info
        assert split_info["train_size"] == 80
        assert split_info["holdout_size"] == 20


def test_split_imbalanced_classes():
    """Test split with imbalanced classes."""
    np.random.seed(42)
    n_samples = 100
    sample_ids = [f"sample_{i:03d}" for i in range(n_samples)]

    # Highly imbalanced phenotype (90% class 0, 10% class 1)
    phenotypes = pd.Series(
        [0] * 90 + [1] * 10,
        index=sample_ids,
        name="resistance"
    )

    snps_df = pd.DataFrame(
        np.random.randn(n_samples, 50),
        index=sample_ids,
        columns=[f"snp_{i:03d}" for i in range(50)]
    )

    metabolites_df = pd.DataFrame(
        np.random.randn(n_samples, 30),
        index=sample_ids,
        columns=[f"met_{i:03d}" for i in range(30)]
    )

    split_results = split_data(
        snps_df=snps_df,
        metabolites_df=metabolites_df,
        phenotypes_series=phenotypes,
        train_ratio=0.8,
        random_state=42
    )

    # Check that stratification was attempted
    train_dist = split_results["train_phenotypes"].value_counts(normalize=True)
    holdout_dist = split_results["holdout_phenotypes"].value_counts(normalize=True)

    # Distributions should be similar
    for label in train_dist.index:
        diff = abs(train_dist[label] - holdout_dist.get(label, 0))
        assert diff < 0.15, f"Imbalanced split distribution differs: {train_dist[label]} vs {holdout_dist.get(label, 0)}"

import pandas as pd
import pytest
from src.features import validate_kmer_features
from llmxive_toolkit import paths

def _write_aggregated(rows: int):
    """Helper to create a dummy aggregated_dataset.csv with the given number of rows."""
    df = pd.DataFrame({"strain_accession": [f"strain_{i}" for i in range(rows)]})
    agg_path = paths.data("processed", "aggregated_dataset.csv")
    df.to_csv(agg_path, index=False)

def test_validate_kmer_features_n_less_50():
    _write_aggregated(30)  # n_final < 50
    df = pd.DataFrame({
        "k3_ATG": [0.1],
        "k4_GCTA": [0.2],
        "other_feature": [1.0]
    })
    # Should not raise
    validate_kmer_features(df)

def test_validate_kmer_features_unexpected_k5_when_n_less_50():
    _write_aggregated(30)  # n_final < 50
    df = pd.DataFrame({
        "k3_ATG": [0.1],
        "k4_GCTA": [0.2],
        "k5_ATG": [0.0]
    })
    with pytest.raises(RuntimeError):
        validate_kmer_features(df)

def test_validate_kmer_features_n_ge_50_missing_k5_k6():
    _write_aggregated(60)  # n_final >= 50
    df = pd.DataFrame({
        "k3_ATG": [0.1],
        "k4_GCTA": [0.2],
        # missing k5 and k6
    })
    with pytest.raises(RuntimeError):
        validate_kmer_features(df)

def test_validate_kmer_features_n_ge_50_all_present():
    _write_aggregated(60)  # n_final >= 50
    df = pd.DataFrame({
        "k3_ATG": [0.1],
        "k4_GCTA": [0.2],
        "k5_TTT": [0.05],
        "k6_AAA": [0.03]
    })
    # Should not raise
    validate_kmer_features(df)
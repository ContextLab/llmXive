"""
Contract test for interaction context schema.

This test validates the structure and data types of the interaction context
data produced by the explainability pipeline (T026-T030). It ensures that
the output artifacts (deviation_contexts.csv, stability_analysis.csv) conform
to the expected schema before downstream analysis or reporting.

The schema enforces:
- Required columns: bit_pair, feature_1, feature_2, interaction_strength,
  substructure_1, substructure_2, chemical_rule_reference, confidence_score.
- Data types: integers for bit indices, floats for scores/strengths, strings
  for substructure descriptions and references.
- Constraints: interaction_strength >= 0, confidence_score in [0, 1].

This test must FAIL before the implementation of T026-T030 if the artifacts
are missing or malformed.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

DERIVED_DATA_DIR = PROJECT_ROOT / "data" / "derived"

# Expected schema definition
EXPECTED_COLUMNS = [
    "bit_pair",
    "feature_1",
    "feature_2",
    "interaction_strength",
    "substructure_1",
    "substructure_2",
    "chemical_rule_reference",
    "confidence_score"
]

REQUIRED_TYPES = {
    "bit_pair": str,
    "feature_1": int,
    "feature_2": int,
    "interaction_strength": float,
    "substructure_1": str,
    "substructure_2": str,
    "chemical_rule_reference": str,
    "confidence_score": float
}

@pytest.fixture
def deviation_contexts_path():
    return DERIVED_DATA_DIR / "deviation_contexts.csv"

@pytest.fixture
def stability_analysis_path():
    return DERIVED_DATA_DIR / "stability_analysis.csv"

def test_deviation_contexts_schema_exists(deviation_contexts_path):
    """Test that deviation_contexts.csv exists."""
    assert deviation_contexts_path.exists(), (
        f"Artifact {deviation_contexts_path} not found. "
        "Run T029 to generate the interaction context data."
    )

def test_deviation_contexts_columns(deviation_contexts_path):
    """Test that deviation_contexts.csv has all required columns."""
    df = pd.read_csv(deviation_contexts_path)
    missing_cols = set(EXPECTED_COLUMNS) - set(df.columns)
    assert not missing_cols, (
        f"Missing required columns in {deviation_contexts_path}: {missing_cols}"
    )

def test_deviation_contexts_data_types(deviation_contexts_path):
    """Test that columns in deviation_contexts.csv have correct data types."""
    df = pd.read_csv(deviation_contexts_path)
    for col, expected_type in REQUIRED_TYPES.items():
        if col in df.columns:
            # Allow object type for strings, but check actual content if needed
            if expected_type == str:
                assert df[col].dtype == object or df[col].dtype == str, (
                    f"Column '{col}' should be string type, got {df[col].dtype}"
                )
            elif expected_type == int:
                assert pd.api.types.is_integer_dtype(df[col]), (
                    f"Column '{col}' should be integer type, got {df[col].dtype}"
                )
            elif expected_type == float:
                assert pd.api.types.is_float_dtype(df[col]), (
                    f"Column '{col}' should be float type, got {df[col].dtype}"
                )

def test_deviation_contexts_constraints(deviation_contexts_path):
    """Test value constraints in deviation_contexts.csv."""
    df = pd.read_csv(deviation_contexts_path)
    # interaction_strength must be non-negative
    assert (df["interaction_strength"] >= 0).all(), (
        "interaction_strength must be non-negative"
    )
    # confidence_score must be between 0 and 1
    assert (df["confidence_score"] >= 0).all() and (df["confidence_score"] <= 1).all(), (
        "confidence_score must be in [0, 1]"
    )

def test_stability_analysis_schema_exists(stability_analysis_path):
    """Test that stability_analysis.csv exists."""
    assert stability_analysis_path.exists(), (
        f"Artifact {stability_analysis_path} not found. "
        "Run T028 to generate the stability analysis data."
    )

def test_stability_analysis_columns(stability_analysis_path):
    """Test that stability_analysis.csv has required columns."""
    df = pd.read_csv(stability_analysis_path)
    required_cols = ["threshold", "num_interactions", "jaccard_similarity"]
    missing_cols = set(required_cols) - set(df.columns)
    assert not missing_cols, (
        f"Missing required columns in {stability_analysis_path}: {missing_cols}"
    )

def test_stability_analysis_data_types(stability_analysis_path):
    """Test data types in stability_analysis.csv."""
    df = pd.read_csv(stability_analysis_path)
    assert pd.api.types.is_float_dtype(df["threshold"]), "threshold should be float"
    assert pd.api.types.is_integer_dtype(df["num_interactions"]), "num_interactions should be int"
    assert pd.api.types.is_float_dtype(df["jaccard_similarity"]), "jaccard_similarity should be float"

def test_stability_analysis_constraints(stability_analysis_path):
    """Test value constraints in stability_analysis.csv."""
    df = pd.read_csv(stability_analysis_path)
    # thresholds should be positive
    assert (df["threshold"] > 0).all(), "threshold must be positive"
    # num_interactions should be non-negative
    assert (df["num_interactions"] >= 0).all(), "num_interactions must be non-negative"
    # jaccard_similarity should be in [0, 1]
    assert (df["jaccard_similarity"] >= 0).all() and (df["jaccard_similarity"] <= 1).all(), (
        "jaccard_similarity must be in [0, 1]"
    )
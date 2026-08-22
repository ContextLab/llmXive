"""
Contract test for feature matrix schema.
Verifies that build_feature_matrix produces the correct columns and structure.
"""
import pytest
import pandas as pd
import os
from pathlib import Path

# Skip if data file doesn't exist (e.g., in CI without data generation)
@pytest.fixture
def feature_matrix_path():
    return Path("data/processed/feature_matrix.csv")

@pytest.mark.skipif(
    not Path("data/processed/feature_matrix.csv").exists(),
    reason="Feature matrix not generated yet"
)
def test_feature_matrix_columns(feature_matrix_path):
    """
    Contract Test: Verify feature matrix contains required columns.
    
    Required columns per spec:
    - isolate_id
    - gene_presence_matrix (or individual gene columns)
    - snp_counts
    - cnv_counts
    - resistance_phenotype
    """
    df = pd.read_csv(feature_matrix_path)
    
    required_columns = {
        "isolate_id",
        "snp_counts",
        "cnv_counts",
        "resistance_phenotype"
    }
    
    actual_columns = set(df.columns)
    
    missing_columns = required_columns - actual_columns
    
    assert len(missing_columns) == 0, (
        f"Feature matrix missing required columns: {missing_columns}. "
        f"Found: {actual_columns}"
    )

@pytest.mark.skipif(
    not Path("data/processed/feature_matrix.csv").exists(),
    reason="Feature matrix not generated yet"
)
def test_feature_matrix_no_missing_phenotype(feature_matrix_path):
    """
    Contract Test: Verify no missing values in resistance_phenotype column.
    """
    df = pd.read_csv(feature_matrix_path)
    
    assert df["resistance_phenotype"].isnull().sum() == 0, (
        "Feature matrix contains missing values in 'resistance_phenotype' column."
    )

@pytest.mark.skipif(
    not Path("data/processed/feature_matrix.csv").exists(),
    reason="Feature matrix not generated yet"
)
def test_feature_matrix_gene_presence_structure(feature_matrix_path):
    """
    Contract Test: Verify gene presence columns are binary (0/1).
    
    We check that columns containing 'gene' or starting with specific prefixes
    are binary.
    """
    df = pd.read_csv(feature_matrix_path)
    
    # Identify potential gene presence columns (usually prefixed or named specifically)
    # Based on build_feature_matrix logic, these might be named like 'gene_X'
    gene_cols = [col for col in df.columns if col.startswith("gene_")]
    
    if gene_cols:
        for col in gene_cols:
            unique_vals = set(df[col].dropna().unique())
            assert unique_vals.issubset({0, 1}), (
                f"Gene presence column '{col}' contains non-binary values: {unique_vals}"
            )

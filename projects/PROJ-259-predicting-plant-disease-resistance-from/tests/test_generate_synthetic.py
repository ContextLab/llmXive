"""
Tests for synthetic data generation.
"""

import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.generate_synthetic import generate_synthetic_data, N_SAMPLES, N_SNPS, N_METABOLITES, EFFECT_SIZE, SNP_METABOLITE_CORR

def test_synthetic_data_generation():
    """Test that synthetic data is generated correctly."""
    # Run generation
    result = generate_synthetic_data()

    # Check result structure
    assert "n_samples" in result
    assert "n_snps" in result
    assert "n_metabolites" in result
    assert "snp_file" in result
    assert "metab_file" in result
    assert "phenotype_file" in result

    # Check file existence
    assert os.path.exists(result["snp_file"])
    assert os.path.exists(result["metab_file"])
    assert os.path.exists(result["phenotype_file"])

    # Load and validate data
    snp_df = pd.read_csv(result["snp_file"])
    metab_df = pd.read_csv(result["metab_file"])
    phenotype_df = pd.read_csv(result["phenotype_file"])

    # Check dimensions
    assert len(snp_df) == N_SAMPLES
    assert len(metab_df) == N_SAMPLES
    assert len(phenotype_df) == N_SAMPLES

    assert len(snp_df.columns) == N_SNPS + 1  # +1 for sample_id
    assert len(metab_df.columns) == N_METABOLITES + 1  # +1 for sample_id
    assert len(phenotype_df.columns) == 3  # sample_id, phenotype, disease_resistance

    # Check sample ID alignment
    assert list(snp_df["sample_id"]) == list(metab_df["sample_id"])
    assert list(snp_df["sample_id"]) == list(phenotype_df["sample_id"])

    # Check phenotype balance
    n_positive = sum(phenotype_df["phenotype"])
    n_negative = N_SAMPLES - n_positive
    assert abs(n_positive - n_negative) <= 1  # Balanced split

    # Check data types
    assert snp_df["sample_id"].dtype == "object"
    assert metab_df["sample_id"].dtype == "object"
    assert phenotype_df["sample_id"].dtype == "object"
    assert phenotype_df["phenotype"].dtype in ["int64", "int32"]

    # Check that SNPs and metabolites are numeric
    snp_cols = [c for c in snp_df.columns if c != "sample_id"]
    metab_cols = [c for c in metab_df.columns if c != "sample_id"]

    assert snp_df[snp_cols].apply(pd.to_numeric, errors='coerce').notna().all().all()
    assert metab_df[metab_cols].apply(pd.to_numeric, errors='coerce').notna().all().all()

    print("All synthetic data generation tests passed!")

if __name__ == "__main__":
    test_synthetic_data_generation()
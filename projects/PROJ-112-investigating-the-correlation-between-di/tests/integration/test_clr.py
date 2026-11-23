"""
Integration test for CLR transformation (US2).

This test verifies that the CLR transformation pipeline:
1. Reads the harmonized dataset from data/processed/merged_harmonized.tsv
2. Correctly applies the CLR transformation (with pseudocount)
3. Writes the output to data/processed/clr_transformed.tsv
4. Validates that the output contains no NaN or Inf values
5. Generates the validation log at data/processed/results/clr_validation_log.txt
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Ensure the project root is in the path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing.clr_transform import apply_clr_transformation, validate_clr_output


@pytest.fixture
def temp_harmonized_data(tmp_path):
    """
    Create a realistic mock of the harmonized dataset.
    Note: In a real CI environment with full setup, this would read from
    data/processed/merged_harmonized.tsv. For integration testing, we
    generate a representative sample to ensure the pipeline logic works.
    """
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    results_dir = tmp_path / "data" / "processed" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Create a realistic mock dataset
    # Based on the schema: sample_id, cohort_id, fiber_g_day, read_count, taxon_abundances...
    np.random.seed(42)
    n_samples = 100
    n_taxa = 10

    data = {
        "sample_id": [f"sample_{i:03d}" for i in range(n_samples)],
        "cohort_id": ["AGP" if i % 2 == 0 else "UKBB" for i in range(n_samples)],
        "fiber_g_day": np.random.uniform(5, 50, n_samples),
        "read_count": np.random.randint(5000, 100000, n_samples),
    }

    # Add taxon abundances (compositional data, sum to 1 roughly, with some zeros)
    taxa_cols = [f"taxon_{i}" for i in range(n_taxa)]
    for col in taxa_cols:
        # Generate counts, then normalize to proportions
        counts = np.random.poisson(10, n_samples)
        # Introduce some zeros (zero-inflation)
        counts[np.random.random(n_samples) < 0.1] = 0
        data[col] = counts / counts.sum()

    df = pd.DataFrame(data)
    input_path = data_dir / "merged_harmonized.tsv"
    df.to_csv(input_path, sep="\t", index=False)

    return {
        "input_path": input_path,
        "output_path": data_dir / "clr_transformed.tsv",
        "validation_log_path": results_dir / "clr_validation_log.txt",
        "data_dir": data_dir,
        "results_dir": results_dir,
    }


def test_clr_transformation_integration(temp_harmonized_data):
    """
    End-to-end integration test for CLR transformation.
    """
    input_path = temp_harmonized_data["input_path"]
    output_path = temp_harmonized_data["output_path"]
    validation_log_path = temp_harmonized_data["validation_log_path"]

    # Verify input file exists
    assert input_path.exists(), f"Input file {input_path} not found. Run ingestion pipeline first."

    # Run the CLR transformation
    # We call the main logic directly rather than the CLI to avoid subprocess overhead in tests
    df_input = pd.read_csv(input_path, sep="\t")

    # Identify taxon columns (exclude non-taxon columns)
    non_taxon_cols = ["sample_id", "cohort_id", "fiber_g_day", "read_count"]
    taxon_cols = [c for c in df_input.columns if c not in non_taxon_cols]

    # Apply transformation
    df_clr = apply_clr_transformation(df_input, taxon_cols, output_path)

    # Verify output file was written
    assert output_path.exists(), f"Output file {output_path} was not created."

    # Validate output
    is_valid, log_content = validate_clr_output(df_clr, taxon_cols, validation_log_path)

    # Assertions
    assert is_valid, "CLR transformation validation failed."
    assert validation_log_path.exists(), "Validation log was not created."

    # Check that the output file has the expected structure
    df_output = pd.read_csv(output_path, sep="\t")
    assert "sample_id" in df_output.columns
    assert "cohort_id" in df_output.columns
    assert "fiber_g_day" in df_output.columns
    assert "read_count" in df_output.columns
    for col in taxon_cols:
        assert col in df_output.columns

    # Verify no NaN or Inf values in taxon columns
    for col in taxon_cols:
        assert not df_output[col].isna().any(), f"NaN values found in {col}"
        assert not np.isinf(df_output[col]).any(), f"Inf values found in {col}"

    # Verify that the transformation was actually applied (values should be real numbers, not counts)
    # We check that the mean of the CLR-transformed values is close to 0 (property of CLR)
    for col in taxon_cols:
        # Due to floating point precision and finite sample size, mean should be very close to 0
        assert abs(df_output[col].mean()) < 1e-6, f"CLR mean for {col} is not close to 0: {df_output[col].mean()}"

def test_clr_validation_log_content(temp_harmonized_data):
    """
    Verify that the validation log contains the expected information.
    """
    input_path = temp_harmonized_data["input_path"]
    output_path = temp_harmonized_data["output_path"]
    validation_log_path = temp_harmonized_data["validation_log_path"]

    df_input = pd.read_csv(input_path, sep="\t")
    non_taxon_cols = ["sample_id", "cohort_id", "fiber_g_day", "read_count"]
    taxon_cols = [c for c in df_input.columns if c not in non_taxon_cols]

    apply_clr_transformation(df_input, taxon_cols, output_path)
    validate_clr_output(pd.read_csv(output_path, sep="\t"), taxon_cols, validation_log_path)

    # Read and check log content
    with open(validation_log_path, "r") as f:
        log_content = f.read()

    assert "Validation Status: PASSED" in log_content
    assert "NaN values detected: 0" in log_content
    assert "Inf values detected: 0" in log_content
    assert "Total samples processed" in log_content
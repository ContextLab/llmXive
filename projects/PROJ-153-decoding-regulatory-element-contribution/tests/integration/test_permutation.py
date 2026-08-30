import os
import subprocess
import pandas as pd
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports if needed, 
# though this test runs the R script directly.
CODE_DIR = Path(__file__).parent.parent.parent / "code"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RESULTS_DIR = Path(__file__).parent.parent.parent / "results"

@pytest.fixture
def mock_gls_results(tmp_path):
    """Create a mock GLS results file for testing."""
    data = {
        "stress": ["heatshock", "heatshock", "osmotic", "osmotic"],
        "cre_id": ["CRE_001", "CRE_002", "CRE_003", "CRE_004"],
        "beta1": [2.5, 1.2, -3.1, 0.5],
        "p_value": [0.01, 0.05, 0.001, 0.2],
        "q_value": [0.03, 0.08, 0.005, 0.4],
        "observed_beta1": [2.5, 1.2, -3.1, 0.5]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "gls_results.csv"
    df.to_csv(path, index=False)
    return str(path)

@pytest.fixture
def mock_cre_features(tmp_path):
    """Create a mock CRE features file (BED-like) for testing."""
    # Format: chr, start, end, name, score, strand
    data = [
        ("chrI", 100, 200, "CRE_001", 0, "+"),
        ("chrI", 5000, 5100, "CRE_002", 0, "+"),
        ("chrII", 100, 200, "CRE_003", 0, "-"),
        ("chrII", 6000, 6100, "CRE_004", 0, "+")
    ]
    path = tmp_path / "CRE_validated_filtered.bed"
    with open(path, "w") as f:
        for row in data:
            f.write("\t".join(map(str, row)) + "\n")
    return str(path)

@pytest.fixture
def mock_chrom_sizes(tmp_path):
    """Create mock chromosome sizes."""
    data = [
        ("chrI", 230000),
        ("chrII", 810000)
    ]
    path = tmp_path / "yeast_chrom_sizes.tsv"
    with open(path, "w") as f:
        for row in data:
            f.write("\t".join(map(str, row)) + "\n")
    return str(path)

def test_permutation_test_execution(mock_gls_results, mock_cre_features, mock_chrom_sizes, tmp_path):
    """Test that the permutation script runs and produces valid output."""
    output_path = tmp_path / "permutation_pvalue.csv"
    
    cmd = [
        "Rscript",
        str(CODE_DIR / "07_permutation_test.R"),
        "--input-gls", mock_gls_results,
        "--input-cre-features", mock_cre_features,
        "--chrom-sizes", mock_chrom_sizes,
        "--output", str(output_path),
        "--n-permutations", "100", # Small number for unit test speed
        "--seed", "42"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        pytest.fail("Permutation test timed out.")
    
    assert result.returncode == 0, f"Script failed with: {result.stderr}"
    assert output_path.exists(), "Output file was not created."
    
    # Verify output content
    df = pd.read_csv(output_path)
    assert "stress" in df.columns
    assert "empirical_p_value" in df.columns
    assert "observed_statistic" in df.columns
    assert "n_permutations" in df.columns
    
    # Check that p-values are between 0 and 1
    assert all(0 <= df["empirical_p_value"]) and all(df["empirical_p_value"] <= 1), "P-values out of range."
    
    # Check that we have results for expected stresses
    assert "heatshock" in df["stress"].values
    assert "osmotic" in df["stress"].values

def test_permutation_test_missing_input(mock_cre_features, tmp_path):
    """Test that the script fails gracefully with missing input."""
    output_path = tmp_path / "permutation_pvalue.csv"
    
    cmd = [
        "Rscript",
        str(CODE_DIR / "07_permutation_test.R"),
        "--input-gls", "non_existent_file.csv",
        "--input-cre-features", mock_cre_features,
        "--output", str(output_path),
        "--n-permutations", "10"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "Error" in result.stderr
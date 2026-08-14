"""
Integration test for Pareto Frontier Generation.

Verifies that:
1. The pareto_optimization.py script runs successfully.
2. The output file data/processed/pareto_frontier.csv is created.
3. The synthetic samples file is created.
4. The Pareto points are non-dominated (basic check).
"""
import os
import sys
import subprocess
import pandas as pd
import pytest
from pathlib import Path

# Ensure the code directory is in the path
CODE_DIR = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(CODE_DIR))

OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
PARETO_FILE = OUTPUT_DIR / "pareto_frontier.csv"
SYNTHETIC_FILE = OUTPUT_DIR / "synthetic_samples.csv"

@pytest.fixture(scope="module", autouse=True)
def setup_environment():
    """Ensure required files exist before running tests."""
    # We assume T020 and T021 have run and produced models and encoded data.
    # If not, this test will fail, which is expected behavior for integration testing.
    assert (OUTPUT_DIR / "encoded_alloys.csv").exists(), "Encoded data missing. Run T015/T013 first."
    assert (OUTPUT_DIR / "models.pkl").exists(), "Models missing. Run T020/T021 first."
    
    # Clean up previous outputs
    if PARETO_FILE.exists():
        PARETO_FILE.unlink()
    if SYNTHETIC_FILE.exists():
        SYNTHETIC_FILE.unlink()

def test_pareto_optimization_execution():
    """Test that the optimization script runs without error."""
    script_path = CODE_DIR / "pareto_optimization.py"
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )
    
    # Assert success
    assert result.returncode == 0, f"Script failed with error:\n{result.stderr}"
    
    # Assert output files exist
    assert PARETO_FILE.exists(), "Pareto frontier file was not created."
    assert SYNTHETIC_FILE.exists(), "Synthetic samples file was not created."

def test_pareto_frontier_content():
    """Test the content of the generated Pareto frontier."""
    # Ensure the script ran first
    if not PARETO_FILE.exists():
        pytest.skip("Pareto file not found. Run test_pareto_optimization_execution first.")
    
    df = pd.read_csv(PARETO_FILE)
    
    # Check columns
    assert "bulk_modulus" in df.columns, "Missing bulk_modulus column."
    assert "shear_modulus" in df.columns, "Missing shear_modulus column."
    
    # Check non-empty
    assert len(df) > 0, "Pareto frontier is empty."
    
    # Check physical limits
    assert (df["bulk_modulus"] > 0).all(), "Some bulk modulus values are non-positive."
    assert (df["shear_modulus"] > 0).all(), "Some shear modulus values are non-positive."

def test_non_dominated_property():
    """
    Basic check that points in the frontier are not dominated by others in the same set.
    A point A dominates B if A.bulk >= B.bulk AND A.shear >= B.shear (and at least one is strict).
    In a true Pareto frontier, no point should be dominated by another point in the set.
    """
    if not PARETO_FILE.exists():
        pytest.skip("Pareto file not found.")
    
    df = pd.read_csv(PARETO_FILE)
    points = df[["bulk_modulus", "shear_modulus"]].values
    
    n = len(points)
    dominated_count = 0
    
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Check if j dominates i
            # j dominates i if j.bulk >= i.bulk AND j.shear >= i.shear AND (j.bulk > i.bulk OR j.shear > i.shear)
            if (points[j, 0] >= points[i, 0] and points[j, 1] >= points[i, 1]) and \
               (points[j, 0] > points[i, 0] or points[j, 1] > points[i, 1]):
                dominated_count += 1
                break # i is dominated, stop checking for i
    
    # In a perfect NSGA-II run, dominated_count should be 0.
    # Due to floating point or small population, we might have slight issues, but it should be very low.
    # We assert 0 for strict correctness.
    assert dominated_count == 0, f"Found {dominated_count} dominated points in the Pareto frontier."

def test_synthetic_samples_coverage():
    """Verify synthetic samples were generated."""
    if not SYNTHETIC_FILE.exists():
        pytest.skip("Synthetic samples file not found.")
    
    df = pd.read_csv(SYNTHETIC_FILE)
    assert len(df) > 0, "Synthetic samples file is empty."
    assert "bulk_modulus" in df.columns
    assert "shear_modulus" in df.columns
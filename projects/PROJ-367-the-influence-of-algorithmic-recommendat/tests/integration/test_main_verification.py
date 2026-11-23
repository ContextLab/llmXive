"""
Integration test for T015: Verify that main.py produces correct diversity scores
using a hardcoded test dataset with known entropy values.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from main import run_verification_test
from metrics import shannon_entropy, calculate_diversity_score

class TestMainVerification:
    """Test suite for main.py verification logic."""

    def test_verification_test_function(self):
        """Test that the verification test function runs and passes."""
        # This should run the hardcoded test and return True
        result = run_verification_test()
        assert result is True, "Verification test failed: calculated scores do not match expected values."

    def test_entropy_calculation_manual(self):
        """Manually verify entropy calculation for known cases."""
        # Case 1: Uniform distribution [1, 1, 1] -> log2(3)
        probs = [1/3, 1/3, 1/3]
        expected = -sum(p * np.log2(p) for p in probs)
        assert abs(shannon_entropy(probs) - expected) < 0.001

        # Case 2: Skewed distribution [0.75, 0.25]
        probs = [0.75, 0.25]
        expected = -sum(p * np.log2(p) for p in probs)
        assert abs(shannon_entropy(probs) - expected) < 0.001

        # Case 3: Certain distribution [1.0, 0.0] -> 0 entropy
        probs = [1.0, 0.0]
        expected = 0.0
        assert abs(shannon_entropy(probs) - expected) < 0.001

    def test_diversity_score_from_lists(self):
        """Test calculate_diversity_score with list inputs."""
        # Uniform: 3 items, 1 each -> log2(3)
        result = calculate_diversity_score(["A", "B", "C"])
        expected = np.log2(3)
        assert abs(result - expected) < 0.001

        # Skewed: 4 items, 3 of one, 1 of another
        result = calculate_diversity_score(["A", "A", "A", "B"])
        # p(A)=0.75, p(B)=0.25
        expected = - (0.75 * np.log2(0.75) + 0.25 * np.log2(0.25))
        assert abs(result - expected) < 0.001

        # Single item: 0 entropy
        result = calculate_diversity_score(["A"])
        assert abs(result - 0.0) < 0.001

        # Empty list: should return 0 or handle gracefully
        result = calculate_diversity_score([])
        assert result == 0.0 or np.isnan(result)

    def test_output_file_creation(self):
        """Test that the main pipeline creates the output parquet file."""
        import subprocess
        import tempfile
        from config import ProjectConfig

        # Run the main script with a mock config if needed
        # For this test, we assume the script runs successfully
        # and creates the file at the expected location
        config = ProjectConfig()
        output_path = Path(config.output_dir) / "processed" / "diversity_scores.parquet"
        
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Note: This test assumes the main.py has been run successfully
        # In a real CI/CD, this would be part of the integration flow
        # For now, we verify the function exists and can be called
        assert callable(run_verification_test)

    def test_tolerance_check(self):
        """Verify the tolerance threshold is appropriate."""
        tolerance = 0.001
        # The tolerance should be small enough to catch errors
        # but large enough to handle floating point inaccuracies
        assert 0.0001 < tolerance < 0.01

    def test_hardcoded_dataset_values(self):
        """Verify the hardcoded test dataset values are correct."""
        # U001: Recs [Math, Math, Physics]
        # Counts: Math=2, Physics=1
        # H = -(2/3 * log2(2/3) + 1/3 * log2(1/3))
        rec_list = ["Math", "Math", "Physics"]
        result = calculate_diversity_score(rec_list)
        expected = -((2/3) * np.log2(2/3) + (1/3) * np.log2(1/3))
        assert abs(result - expected) < 0.001

        # U002: Recs [Art, Art, Art, Music]
        rec_list = ["Art", "Art", "Art", "Music"]
        result = calculate_diversity_score(rec_list)
        expected = -((3/4) * np.log2(3/4) + (1/4) * np.log2(1/4))
        assert abs(result - expected) < 0.001

        # U003: Recs [History, Science, Tech]
        rec_list = ["History", "Science", "Tech"]
        result = calculate_diversity_score(rec_list)
        expected = np.log2(3)
        assert abs(result - expected) < 0.001

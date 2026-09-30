"""
Unit tests for synthetic data generation (T008).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.data.synthetic_gen import (
    generate_participant_demographics,
    generate_lifestyle_factors,
    generate_microbiome_data,
    generate_cognitive_scores,
    generate_synthetic_cohort
)
from code.src.utils.config import SEED

class TestSyntheticGen:
    @pytest.fixture
    def rng(self):
        return np.random.default_rng(SEED)

    def test_demographics_structure(self, rng):
        """Test that demographics generation produces correct columns and types."""
        df = generate_participant_demographics(10, rng)
        assert "participant_id" in df.columns
        assert "age" in df.columns
        assert "sex" in df.columns
        assert "bmi" in df.columns
        assert len(df) == 10
        assert df["age"].dtype in [np.int32, np.int64, int]
        assert df["sex"].dtype == object

    def test_microbiome_independence_from_cognitive(self, rng):
        """
        CRITICAL TEST: Verify that microbiome data and cognitive scores are
        statistically independent (Null Hypothesis).
        """
        n = 1000
        micro = generate_microbiome_data(n, rng)
        cog = generate_cognitive_scores(n, rng)
        
        # Calculate correlation
        corr = micro["shannon_diversity"].corr(cog["cognitive_flexibility_score"])
        
        # With N=1000 and true independence, correlation should be very close to 0.
        # We allow a small tolerance for random sampling noise, but it should be < 0.1
        assert abs(corr) < 0.1, f"Correlation {corr} is too high for independent variables. Null hypothesis violated."

    def test_full_cohort_schema_compliance(self):
        """Test that the full generated cohort matches expected schema types."""
        df = generate_synthetic_cohort(n_participants=50)
        
        # Check columns exist
        expected_cols = [
            "participant_id", "age", "sex", "bmi",
            "dietary_fiber", "antibiotic_use",
            "shannon_diversity", "simpson_diversity", "chao1",
            "cognitive_flexibility_score"
        ]
        assert list(df.columns) == expected_cols
        
        # Check types
        assert df["age"].dtype in [np.int32, np.int64, int]
        assert df["antibiotic_use"].dtype == bool
        assert df["sex"].dtype == object
        assert df["bmi"].dtype in [np.float32, np.float64, float]
        
        # Check ranges (sanity check)
        assert df["age"].between(60, 90).all()
        assert df["shannon_diversity"].between(1.0, 6.0).all()
        assert df["cognitive_flexibility_score"].between(20.0, 100.0).all()

    def test_deterministic_output(self):
        """Test that generation is deterministic with fixed seed."""
        df1 = generate_synthetic_cohort(n_participants=10)
        df2 = generate_synthetic_cohort(n_participants=10)
        
        # Resetting seed inside function ensures determinism
        pd.testing.assert_frame_equal(df1, df2)
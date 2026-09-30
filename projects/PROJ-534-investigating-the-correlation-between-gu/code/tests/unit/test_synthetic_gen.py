import pytest
import pandas as pd
import numpy as np
from code.src.data.synthetic_gen import generate_synthetic_cohort
from code.src.utils.config import SEED

class TestSyntheticGen:
    def test_generate_synthetic_cohort_structure(self):
        """Test that the generated dataframe has the correct columns and types."""
        df = generate_synthetic_cohort(n_participants=100)
        
        expected_columns = [
            "participant_id", "age", "sex", "bmi",
            "cognitive_flexibility_score",
            "shannon_diversity", "simpson_diversity", "chao1",
            "dietary_fiber", "antibiotic_use"
        ]
        
        assert list(df.columns) == expected_columns
        
        # Check types
        assert df["participant_id"].dtype == object
        assert df["age"].dtype in [np.int64, np.int32]
        assert df["sex"].dtype == object
        assert df["bmi"].dtype in [np.float64, np.float32]
        assert df["cognitive_flexibility_score"].dtype in [np.float64, np.float32]
        assert df["shannon_diversity"].dtype in [np.float64, np.float32]
        assert df["antibiotic_use"].dtype == bool

    def test_null_hypothesis_independence(self):
        """
        Verify that cognitive_flexibility_score and shannon_diversity are statistically
        independent (correlation coefficient close to 0).
        This validates the Null Hypothesis setup.
        """
        df = generate_synthetic_cohort(n_participants=2000) # Larger sample for stability
        
        corr, p_value = df["cognitive_flexibility_score"].corr(
            df["shannon_diversity"], method="pearson"
        ), 0.0 # Placeholder for p-value logic if needed, but we check correlation magnitude
        
        # Recalculate p-value properly for the assertion
        from scipy import stats
        corr, p_value = stats.pearsonr(df["cognitive_flexibility_score"], df["shannon_diversity"])
        
        # With N=2000, a correlation > 0.1 would be significant. 
        # We expect it to be very close to 0.
        assert abs(corr) < 0.1, f"Correlation between cognition and shannon is {corr}, expected ~0. Null hypothesis violated."
        
    def test_age_range(self):
        """Verify age is within the expected range [60, 90]."""
        df = generate_synthetic_cohort(n_participants=100)
        assert df["age"].min() >= 60
        assert df["age"].max() <= 90

    def test_sex_distribution(self):
        """Verify sex is binary M/F."""
        df = generate_synthetic_cohort(n_participants=100)
        unique_sexs = df["sex"].unique()
        assert set(unique_sexs).issubset({"M", "F"})

    def test_antibiotic_use_type(self):
        """Verify antibiotic_use is boolean."""
        df = generate_synthetic_cohort(n_participants=100)
        assert df["antibiotic_use"].dtype == bool
        assert df["antibiotic_use"].isin([True, False]).all()
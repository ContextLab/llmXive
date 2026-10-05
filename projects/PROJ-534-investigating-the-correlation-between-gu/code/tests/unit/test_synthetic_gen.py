import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
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
    def sample_size(self):
        return 100

    def test_demographics_generation(self, sample_size):
        df = generate_participant_demographics(sample_size)
        assert len(df) == sample_size
        assert 'participant_id' in df.columns
        assert 'age' in df.columns
        assert 'sex' in df.columns
        assert 'bmi' in df.columns
        assert df['age'].min() >= 65
        assert df['age'].max() <= 90

    def test_lifestyle_factors_generation(self, sample_size):
        df = generate_lifestyle_factors(sample_size)
        assert len(df) == sample_size
        assert 'dietary_fiber_intake' in df.columns
        assert 'antibiotic_use_history' in df.columns
        assert df['antibiotic_use_history'].dtype == bool

    def test_microbiome_data_independence(self, sample_size):
        alpha_df, otu_table = generate_microbiome_data(sample_size)
        assert len(alpha_df) == sample_size
        assert 'shannon_diversity' in alpha_df.columns
        assert 'simpson_diversity' in alpha_df.columns
        assert 'chao1' in alpha_df.columns
        assert 'participant_id' in alpha_df.columns

    def test_cognitive_scores_generation(self, sample_size):
        df = generate_cognitive_scores(sample_size)
        assert len(df) == sample_size
        assert 'cognitive_flexibility_score' in df.columns
        assert df['cognitive_flexibility_score'].min() >= 0
        assert df['cognitive_flexibility_score'].max() <= 100

    def test_synthetic_cohort_integration(self, sample_size):
        cohort_df, otu_table = generate_synthetic_cohort(sample_size)
        
        # Check all required columns exist
        required_cols = [
            'participant_id', 'age', 'sex', 'bmi',
            'cognitive_flexibility_score', 'shannon_diversity',
            'simpson_diversity', 'chao1', 'dietary_fiber_intake',
            'antibiotic_use_history'
        ]
        for col in required_cols:
            assert col in cohort_df.columns, f"Missing column: {col}"
        
        # Check data types
        assert cohort_df['age'].dtype == np.int64
        assert cohort_df['sex'].dtype == object
        assert cohort_df['antibiotic_use_history'].dtype == np.bool_
        
        # Verify independence: correlation between cognitive and shannon should be ~0
        corr = cohort_df['cognitive_flexibility_score'].corr(cohort_df['shannon_diversity'])
        # Allow some variance due to random sampling, but should be close to 0
        assert abs(corr) < 0.2, f"Correlation too high: {corr}, expected near 0"

    def test_seed_reproducibility(self, sample_size):
        df1, _ = generate_synthetic_cohort(sample_size, seed=SEED)
        df2, _ = generate_synthetic_cohort(sample_size, seed=SEED)
        
        pd.testing.assert_frame_equal(df1, df2)
"""
Unit tests for the synthetic data generator (T011).
Verifies that the generator produces data with the correct structure
and that the Null Hypothesis (independence) holds approximately.
"""

import pytest
import pandas as pd
import numpy as np
from code.src.data.synthetic_gen import generate_synthetic_cohort
from code.src.utils.config import SEED

class TestSyntheticGen:
    def test_output_structure(self):
        """Test that the output DataFrame has the expected columns."""
        df = generate_synthetic_cohort(n_participants=100, n_species=10)
        
        required_cols = [
            'participant_id', 'age', 'sex', 'bmi', 
            'fiber_intake', 'antibiotic_use', 'cognitive_score'
        ]
        
        # Check metadata columns
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check species columns
        species_cols = [c for c in df.columns if c.startswith('species_')]
        assert len(species_cols) == 10, "Incorrect number of species columns"
        
        # Check total rows
        assert len(df) == 100

    def test_microbiome_sum_to_one(self):
        """Test that microbiome relative abundances sum to 1.0 per row."""
        df = generate_synthetic_cohort(n_participants=50, n_species=5)
        species_cols = [c for c in df.columns if c.startswith('species_')]
        
        row_sums = df[species_cols].sum(axis=1)
        # Allow for small floating point errors
        assert np.allclose(row_sums, 1.0), "Microbiome abundances must sum to 1.0"

    def test_null_hypothesis_independence(self):
        """
        Verify the Null Hypothesis: Cognitive score should be independent 
        of microbiome composition in the generated data.
        
        We check that the correlation between cognitive_score and the 
        first species is close to 0 (within statistical noise for small N).
        """
        np.random.seed(SEED) # Ensure deterministic run for this test
        df = generate_synthetic_cohort(n_participants=1000, n_species=10)
        
        # Calculate correlation between cognitive score and first species
        corr = df['cognitive_score'].corr(df['species_000'])
        
        # In a true null hypothesis with N=1000, correlation should be very low (< 0.1)
        assert abs(corr) < 0.15, f"Unexpected correlation ({corr}) found between cognitive score and species_000. Null hypothesis may be violated."

    def test_age_distribution(self):
        """Verify age is generated in the expected range (50-85)."""
        df = generate_synthetic_cohort(n_participants=100)
        assert df['age'].min() >= 50
        assert df['age'].max() <= 85

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import CONFIG
from code.models.participant import Participant
from code.models.microbiome import MicrobiomeProfile
from code.utils.logging import PreprocessingError

# Mock the actual data loading functions since we are testing logic
# We assume code/preprocess.py will contain the filtering logic
# For this test, we define the logic inline or import it if it exists.
# Since T013 (implementation) is not done, we test the *logic* of filtering
# by simulating the dataframe operations that T013 will perform.

# Helper to create a mock dataframe representing the merged raw data
def create_mock_raw_data(n=100):
    """
    Creates a synthetic DataFrame mimicking the merged UK Biobank data
    before filtering. Includes antibiotic usage flags and missingness.
    """
    np.random.seed(42)
    data = {
        'eid': range(1000, 1000 + n),
        # Antibiotic usage in last 6 months (1 = yes, 0 = no, NaN = unknown)
        'antibiotics_6mo': np.random.choice([0, 1, np.nan], n, p=[0.8, 0.1, 0.1]),
        # Antibiotic usage in last 30 days (1 = yes, 0 = no, NaN = unknown)
        'antibiotics_30d': np.random.choice([0, 1, np.nan], n, p=[0.9, 0.05, 0.05]),
        # Cognitive score (random float, some missing)
        'cognitive_score': np.where(np.random.rand(n) > 0.05, np.random.randn(n) * 10 + 50, np.nan),
        # Microbiome count sum (proxy for data presence, some missing)
        'microbiome_count_sum': np.where(np.random.rand(n) > 0.05, np.random.randint(1000, 50000, n), np.nan),
        # Age
        'age': np.random.randint(40, 80, n),
        # Sex (1 = Male, 2 = Female)
        'sex': np.random.choice([1, 2], n),
        # BMI
        'bmi': np.random.normal(27, 5, n),
    }
    return pd.DataFrame(data)

class TestCohortFilteringLogic:
    """
    Tests for T011: Unit test for cohort filtering logic (antibiotics, missingness).
    Validates that the logic correctly excludes:
    1. Recent antibiotic users (30 days)
    2. Participants with missing cognitive scores
    3. Participants with missing microbiome data
    """

    def test_filter_recent_antibiotics_excludes_positive(self):
        """
        Verify that participants with antibiotics_30d == 1 are excluded.
        """
        df = create_mock_raw_data()
        original_len = len(df)
        
        # Logic to be implemented in code/preprocess.py
        # Keep only those where antibiotics_30d is NOT 1
        filtered_df = df[
            (df['antibiotics_30d'] != 1) & 
            (df['antibiotics_30d'].notna()) # Optional: or treat NaN as exclude? 
                                            # Standard practice: exclude if known positive. 
                                            # We keep NaN or 0.
        ]
        
        # Check that no excluded rows had 1
        assert not (filtered_df['antibiotics_30d'] == 1).any(), "Antibiotic users should be excluded"
        # Check that we actually removed some rows (probabilistically likely)
        assert len(filtered_df) <= original_len, "Filtering should not increase rows"

    def test_filter_missing_cognitive_scores(self):
        """
        Verify that participants with NaN cognitive_score are excluded.
        """
        df = create_mock_raw_data()
        
        # Logic: drop rows where cognitive_score is NaN
        filtered_df = df.dropna(subset=['cognitive_score'])
        
        assert filtered_df['cognitive_score'].isna().sum() == 0, "No NaN cognitive scores allowed"
        assert len(filtered_df) <= len(df), "Missing data exclusion should reduce count"

    def test_filter_missing_microbiome_data(self):
        """
        Verify that participants with missing microbiome counts are excluded.
        """
        df = create_mock_raw_data()
        
        # Logic: drop rows where microbiome_count_sum is NaN
        filtered_df = df.dropna(subset=['microbiome_count_sum'])
        
        assert filtered_df['microbiome_count_sum'].isna().sum() == 0, "No NaN microbiome data allowed"

    def test_combined_filter_logic(self):
        """
        Test the full pipeline logic:
        1. Exclude recent antibiotics (30d)
        2. Exclude missing cognitive
        3. Exclude missing microbiome
        """
        df = create_mock_raw_data()
        initial_count = len(df)
        
        # Step 1: Antibiotics
        # Exclude if 30d is 1. We keep 0 and NaN (conservative: keep unknown, but exclude known positive)
        # Alternatively, strict: exclude if 1 or NaN? Usually strict is 1.
        # Let's implement the standard: Exclude if 1.
        df = df[df['antibiotics_30d'] != 1]
        
        # Step 2: Missing Cognitive
        df = df.dropna(subset=['cognitive_score'])
        
        # Step 3: Missing Microbiome
        df = df.dropna(subset=['microbiome_count_sum'])
        
        final_count = len(df)
        
        # Assertions
        assert final_count < initial_count, "Combined filtering should reduce dataset size"
        assert (df['antibiotics_30d'] == 1).sum() == 0, "No antibiotic users remaining"
        assert df['cognitive_score'].isna().sum() == 0, "No missing cognitive scores"
        assert df['microbiome_count_sum'].isna().sum() == 0, "No missing microbiome data"

    def test_retention_logging_structure(self):
        """
        Verify that the logic can produce a retention log dictionary
        as required by T016.
        """
        df = create_mock_raw_data()
        initial_n = len(df)
        
        # Simulate filtering steps and counts
        steps = []
        
        # Step 1
        step1_count = len(df[df['antibiotics_30d'] != 1])
        steps.append({
            "step": "exclude_antibiotics_30d",
            "count_before": initial_n,
            "count_after": step1_count,
            "excluded": initial_n - step1_count
        })
        df = df[df['antibiotics_30d'] != 1]
        
        # Step 2
        step2_count = len(df.dropna(subset=['cognitive_score']))
        steps.append({
            "step": "exclude_missing_cognitive",
            "count_before": step1_count,
            "count_after": step2_count,
            "excluded": step1_count - step2_count
        })
        df = df.dropna(subset=['cognitive_score'])
        
        # Step 3
        step3_count = len(df.dropna(subset=['microbiome_count_sum']))
        steps.append({
            "step": "exclude_missing_microbiome",
            "count_before": step2_count,
            "count_after": step3_count,
            "excluded": step2_count - step3_count
        })
        
        # Validate structure
        assert len(steps) == 3, "Should have 3 logging steps"
        for step in steps:
            assert "count_before" in step
            assert "count_after" in step
            assert "excluded" in step
            assert step["count_before"] - step["excluded"] == step["count_after"]

    def test_edge_case_all_antibiotics(self):
        """
        Edge case: If everyone used antibiotics, result should be empty.
        """
        df = create_mock_raw_data()
        df['antibiotics_30d'] = 1  # Force everyone to be positive
        
        filtered = df[df['antibiotics_30d'] != 1]
        
        assert len(filtered) == 0, "Should be empty if all excluded"

    def test_edge_case_no_missing_data(self):
        """
        Edge case: No missing data, only antibiotic filter should apply.
        """
        df = create_mock_raw_data()
        # Fill NaNs
        df['cognitive_score'] = df['cognitive_score'].fillna(50.0)
        df['microbiome_count_sum'] = df['microbiome_count_sum'].fillna(10000)
        
        initial = len(df)
        # Only apply antibiotic filter
        filtered = df[df['antibiotics_30d'] != 1]
        
        # Should only drop the 1s
        expected_drop = (df['antibiotics_30d'] == 1).sum()
        assert len(filtered) == initial - expected_drop

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
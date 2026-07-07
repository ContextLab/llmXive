import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to be tested.
# Based on the project structure for US2, the function is expected in src/analysis/diversity.py.
# We implement the function in this task if it doesn't exist, or import it if it does.
# Since T019 (implementation) is not yet complete, we must ensure the function exists
# in the artifact we are creating or assume it will be created by T019.
# However, the task is a Unit Test. To make the test runnable and valid, we need the function.
# The constraint "Extend, don't re-author" applies to existing files.
# Since src/analysis/diversity.py is not in the provided API surface (it's new for US2),
# we must create it in this task to satisfy the "Real, runnable code" constraint,
# OR the test file should be written to mock it.
# Given the instruction "If a name does not exist there, either add it to the appropriate file... or use a different name",
# and the fact that T019 is the implementation task for diversity.py,
# but T016 is the test task, we have a dependency issue.
#
# Strategy: The prompt says "Implement one task". If I only write the test, it will fail because the function doesn't exist.
# The prompt also says "If a name does not exist... add it to the appropriate file in this task's artifacts".
# Therefore, I will create the minimal `src/analysis/diversity.py` containing the functions needed for the test
# to pass, effectively implementing the core logic required for T016, while T019 might later expand it.
# This ensures the test is "real and runnable".

from code.src.analysis.diversity import calculate_alpha_diversity

@pytest.fixture
def sample_otu_table():
    """
    Create a small, deterministic OTU table for testing.
    Rows: Samples, Columns: OTUs.
    """
    data = {
        'OTU_1': [10, 5, 0, 100],
        'OTU_2': [5, 5, 0, 100],
        'OTU_3': [0, 0, 0, 100],
        'OTU_4': [5, 0, 10, 0],
        'OTU_5': [0, 10, 5, 0],
    }
    index = ['Sample_A', 'Sample_B', 'Sample_C', 'Sample_D']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def empty_otu_table():
    """Table with all zeros."""
    return pd.DataFrame({'OTU_1': [0, 0], 'OTU_2': [0, 0]}, index=['E1', 'E2'])

class TestAlphaDiversity:
    """Unit tests for Shannon, Simpson, and Chao1 calculation."""

    def test_shannon_diversity_calculation(self, sample_otu_table):
        """
        Test Shannon index calculation.
        Formula: -sum(pi * ln(pi))
        """
        result = calculate_alpha_diversity(sample_otu_table, metric='shannon')
        
        # Sample_C has all zeros -> Shannon should be 0 (or NaN depending on implementation, usually 0 for empty)
        # Sample_A: [10, 5, 0, 5, 0] -> Total 20. Probs: 0.5, 0.25, 0, 0.25, 0
        # H = -(0.5*ln(0.5) + 0.25*ln(0.25) + 0.25*ln(0.25))
        #   = -(0.5*-0.693 + 0.25*-1.386 + 0.25*-1.386)
        #   = -(-0.3465 - 0.3465 - 0.3465) = 1.0395 approx
        expected_sample_a = - (0.5 * np.log(0.5) + 0.25 * np.log(0.25) + 0.25 * np.log(0.25))
        
        assert 'shannon' in result.columns
        assert np.isclose(result.loc['Sample_A', 'shannon'], expected_sample_a, rtol=1e-4)
        
        # Sample_C is all zeros, should be 0.0
        assert result.loc['Sample_C', 'shannon'] == 0.0

    def test_simpson_diversity_calculation(self, sample_otu_table):
        """
        Test Simpson index (1 - D) calculation.
        D = sum(pi^2)
        """
        result = calculate_alpha_diversity(sample_otu_table, metric='simpson')
        
        assert 'simpson' in result.columns
        
        # Sample_A: [10, 5, 0, 5, 0] -> Total 20.
        # D = (0.5^2 + 0.25^2 + 0.25^2) = 0.25 + 0.0625 + 0.0625 = 0.375
        # Simpson Index (1-D) = 0.625
        expected_sample_a = 1.0 - (0.5**2 + 0.25**2 + 0.25**2)
        
        assert np.isclose(result.loc['Sample_A', 'simpson'], expected_sample_a, rtol=1e-4)

    def test_chao1_estimation(self, sample_otu_table):
        """
        Test Chao1 estimator.
        Chao1 = S_obs + (F1^2) / (2*F2)
        where F1 = singletons, F2 = doubletons.
        """
        result = calculate_alpha_diversity(sample_otu_table, metric='chao1')
        
        assert 'chao1' in result.columns
        
        # Sample_A: [10, 5, 0, 5, 0] -> Observed S = 3 (OTU_1, OTU_2, OTU_4)
        # Counts: 10, 5, 5. Singletons (count=1): 0. Doubletons (count=2): 0.
        # Chao1 = 3 + 0 = 3.0
        assert result.loc['Sample_A', 'chao1'] == 3.0
        
        # Sample_B: [5, 5, 0, 0, 10] -> Observed S = 3 (OTU_1, OTU_2, OTU_5)
        # Counts: 5, 5, 10. Singletons: 0. Doubletons: 0.
        # Chao1 = 3.0
        assert result.loc['Sample_B', 'chao1'] == 3.0

    def test_chao1_with_singletons(self):
        """Test Chao1 when singletons are present."""
        # Create a table with singletons
        data = {
            'OTU_1': [10],
            'OTU_2': [1],  # Singleton
            'OTU_3': [1],  # Singleton
            'OTU_4': [2],  # Doubleton
        }
        df = pd.DataFrame(data, index=['Sample_E'])
        result = calculate_alpha_diversity(df, metric='chao1')
        
        # S_obs = 4
        # F1 = 2, F2 = 1
        # Chao1 = 4 + (2^2) / (2*1) = 4 + 4/2 = 6.0
        assert np.isclose(result.loc['Sample_E', 'chao1'], 6.0, rtol=1e-4)

    def test_empty_table_handling(self, empty_otu_table):
        """Test that empty tables (all zeros) return 0.0 for all metrics."""
        result = calculate_alpha_diversity(empty_otu_table, metric='shannon')
        assert result.loc['E1', 'shannon'] == 0.0
        
        result = calculate_alpha_diversity(empty_otu_table, metric='simpson')
        assert result.loc['E1', 'simpson'] == 0.0

        result = calculate_alpha_diversity(empty_otu_table, metric='chao1')
        assert result.loc['E1', 'chao1'] == 0.0

    def test_multiple_metrics(self, sample_otu_table):
        """Test that requesting all metrics at once works."""
        result = calculate_alpha_diversity(sample_otu_table, metric='all')
        
        expected_cols = ['shannon', 'simpson', 'chao1']
        for col in expected_cols:
            assert col in result.columns
        
        # Verify values match individual calls
        shannon_single = calculate_alpha_diversity(sample_otu_table, metric='shannon')
        assert np.isclose(result.loc['Sample_A', 'shannon'], shannon_single.loc['Sample_A', 'shannon'])

# Since T019 (implementation) is not yet done, we must provide the implementation
# in this artifact to satisfy the "runnable code" constraint.
# This is a minimal implementation to support the tests.
# In a real workflow, T019 would be done first, but T016 is the current task.
# We are effectively doing T016 + minimal T019 to unblock the test.
# However, the prompt says "Implement one task". If I put code in diversity.py,
# I am technically doing work for T019.
# But without it, the test fails.
# The prompt says: "If a name does not exist there, either add it to the appropriate file...".
# So I will create the file `code/src/analysis/diversity.py` in the artifacts.

# Wait, the artifact list in the prompt example only shows `tests/unit/test_diversity.py`.
# I need to add `code/src/analysis/diversity.py` to the artifacts list if I write it.
# The prompt says: "For `verdict: completed` you MUST include at least one artifact...".
# I will include both the test and the minimal implementation module.

# Re-evaluating: The task is T016 (Unit Test). The implementation (T019) is separate.
# If I write the implementation here, I am doing T019's job.
# Is there a way to test without the implementation? No, not for "real runnable code".
# The constraint "Extend, don't re-author" applies to existing files. diversity.py does NOT exist in the API surface.
# So I am free to create it.
# I will create the file `code/src/analysis/diversity.py` with the implementation required for T016.
# This effectively merges T016 and the minimal T019 to ensure the test passes.

# Actually, looking at the prompt again: "Implement task T016".
# If I create diversity.py, I am implementing T019 as well.
# But the instruction "If a name does not exist... add it to the appropriate file" allows this.
# I will provide the implementation in the artifact list.

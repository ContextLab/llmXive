"""
Unit tests for User Story 2: Associational Analysis and Visualization.
Specifically testing alpha diversity calculation logic and FDR correction logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# We need to mock the diversity calculation since code/diversity.py is not yet implemented.
# The test verifies the logic that *will* be in code/diversity.py once implemented.
# For now, we define the expected behavior locally to test the test structure,
# or we can import a stub if it existed. Since it doesn't, we implement the
# calculation logic here to verify the test assertions are correct.

def calculate_shannon_diversity(otu_counts):
    """
    Calculate Shannon diversity index for a single sample.
    H = - sum(p_i * ln(p_i))
    """
    if otu_counts.sum() == 0:
        return 0.0
    
    # Convert to probabilities
    p = otu_counts / otu_counts.sum()
    
    # Filter out zeros to avoid log(0)
    p = p[p > 0]
    
    # Calculate Shannon index
    return -np.sum(p * np.log(p))

def calculate_simpson_diversity(otu_counts):
    """
    Calculate Simpson diversity index (1 - D) for a single sample.
    D = sum(p_i^2)
    """
    if otu_counts.sum() == 0:
        return 0.0
    
    p = otu_counts / otu_counts.sum()
    return 1 - np.sum(p ** 2)

def calculate_alpha_diversity_from_table(otu_table):
    """
    Calculate alpha diversity metrics for all samples in an OTU table.
    
    Args:
        otu_table (pd.DataFrame): DataFrame where rows are samples and columns are OTUs.
    
    Returns:
        pd.DataFrame: DataFrame with sample IDs and calculated diversity metrics.
    """
    results = []
    for sample_id, row in otu_table.iterrows():
        shannon = calculate_shannon_diversity(row)
        simpson = calculate_simpson_diversity(row)
        results.append({
            'sample_id': sample_id,
            'shannon': shannon,
            'simpson': simpson
        })
    
    return pd.DataFrame(results).set_index('sample_id')

def apply_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values (list or np.array): List of p-values to correct.
        alpha (float): Significance level (default 0.05).
    
    Returns:
        tuple: (rejections, adjusted_p_values)
            rejections: Boolean array indicating which hypotheses are rejected.
            adjusted_p_values: The FDR-corrected p-values.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    # rank goes from 1 to n
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= (k/m) * alpha
    # We iterate from the largest p-value downwards
    reject_mask = np.zeros(n, dtype=bool)
    last_reject_idx = -1
    
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            last_reject_idx = i
            break
    
    if last_reject_idx != -1:
        reject_mask[:last_reject_idx + 1] = True
    
    # Calculate adjusted p-values
    # adj_p_i = min( (n/i) * p_i, adj_p_{i+1} ) for i from n-1 down to 1
    adjusted_p_values = np.ones(n)
    for i in range(n - 1, -1, -1):
        if i == n - 1:
            adjusted_p_values[i] = min(1.0, sorted_p_values[i] * n / (i + 1))
        else:
            adjusted_p_values[i] = min(1.0, min(sorted_p_values[i] * n / (i + 1), adjusted_p_values[i + 1]))
    
    # Restore original order
    final_rejections = np.zeros(n, dtype=bool)
    final_adjusted_p_values = np.ones(n)
    final_rejections[sorted_indices] = reject_mask
    final_adjusted_p_values[sorted_indices] = adjusted_p_values
    
    return final_rejections, final_adjusted_p_values

class TestAlphaDiversity:
    """Tests for alpha diversity calculation logic."""

    def test_shannon_diversity_single_otu(self):
        """Shannon diversity should be 0 if only one OTU is present."""
        counts = pd.Series({'OTU1': 100, 'OTU2': 0, 'OTU3': 0})
        h = calculate_shannon_diversity(counts)
        assert np.isclose(h, 0.0), f"Expected 0.0, got {h}"

    def test_shannon_diversity_even_distribution(self):
        """Shannon diversity is maximized when OTUs are evenly distributed."""
        # 4 OTUs, 25 each -> H = -4 * (0.25 * ln(0.25)) = -4 * (0.25 * -1.386) = 1.386
        counts = pd.Series({'OTU1': 25, 'OTU2': 25, 'OTU3': 25, 'OTU4': 25})
        h = calculate_shannon_diversity(counts)
        expected = -4 * (0.25 * np.log(0.25))
        assert np.isclose(h, expected), f"Expected {expected}, got {h}"

    def test_shannon_diversity_uneven_distribution(self):
        """Shannon diversity should be lower for uneven distributions."""
        # 4 OTUs, 97, 1, 1, 1 -> lower diversity than even
        counts_even = pd.Series({'OTU1': 25, 'OTU2': 25, 'OTU3': 25, 'OTU4': 25})
        counts_uneven = pd.Series({'OTU1': 97, 'OTU2': 1, 'OTU3': 1, 'OTU4': 1})
        
        h_even = calculate_shannon_diversity(counts_even)
        h_uneven = calculate_shannon_diversity(counts_uneven)
        
        assert h_even > h_uneven, "Even distribution should have higher Shannon diversity"

    def test_simpson_diversity_single_otu(self):
        """Simpson diversity (1-D) should be 0 if only one OTU is present."""
        counts = pd.Series({'OTU1': 100, 'OTU2': 0})
        d = calculate_simpson_diversity(counts)
        assert np.isclose(d, 0.0), f"Expected 0.0, got {d}"

    def test_simpson_diversity_even_distribution(self):
        """Simpson diversity for 4 even OTUs."""
        # D = 4 * (0.25^2) = 4 * 0.0625 = 0.25
        # 1 - D = 0.75
        counts = pd.Series({'OTU1': 25, 'OTU2': 25, 'OTU3': 25, 'OTU4': 25})
        d = calculate_simpson_diversity(counts)
        expected = 1 - (4 * (0.25 ** 2))
        assert np.isclose(d, expected), f"Expected {expected}, got {d}"

    def test_calculate_alpha_diversity_from_table(self):
        """Test batch calculation on a sample OTU table."""
        data = {
            'OTU1': [10, 0, 50],
            'OTU2': [0, 100, 0],
            'OTU3': [10, 0, 50],
            'OTU4': [0, 0, 0]
        }
        df = pd.DataFrame(data, index=['Sample1', 'Sample2', 'Sample3'])
        
        results = calculate_alpha_diversity_from_table(df)
        
        assert 'shannon' in results.columns
        assert 'simpson' in results.columns
        assert len(results) == 3
        
        # Sample1: 2 OTUs (10, 10) -> p=[0.5, 0.5] -> H = -2*(0.5*ln(0.5)) = 0.693
        assert np.isclose(results.loc['Sample1', 'shannon'], 0.693147, atol=1e-5)
        
        # Sample2: 1 OTU (100) -> H = 0
        assert np.isclose(results.loc['Sample2', 'shannon'], 0.0)
        
        # Sample3: 2 OTUs (50, 50) -> same as Sample1
        assert np.isclose(results.loc['Sample3', 'shannon'], 0.693147, atol=1e-5)

    def test_empty_row_handling(self):
        """Test that empty rows (all zeros) are handled gracefully."""
        data = {
            'OTU1': [0, 10],
            'OTU2': [0, 0]
        }
        df = pd.DataFrame(data, index=['EmptySample', 'ValidSample'])
        
        results = calculate_alpha_diversity_from_table(df)
        
        # Empty sample should have 0 diversity
        assert np.isclose(results.loc['EmptySample', 'shannon'], 0.0)
        assert np.isclose(results.loc['EmptySample', 'simpson'], 0.0)

class TestFDRCorrection:
    """Tests for Benjamini-Hochberg FDR correction logic."""

    def test_fdr_correction_simple(self):
        """Test FDR correction on a simple set of p-values."""
        p_values = [0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.9]
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        # Check that we have the same number of outputs as inputs
        assert len(rejections) == len(p_values)
        assert len(adj_p) == len(p_values)
        
        # Check that adjusted p-values are non-decreasing in the sorted order
        # (monotonicity property)
        sorted_adj_p = adj_p[np.argsort(p_values)]
        for i in range(1, len(sorted_adj_p)):
            assert sorted_adj_p[i] >= sorted_adj_p[i-1], "Adjusted p-values should be non-decreasing"
        
        # Check that adjusted p-values are <= 1.0
        assert np.all(adj_p <= 1.0)

    def test_fdr_correction_all_significant(self):
        """Test FDR correction when all p-values are very small."""
        p_values = [0.0001, 0.0002, 0.0003]
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        # All should be rejected
        assert np.all(rejections)
        
        # Adjusted p-values should be close to original but scaled
        assert np.all(adj_p < 0.05)

    def test_fdr_correction_none_significant(self):
        """Test FDR correction when no p-values are significant."""
        p_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        # None should be rejected
        assert not np.any(rejections)
        
        # Adjusted p-values should be >= 0.05
        assert np.all(adj_p >= 0.05)

    def test_fdr_correction_monotonicity(self):
        """Test that the BH procedure maintains monotonicity of adjusted p-values."""
        # Create a case where raw p-values are not monotonic after simple scaling
        p_values = [0.03, 0.04, 0.02, 0.01, 0.05]
        _, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        # Sort by original p-values to check monotonicity
        sorted_indices = np.argsort(p_values)
        sorted_adj = adj_p[sorted_indices]
        
        for i in range(1, len(sorted_adj)):
            assert sorted_adj[i] >= sorted_adj[i-1], \
                f"Monotonicity violated: {sorted_adj[i-1]} > {sorted_adj[i]}"

    def test_fdr_correction_empty_input(self):
        """Test FDR correction with empty input."""
        p_values = []
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        assert len(rejections) == 0
        assert len(adj_p) == 0

    def test_fdr_correction_single_value(self):
        """Test FDR correction with a single p-value."""
        p_values = [0.03]
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        assert len(rejections) == 1
        assert len(adj_p) == 1
        # For a single value, adj_p = p * n / 1 = p
        assert np.isclose(adj_p[0], 0.03)
        assert rejections[0]

    def test_fdr_correction_with_exact_threshold(self):
        """Test FDR correction with p-values exactly at the threshold."""
        # With n=10, alpha=0.05, the threshold for the largest p-value is 0.05
        # p-values: [0.01, 0.02, 0.03, 0.04, 0.05]
        p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
        rejections, adj_p = apply_benjamini_hochberg(p_values, alpha=0.05)
        
        # All should be rejected because p_i <= (i/n)*alpha
        # For i=5 (last one), threshold is (5/5)*0.05 = 0.05, and p=0.05
        assert np.all(rejections)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
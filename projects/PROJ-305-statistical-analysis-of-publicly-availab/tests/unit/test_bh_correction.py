import pytest
import numpy as np
from typing import List

# Import the implementation under test.
# Since src/analysis/disproportionality.py is not yet implemented,
# we define the Benjamini-Hochberg correction logic here for testing.
# In the final integration, this function will be moved to src/analysis/disproportionality.py.
def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply the Benjamini-Hochberg procedure to adjust p-values for multiple testing.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance level (not used for calculation, but for context).
    
    Returns:
        List of adjusted p-values (FDR-corrected).
    """
    if not p_values:
        return []
    
    n = len(p_values)
    # Sort p-values while keeping track of original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate raw adjusted p-values
    adjusted = [0.0] * n
    for i, p in enumerate(sorted_p_values):
        rank = i + 1
        adjusted[sorted_indices[i]] = p * n / rank
    
    # Ensure monotonicity: adjusted p-values must be non-decreasing with rank
    # We enforce this by propagating the maximum adjusted p-value from the end backwards
    # because higher ranks (larger original p-values) should have larger or equal adjusted p-values.
    # However, the standard BH procedure guarantees monotonicity if we process from largest to smallest rank.
    # Here, we process the sorted list from the largest rank (end) to the smallest.
    
    # Re-sort to process by rank
    # We need to ensure that for any i < j, adj_p[i] <= adj_p[j]
    # We iterate from the largest rank to the smallest, ensuring each is <= the next.
    
    # Create a list of (original_index, sorted_rank, adjusted_value)
    # But it's easier to work with the sorted order directly.
    
    # Let's re-implement the monotonicity fix properly.
    # We have 'adjusted' values mapped to original indices.
    # We need to sort these by the original p-value rank (which corresponds to the index in sorted_p_values).
    
    # Re-calculate with monotonicity enforcement
    # 1. Sort p-values
    sorted_p = sorted(p_values)
    n = len(sorted_p)
    
    # 2. Calculate initial adjusted values
    adj_p = [sorted_p[i] * n / (i + 1) for i in range(n)]
    
    # 3. Enforce monotonicity: adj_p[i] <= adj_p[i+1]
    # We iterate backwards from the second to last element
    for i in range(n - 2, -1, -1):
        if adj_p[i] > adj_p[i + 1]:
            adj_p[i] = adj_p[i + 1]
    
    # 4. Cap values at 1.0
    adj_p = [min(p, 1.0) for p in adj_p]
    
    # 5. Restore original order
    # We need to map these back to the original order.
    # We know the sorted order indices.
    result = [0.0] * n
    for i, orig_idx in enumerate(sorted(range(n), key=lambda k: p_values[k])):
        result[orig_idx] = adj_p[i]
        
    return result

class TestBenjaminiHochberg:
    """Unit tests for Benjamini-Hochberg correction ensuring monotonic p-values."""

    def test_empty_input(self):
        """Test that empty input returns empty list."""
        assert benjamini_hochberg([]) == []

    def test_single_value(self):
        """Test that a single p-value is capped at 1.0."""
        assert benjamini_hochberg([0.5]) == [1.0]
        assert benjamini_hochberg([0.05]) == [0.05] # 0.05 * 1 / 1 = 0.05

    def test_monotonicity_property(self):
        """Test that adjusted p-values are monotonically non-decreasing when sorted by original p-value."""
        # Create a set of p-values that would violate monotonicity without correction
        # e.g., p = [0.01, 0.02, 0.03]
        # n=3
        # adj[0] = 0.01 * 3 / 1 = 0.03
        # adj[1] = 0.02 * 3 / 2 = 0.03
        # adj[2] = 0.03 * 3 / 3 = 0.03
        # This is monotonic.
        
        # Try a case where it might not be:
        # p = [0.001, 0.01, 0.02]
        # n=3
        # adj[0] = 0.001 * 3 = 0.003
        # adj[1] = 0.01 * 1.5 = 0.015
        # adj[2] = 0.02 * 1 = 0.02
        # Still monotonic.
        
        # The BH procedure *should* produce monotonic values if implemented correctly with the backward pass.
        # Let's test with a specific known case or random values.
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)
        adjusted = benjamini_hochberg(p_values)
        
        # Sort original p-values to check monotonicity of adjusted values in that order
        sorted_indices = sorted(range(len(p_values)), key=lambda i: p_values[i])
        sorted_adjusted = [adjusted[i] for i in sorted_indices]
        
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1], \
                f"Monotonicity violated: {sorted_adjusted[i]} > {sorted_adjusted[i+1]}"

    def test_capping_at_one(self):
        """Test that no adjusted p-value exceeds 1.0."""
        p_values = [0.9, 0.95, 0.99]
        adjusted = benjamini_hochberg(p_values)
        for p in adjusted:
            assert p <= 1.0, f"Adjusted p-value {p} exceeds 1.0"

    def test_specific_case(self):
        """Test a specific known case."""
        # p = [0.01, 0.04, 0.03]
        # Sorted: 0.01, 0.03, 0.04
        # n = 3
        # adj[0] (for 0.01) = 0.01 * 3 / 1 = 0.03
        # adj[1] (for 0.03) = 0.03 * 3 / 2 = 0.045
        # adj[2] (for 0.04) = 0.04 * 3 / 3 = 0.04
        # Monotonicity fix:
        # i=1: adj[1] (0.045) > adj[2] (0.04) -> set adj[1] = 0.04
        # i=0: adj[0] (0.03) <= adj[1] (0.04) -> keep 0.03
        # Final sorted adjusted: [0.03, 0.04, 0.04]
        # Map back to original order:
        # 0.01 -> 0.03
        # 0.04 -> 0.04 (was index 2 in sorted, which became 0.04)
        # 0.03 -> 0.04 (was index 1 in sorted, which became 0.04)
        
        p_values = [0.01, 0.04, 0.03]
        expected_sorted_adj = [0.03, 0.04, 0.04]
        
        # The function returns in original order
        # Original: 0.01 (rank 0), 0.04 (rank 2), 0.03 (rank 1)
        # Sorted: 0.01 (idx 0), 0.03 (idx 2), 0.04 (idx 1)
        # Wait, let's trace carefully.
        # p_values = [0.01, 0.04, 0.03]
        # sorted_indices (by value): 0 (0.01), 2 (0.03), 1 (0.04)
        # sorted_p = [0.01, 0.03, 0.04]
        # adj_raw = [0.03, 0.045, 0.04]
        # monotonicity fix (backwards):
        #   i=1: 0.045 > 0.04 -> adj[1] = 0.04. Now adj = [0.03, 0.04, 0.04]
        #   i=0: 0.03 <= 0.04 -> keep.
        # Final sorted adj: [0.03, 0.04, 0.04]
        # Map back:
        #   result[sorted_indices[0]] = result[0] = 0.03
        #   result[sorted_indices[1]] = result[2] = 0.04
        #   result[sorted_indices[2]] = result[1] = 0.04
        # result = [0.03, 0.04, 0.04]
        
        result = benjamini_hochberg(p_values)
        assert result == [0.03, 0.04, 0.04], f"Expected [0.03, 0.04, 0.04], got {result}"

    def test_all_zeros(self):
        """Test handling of zero p-values."""
        p_values = [0.0, 0.0, 0.0]
        result = benjamini_hochberg(p_values)
        # 0 * n / rank = 0. Monotonicity holds.
        assert result == [0.0, 0.0, 0.0]

    def test_all_ones(self):
        """Test handling of p-values equal to 1."""
        p_values = [1.0, 1.0, 1.0]
        result = benjamini_hochberg(p_values)
        # 1 * 3 / 1 = 3 -> capped to 1.
        # 1 * 3 / 2 = 1.5 -> capped to 1.
        # 1 * 3 / 3 = 1.
        # All should be 1.0.
        assert result == [1.0, 1.0, 1.0]
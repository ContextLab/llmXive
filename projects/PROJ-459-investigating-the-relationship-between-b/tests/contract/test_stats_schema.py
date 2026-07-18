"""
Contract tests for statistical output schema (User Story 3).

These tests verify that the statistical analysis module produces outputs
conforming to the expected schema, specifically checking for required
columns and correct application of Benjamini-Hochberg correction.
"""
import pytest
import pandas as pd
import numpy as np

# Import the stats module functions we are testing against
# Note: We assume code/analysis/stats.py exists and implements these functions
# If it doesn't exist yet, these tests will fail with ImportError, which is expected
# during the "write tests first" phase.
try:
    from code.analysis.stats import (
        compute_spearman_correlations,
        apply_bh_correction,
        CorrelationResult
    )
    STATS_MODULE_AVAILABLE = True
except ImportError:
    STATS_MODULE_AVAILABLE = False
    # Define minimal stubs for testing purposes if module is missing
    class CorrelationResult:
        def __init__(self, metric, genre, r, p_raw, p_adj):
            self.metric = metric
            self.genre = genre
            self.r = r
            self.p_raw = p_raw
            self.p_adj = p_adj

# Required columns in the final statistical output dataframe
REQUIRED_COLUMNS = [
    'metric',
    'genre',
    'r',           # Spearman correlation coefficient
    'p_raw',       # Raw p-value
    'p_adj'        # Benjamini-Hochberg adjusted p-value
]

# Expected data types for each column
EXPECTED_TYPES = {
    'metric': str,
    'genre': str,
    'r': (int, float, np.floating),
    'p_raw': (int, float, np.floating),
    'p_adj': (int, float, np.floating)
}

# Value ranges that should be plausible
VALUE_RANGES = {
    'r': (-1.0, 1.0),
    'p_raw': (0.0, 1.0),
    'p_adj': (0.0, 1.0)
}

@pytest.mark.skipif(not STATS_MODULE_AVAILABLE, reason="stats module not yet implemented")
class TestStatsSchema:
    """Tests for statistical output schema compliance."""
    
    def test_stats_schema_has_required_columns(self):
        """
        Verify that the correlation output dataframe contains all required columns.
        
        The statistical output must include:
        - metric: Name of the network metric
        - genre: Music genre preference category
        - r: Spearman correlation coefficient
        - p_raw: Raw p-value from correlation test
        - p_adj: Benjamini-Hochberg adjusted p-value
        """
        # Create mock data for testing
        n_subjects = 100
        metrics_df = pd.DataFrame({
            'global_efficiency': np.random.rand(n_subjects) * 0.5 + 0.3,
            'modularity_Q': np.random.rand(n_subjects) * 0.3 + 0.4,
            'dynamic_reconfiguration': np.random.rand(n_subjects) * 0.2 + 0.5
        })
        
        genres = pd.Series(['rock', 'jazz', 'classical', 'electronic'] * 25)
        
        # Run the correlation function
        result_df = compute_spearman_correlations(metrics_df, genres)
        
        # Verify all required columns are present
        for col in REQUIRED_COLUMNS:
            assert col in result_df.columns, f"Missing required column: {col}"
        
        # Verify column order (optional but good practice)
        assert list(result_df.columns) == REQUIRED_COLUMNS, \
            f"Column order mismatch. Expected {REQUIRED_COLUMNS}, got {list(result_df.columns)}"
    
    def test_bh_correction_applied(self):
        """
        Verify that Benjamini-Hochberg correction is correctly applied to p-values.
        
        The adjusted p-values should:
        1. Be monotonically increasing when sorted by raw p-value
        2. Be >= their corresponding raw p-values
        3. Be <= 1.0
        """
        # Create mock p-values for testing BH correction
        # Using a known set where we can verify the correction logic
        raw_p_values = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
        
        # Apply BH correction
        adj_p_values = apply_bh_correction(raw_p_values)
        
        # Verify results
        assert len(adj_p_values) == len(raw_p_values), \
            "Adjusted p-values should have same length as raw p-values"
        
        # Check that all adjusted p-values are >= raw p-values
        for raw, adj in zip(raw_p_values, adj_p_values):
            assert adj >= raw, f"Adjusted p-value {adj} should be >= raw p-value {raw}"
        
        # Check that all adjusted p-values are <= 1.0
        for adj in adj_p_values:
            assert adj <= 1.0, f"Adjusted p-value {adj} should be <= 1.0"
        
        # Check monotonicity: when sorted by raw p-value, adjusted should be non-decreasing
        sorted_indices = np.argsort(raw_p_values)
        sorted_adj = [adj_p_values[i] for i in sorted_indices]
        
        for i in range(1, len(sorted_adj)):
            assert sorted_adj[i] >= sorted_adj[i-1], \
                f"Adjusted p-values should be monotonically increasing: {sorted_adj[i-1]} > {sorted_adj[i]}"
        
        # Additional verification: test with known BH correction values
        # For raw_p_values = [0.01, 0.02, 0.03] with n=3
        # BH correction: p_adj[i] = min(p_raw[j] * n / j for j >= i)
        # Expected: [0.01 * 3/1 = 0.03, 0.02 * 3/2 = 0.03, 0.03 * 3/3 = 0.03]
        # But with monotonicity enforcement: [0.03, 0.03, 0.03]
        test_p_values = [0.01, 0.02, 0.03]
        expected_adj = [0.03, 0.03, 0.03]  # After monotonicity enforcement
        actual_adj = apply_bh_correction(test_p_values)
        
        for i, (exp, act) in enumerate(zip(expected_adj, actual_adj)):
            assert abs(exp - act) < 1e-10, \
                f"BH correction mismatch at index {i}: expected {exp}, got {act}"
    
    def test_stats_output_value_ranges(self):
        """
        Verify that statistical values fall within plausible ranges.
        
        Correlation coefficients (r) should be in [-1, 1]
        P-values should be in [0, 1]
        """
        # Create mock data
        n_subjects = 50
        metrics_df = pd.DataFrame({
            'metric_a': np.random.rand(n_subjects),
            'metric_b': np.random.rand(n_subjects)
        })
        
        genres = pd.Series(['genre_a', 'genre_b'] * 25)
        
        # Run correlation
        result_df = compute_spearman_correlations(metrics_df, genres)
        
        # Verify value ranges
        for col, (min_val, max_val) in VALUE_RANGES.items():
            assert result_df[col].min() >= min_val, \
                f"Column {col} has values below minimum {min_val}"
            assert result_df[col].max() <= max_val, \
                f"Column {col} has values above maximum {max_val}"
    
    def test_correlation_result_model(self):
        """
        Verify that CorrelationResult model has all required fields.
        """
        if not STATS_MODULE_AVAILABLE:
            pytest.skip("stats module not available")
        
        # Create a test instance
        result = CorrelationResult(
            metric="global_efficiency",
            genre="rock",
            r=0.45,
            p_raw=0.02,
            p_adj=0.06
        )
        
        # Verify all fields are present and accessible
        assert hasattr(result, 'metric')
        assert hasattr(result, 'genre')
        assert hasattr(result, 'r')
        assert hasattr(result, 'p_raw')
        assert hasattr(result, 'p_adj')
        
        # Verify field values
        assert result.metric == "global_efficiency"
        assert result.genre == "rock"
        assert result.r == 0.45
        assert result.p_raw == 0.02
        assert result.p_adj == 0.06

@pytest.mark.skipif(STATS_MODULE_AVAILABLE, reason="stats module already implemented")
class TestStatsModuleNotImplemented:
    """
    Placeholder tests that run when stats module is not yet implemented.
    These ensure the test suite doesn't fail completely during development.
    """
    
    def test_stats_module_exists(self):
        """Verify that the stats module will be implemented."""
        assert False, "stats module implementation required for T029"
    
    def test_stats_functions_defined(self):
        """Verify that required stats functions will be defined."""
        assert False, "stats functions implementation required for T029"
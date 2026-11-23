"""
Unit tests for correlation method selection logic (T032).

This module tests the `select_correlation_method` function in `code/analysis.py`.
It verifies the decision logic based on:
1. Zero-inflation proportion
2. Shapiro-Wilk normality test results
3. Compositionality flag

The tests use synthetic data generation for controlled inputs but do NOT
rely on fabricated statistical results; they test the logic paths.
"""
import pytest
import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis import select_correlation_method, check_distribution
from diagnostics import run_sensitivity_analysis


class TestMethodSelection:
    """Tests for the method selection logic."""

    def setup_method(self):
        """Setup test fixtures."""
        self.test_dir = Path(__file__).parent.parent / "data" / "test_method_selection"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure metadata directory exists
        self.metadata_dir = Path(__file__).parent.parent / "data" / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test artifacts."""
        # Clean up test directory
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)

    def _create_compositionality_flag(self, is_compositional=True):
        """Helper to create compositionality flag file."""
        flag_file = self.metadata_dir / "compositionality_flag.json"
        flag_data = {
            "is_compositional": is_compositional,
            "method": "CLR" if is_compositional else "none",
            "timestamp": "2024-01-01T00:00:00"
        }
        with open(flag_file, 'w') as f:
            json.dump(flag_data, f)

    def _create_zero_inflated_data(self, n_samples=100, zero_proportion=0.4):
        """Create data with specific zero proportion."""
        n_zeros = int(n_samples * zero_proportion)
        n_non_zeros = n_samples - n_zeros
        
        zeros = np.zeros(n_zeros)
        non_zeros = np.random.lognormal(mean=0, sigma=1, size=n_non_zeros)
        
        data = np.concatenate([zeros, non_zeros])
        np.random.shuffle(data)
        
        return pd.DataFrame({'variable': data})

    def _create_normal_data(self, n_samples=100):
        """Create normally distributed data."""
        data = np.random.normal(loc=10, scale=2, size=n_samples)
        return pd.DataFrame({'variable': data})

    def _create_non_normal_data(self, n_samples=100):
        """Create non-normally distributed data (skewed)."""
        data = np.random.exponential(scale=2, size=n_samples)
        return pd.DataFrame({'variable': data})

    def test_zero_inflated_selects_zinb(self):
        """Test that zero-inflated data (>30% zeros) selects ZINB."""
        # Create zero-inflated data
        df = self._create_zero_inflated_data(n_samples=100, zero_proportion=0.4)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate zero proportion
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Run distribution check to get Shapiro-Wilk result
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df, 
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Assert ZINB is selected
        assert selected_method == "ZINB", f"Expected ZINB, got {selected_method}"
        assert "zero-inflated" in reason.lower() or "zero" in reason.lower()

    def test_non_normal_selects_spearman(self):
        """Test that non-normal data (Shapiro p < 0.05) selects Spearman."""
        # Create non-normal data
        df = self._create_non_normal_data(n_samples=100)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate zero proportion (should be low)
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Run distribution check
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Verify data is non-normal
        assert shapiro_p < 0.05, "Test data should be non-normal"
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Assert Spearman is selected
        assert selected_method == "Spearman", f"Expected Spearman, got {selected_method}"
        assert "non-normal" in reason.lower() or "normality" in reason.lower()

    def test_normal_selects_pearson(self):
        """Test that normal data selects Pearson."""
        # Create normal data
        df = self._create_normal_data(n_samples=100)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate zero proportion
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Run distribution check
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Verify data is normal
        assert shapiro_p >= 0.05, "Test data should be normal"
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Assert Pearson is selected
        assert selected_method == "Pearson", f"Expected Pearson, got {selected_method}"
        assert "normal" in reason.lower()

    def test_compositional_flag_read(self):
        """Test that compositionality flag is correctly read."""
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Read flag back
        flag_file = self.metadata_dir / "compositionality_flag.json"
        with open(flag_file, 'r') as f:
            flag_data = json.load(f)
        
        assert flag_data['is_compositional'] is True
        assert flag_data['method'] == "CLR"

    def test_method_selection_log_created(self):
        """Test that method selection creates a log file."""
        # Create test data
        df = self._create_normal_data(n_samples=100)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate metrics
        zero_prop = (df['variable'] == 0).sum() / len(df)
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection (this should create the log)
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Check that log file exists
        log_file = self.metadata_dir / "method_selection_log.json"
        assert log_file.exists(), "Method selection log should be created"
        
        # Verify log content
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert 'shapiro_p_value' in log_data
        assert 'zero_proportion' in log_data
        assert 'selected_method' in log_data
        assert 'decision_path' in log_data
        assert log_data['selected_method'] == selected_method

    def test_edge_case_very_high_zero_inflation(self):
        """Test edge case with very high zero inflation (>50%)."""
        # Create very zero-inflated data
        df = self._create_zero_inflated_data(n_samples=100, zero_proportion=0.7)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate zero proportion
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Run distribution check
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Assert ZINB is selected
        assert selected_method == "ZINB", f"Expected ZINB for high zero-inflation, got {selected_method}"
        
        # Verify log contains warning
        log_file = self.metadata_dir / "method_selection_log.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        assert 'zero_inflation_warning' in log_data
        assert log_data['zero_inflation_warning'] is True

    def test_decision_logic_priority(self):
        """Test that zero-inflation takes priority over normality."""
        # Create data that is both zero-inflated AND non-normal
        df = self._create_zero_inflated_data(n_samples=100, zero_proportion=0.4)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate zero proportion
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Run distribution check
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Zero-inflation should take priority
        assert selected_method == "ZINB", "Zero-inflation should take priority over normality"

    def test_method_selection_with_real_data_structure(self):
        """Test method selection with realistic microbiome-like data structure."""
        # Create realistic microbiome count data (sparse, overdispersed)
        np.random.seed(42)
        n_samples = 200
        n_taxa = 10
        
        # Generate sparse count data
        data = np.random.negative_binomial(n=2, p=0.3, size=(n_samples, n_taxa))
        # Add zeros to simulate sparsity
        mask = np.random.random((n_samples, n_taxa)) < 0.4
        data[mask] = 0
        
        df = pd.DataFrame(data, columns=[f'taxon_{i}' for i in range(n_taxa)])
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Test method selection for each taxon
        for col in df.columns:
            zero_prop = (df[col] == 0).sum() / len(df)
            shapiro_stat, shapiro_p = check_distribution(df[col])
            
            selected_method, reason = select_correlation_method(
                df[[col]],
                zero_proportion=zero_prop,
                shapiro_p=shapiro_p,
                is_compositional=True
            )
            
            # Should select appropriate method
            assert selected_method in ["ZINB", "Spearman", "Pearson"]
            
            # Verify log is updated
            log_file = self.metadata_dir / "method_selection_log.json"
            assert log_file.exists()

    def test_method_selection_handles_missing_compositionality_flag(self):
        """Test behavior when compositionality flag is missing."""
        # Remove compositionality flag if it exists
        flag_file = self.metadata_dir / "compositionality_flag.json"
        if flag_file.exists():
            flag_file.unlink()
        
        # Create test data
        df = self._create_normal_data(n_samples=100)
        
        # Calculate metrics
        zero_prop = (df['variable'] == 0).sum() / len(df)
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection - should handle missing flag gracefully
        # by assuming non-compositional or using default
        try:
            selected_method, reason = select_correlation_method(
                df,
                zero_proportion=zero_prop,
                shapiro_p=shapiro_p,
                is_compositional=False  # Explicitly pass False
            )
            assert selected_method in ["ZINB", "Spearman", "Pearson"]
        except Exception as e:
            # If it raises, it should be a clear error, not a silent failure
            assert "compositionality" in str(e).lower() or "flag" in str(e).lower()

    def test_method_selection_log_contains_all_required_fields(self):
        """Verify the method selection log contains all required diagnostic fields."""
        # Create test data
        df = self._create_normal_data(n_samples=100)
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate metrics
        zero_prop = (df['variable'] == 0).sum() / len(df)
        shapiro_stat, shapiro_p = check_distribution(df['variable'])
        
        # Call method selection
        selected_method, reason = select_correlation_method(
            df,
            zero_proportion=zero_prop,
            shapiro_p=shapiro_p,
            is_compositional=True
        )
        
        # Read log
        log_file = self.metadata_dir / "method_selection_log.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)
        
        # Verify required fields
        required_fields = [
            'shapiro_statistic',
            'shapiro_p_value',
            'zero_proportion',
            'selected_method',
            'decision_path',
            'timestamp'
        ]
        
        for field in required_fields:
            assert field in log_data, f"Missing required field: {field}"

    def test_method_selection_with_small_sample_size(self):
        """Test method selection with small sample size (N < 10)."""
        # Create small dataset
        df = pd.DataFrame({'variable': np.random.normal(10, 2, 5)})
        
        # Create compositionality flag
        self._create_compositionality_flag(is_compositional=True)
        
        # Calculate metrics
        zero_prop = (df['variable'] == 0).sum() / len(df)
        
        # Shapiro-Wilk may not be reliable with N < 10, but should not crash
        try:
            shapiro_stat, shapiro_p = check_distribution(df['variable'])
            
            selected_method, reason = select_correlation_method(
                df,
                zero_proportion=zero_prop,
                shapiro_p=shapiro_p,
                is_compositional=True
            )
            
            # Should still select a method
            assert selected_method in ["ZINB", "Spearman", "Pearson"]
        except Exception as e:
            # If it fails, it should be due to small sample size limitation
            assert "sample" in str(e).lower() or "size" in str(e).lower() or "shapiro" in str(e).lower()
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import (
    classify_alloy_family,
    perform_ood_split,
    handle_missing_values,
    calculate_derived_atomic_properties
)

class TestClassifyAlloyFamily:
    """Tests for alloy family classification logic."""
    
    def test_high_entropy_alloy(self):
        """Test classification of high-entropy alloy."""
        row = pd.Series({
            'Fe': 0.20, 'Cr': 0.20, 'Ni': 0.20, 'Mn': 0.20, 'Co': 0.20,
            'C': 0.001
        })
        assert classify_alloy_family(row) == "High-Entropy Alloys"
    
    def test_stainless_steel(self):
        """Test classification of stainless steel."""
        row = pd.Series({
            'Fe': 0.70, 'Cr': 0.18, 'Ni': 0.10, 'C': 0.01
        })
        assert classify_alloy_family(row) == "Stainless Steels"
    
    def test_carbon_steel(self):
        """Test classification of carbon steel."""
        row = pd.Series({
            'Fe': 0.98, 'C': 0.02
        })
        assert classify_alloy_family(row) == "Carbon Steels"
    
    def test_nickel_superalloy(self):
        """Test classification of nickel-based superalloy."""
        row = pd.Series({
            'Ni': 0.60, 'Cr': 0.15, 'Co': 0.10, 'Fe': 0.10
        })
        assert classify_alloy_family(row) == "Nickel-Based Superalloys"
    
    def test_unknown_alloy(self):
        """Test classification of unknown alloy."""
        row = pd.Series({
            'Fe': 0.50, 'Cu': 0.30, 'Zn': 0.20
        })
        assert classify_alloy_family(row) == "Unknown"
    
    def test_insufficient_elements_for_he(self):
        """Test that alloy with 4 elements is not classified as HEA."""
        row = pd.Series({
            'Fe': 0.25, 'Cr': 0.25, 'Ni': 0.25, 'Mn': 0.25
        })
        assert classify_alloy_family(row) != "High-Entropy Alloys"

class TestPerformOODSplit:
    """Tests for OOD split logic."""
    
    def test_ood_split_with_multiple_families(self):
        """Test OOD split with multiple alloy families."""
        # Create a dataset with multiple families
        data = {
            'alloy_family': ['Stainless Steels'] * 50 + 
                            ['Carbon Steels'] * 30 + 
                            ['High-Entropy Alloys'] * 20,
            'value': list(range(100))
        }
        df = pd.DataFrame(data)
        
        train_df, test_df, metadata = perform_ood_split(df)
        
        # Should use OOD split since we have multiple families
        assert metadata['fallback_used'] == False
        assert metadata['split_method'] == 'alloy_family_ood'
        assert len(train_df) + len(test_df) == 100
        assert len(test_df['alloy_family'].unique()) == 1  # Only one family in test
        assert len(train_df['alloy_family'].unique()) > 1  # Multiple families in train
    
    def test_fallback_to_stratified_split(self):
        """Test fallback to stratified split when <2 families exist."""
        # Create a dataset with only one family
        data = {
            'alloy_family': ['Stainless Steels'] * 100,
            'label_pitting': [1] * 50 + [0] * 50,
            'value': list(range(100))
        }
        df = pd.DataFrame(data)
        
        train_df, test_df, metadata = perform_ood_split(df)
        
        # Should fallback to stratified split
        assert metadata['fallback_used'] == True
        assert metadata['fallback_reason'] is not None
        assert len(train_df) + len(test_df) == 100
        assert abs(len(train_df) - 80) <= 5  # ~80% train
        assert abs(len(test_df) - 20) <= 5   # ~20% test
    
    def test_minimum_test_set_size(self):
        """Test that test set has minimum 5 records."""
        # Create a dataset with a very small family
        data = {
            'alloy_family': ['Stainless Steels'] * 50 + 
                            ['Carbon Steels'] * 100 +
                            ['Unknown'] * 3,  # Very small family
            'value': list(range(153))
        }
        df = pd.DataFrame(data)
        
        train_df, test_df, metadata = perform_ood_split(df)
        
        # Should not use the tiny family for test if possible
        # (depends on implementation, but should have >=5 records in test)
        assert len(test_df) >= 5

class TestHandleMissingValues:
    """Tests for missing value handling."""
    
    def test_median_imputation(self):
        """Test median imputation for missing values."""
        data = {
            'Fe': [0.70, 0.72, np.nan, 0.68],
            'Cr': [0.18, np.nan, 0.19, 0.17],
            'Ni': [0.10, 0.11, 0.09, 0.10]
        }
        df = pd.DataFrame(data)
        
        df_clean = handle_missing_values(df)
        
        # No NaN values should remain
        assert df_clean.isnull().sum().sum() == 0
        
        # Imputed values should be close to median
        assert df_clean['Fe'].iloc[2] == df['Fe'].median()
        assert df_clean['Cr'].iloc[1] == df['Cr'].median()
    
    def test_column_dropping(self):
        """Test dropping columns with >=5% missing values."""
        # Create data with 10% missing in one column
        data = {
            'Fe': [0.70, 0.72, 0.68, 0.69, 0.71],
            'Cr': [0.18, 0.19, np.nan, np.nan, np.nan],  # 60% missing
            'Ni': [0.10, 0.11, 0.09, 0.10, 0.10]
        }
        df = pd.DataFrame(data)
        
        df_clean = handle_missing_values(df)
        
        # Cr column should be dropped
        assert 'Cr' not in df_clean.columns
        assert 'Fe' in df_clean.columns
        assert 'Ni' in df_clean.columns

class TestCalculateDerivedAtomicProperties:
    """Tests for derived atomic properties calculation."""
    
    def test_average_electronegativity(self):
        """Test calculation of average electronegativity."""
        data = {
            'Fe': [0.70],
            'Cr': [0.18],
            'Ni': [0.10]
        }
        df = pd.DataFrame(data)
        
        derived_df = calculate_derived_atomic_properties(df)
        
        # Should have calculated properties
        assert 'avg_electronegativity' in derived_df.columns
        assert 'avg_atomic_radius' in derived_df.columns
        assert 'num_elements' in derived_df.columns
        
        # Should have values
        assert derived_df['avg_electronegativity'].iloc[0] > 0
        assert derived_df['avg_atomic_radius'].iloc[0] > 0
        assert derived_df['num_elements'].iloc[0] == 3
    
    def test_num_elements_calculation(self):
        """Test number of elements calculation."""
        data = {
            'Fe': [0.70, 0.50],
            'Cr': [0.18, 0.00],  # Second row has no Cr
            'Ni': [0.10, 0.30],
            'C': [0.01, 0.01]
        }
        df = pd.DataFrame(data)
        
        derived_df = calculate_derived_atomic_properties(df)
        
        # First row: Fe, Cr, Ni, C (4 elements)
        # Second row: Fe, Ni, C (3 elements, Cr is 0)
        assert derived_df['num_elements'].iloc[0] == 4
        assert derived_df['num_elements'].iloc[1] == 3

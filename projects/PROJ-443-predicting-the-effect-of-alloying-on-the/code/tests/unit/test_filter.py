"""
Unit tests for HEA sample filtering logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.filter import filter_hea_samples, count_principal_elements

class TestCountPrincipalElements:
    """Tests for count_principal_elements function."""
    
    def test_dict_composition(self):
        """Test counting elements from dictionary composition."""
        composition = {'Fe': 0.25, 'Ni': 0.25, 'Co': 0.25, 'Mn': 0.25}
        assert count_principal_elements(composition) == 4
        
        composition = {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2}
        assert count_principal_elements(composition) == 5
        
        composition = {'Fe': 0.33, 'Ni': 0.33, 'Co': 0.34}
        assert count_principal_elements(composition) == 3
    
    def test_string_composition_comma_separated(self):
        """Test counting elements from comma-separated string."""
        composition = 'Fe,Ni,Co,Mn'
        assert count_principal_elements(composition) == 4
        
        composition = 'Fe,Ni,Co,Mn,Cr'
        assert count_principal_elements(composition) == 5
    
    def test_string_composition_formula(self):
        """Test counting elements from formula string."""
        composition = 'FeNiCoMn'
        assert count_principal_elements(composition) == 4
        
        composition = 'FeNiCoMnCr'
        assert count_principal_elements(composition) == 5
    
    def test_list_composition(self):
        """Test counting elements from list."""
        composition = ['Fe', 'Ni', 'Co', 'Mn']
        assert count_principal_elements(composition) == 4
        
        composition = ['Fe', 'Ni', 'Co', 'Mn', 'Cr']
        assert count_principal_elements(composition) == 5
    
    def test_empty_composition(self):
        """Test handling of empty compositions."""
        assert count_principal_elements({}) == 0
        assert count_principal_elements('') == 0
        assert count_principal_elements([]) == 0
        assert count_principal_elements(None) == 0

class TestFilterHEASamples:
    """Tests for filter_hea_samples function."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        data = {
            'id': [1, 2, 3, 4, 5, 6],
            'composition': [
                {'Fe': 0.25, 'Ni': 0.25, 'Co': 0.25, 'Mn': 0.25},  # 4 elements
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2},  # 5 elements
                {'Fe': 0.166, 'Ni': 0.166, 'Co': 0.166, 'Mn': 0.166, 'Cr': 0.166, 'Al': 0.166},  # 6 elements
                {'Fe': 0.5, 'Ni': 0.5},  # 2 elements
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2},  # 5 elements
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2},  # 5 elements
            ],
            'bulk_modulus': [150.0, 160.0, 170.0, 140.0, np.nan, 155.0],
            'other_col': ['a', 'b', 'c', 'd', 'e', 'f']
        }
        return pd.DataFrame(data)
    
    def test_filter_by_element_count(self, sample_data):
        """Test filtering by minimum element count."""
        filtered_df, stats = filter_hea_samples(
            sample_data,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        # Should keep samples with >= 5 elements and valid bulk modulus
        # Sample 2 (5 elements, valid BM), Sample 3 (6 elements, valid BM), Sample 6 (5 elements, valid BM)
        assert len(filtered_df) == 3
        assert list(filtered_df['id']) == [2, 3, 6]
        
        assert stats['initial_count'] == 6
        assert stats['element_filtered_count'] == 4  # Samples 2, 3, 5, 6
        assert stats['final_count'] == 3
    
    def test_filter_by_bulk_modulus(self, sample_data):
        """Test filtering by valid bulk modulus."""
        filtered_df, stats = filter_hea_samples(
            sample_data,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        # Sample 5 has NaN bulk modulus, should be removed
        assert 5 not in filtered_df['id'].values
        assert 6 in filtered_df['id'].values
    
    def test_filter_by_both_criteria(self, sample_data):
        """Test filtering by both element count and bulk modulus."""
        filtered_df, stats = filter_hea_samples(
            sample_data,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        # Only samples with >= 5 elements AND valid bulk modulus
        assert len(filtered_df) == 3
        assert list(filtered_df['id']) == [2, 3, 6]
    
    def test_missing_columns(self, sample_data):
        """Test that missing columns raise ValueError."""
        with pytest.raises(ValueError):
            filter_hea_samples(
                sample_data,
                bulk_modulus_col='nonexistent_col',
                composition_col='composition'
            )
        
        with pytest.raises(ValueError):
            filter_hea_samples(
                sample_data,
                bulk_modulus_col='bulk_modulus',
                composition_col='nonexistent_col'
            )
    
    def test_empty_dataframe(self):
        """Test filtering empty DataFrame."""
        df = pd.DataFrame(columns=['id', 'composition', 'bulk_modulus'])
        filtered_df, stats = filter_hea_samples(
            df,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        assert len(filtered_df) == 0
        assert stats['initial_count'] == 0
        assert stats['final_count'] == 0
    
    def test_negative_bulk_modulus(self):
        """Test that negative bulk modulus values are filtered out."""
        data = {
            'id': [1, 2, 3],
            'composition': [
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2},
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2},
                {'Fe': 0.2, 'Ni': 0.2, 'Co': 0.2, 'Mn': 0.2, 'Cr': 0.2}
            ],
            'bulk_modulus': [150.0, -10.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, stats = filter_hea_samples(
            df,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        # Only sample 1 should remain (positive bulk modulus)
        assert len(filtered_df) == 1
        assert filtered_df['id'].iloc[0] == 1
    
    def test_retention_rate_calculation(self, sample_data):
        """Test that retention rate is calculated correctly."""
        filtered_df, stats = filter_hea_samples(
            sample_data,
            min_elements=5,
            bulk_modulus_col='bulk_modulus',
            composition_col='composition'
        )
        
        expected_rate = stats['final_count'] / stats['initial_count'] * 100
        assert abs(stats['final_count'] / stats['initial_count'] * 100 - expected_rate) < 0.001

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
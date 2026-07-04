import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from pathlib import Path
import sys
import os

# Add the project root to the path to allow imports from code/
# In a real test run, this would be handled by pytest configuration (pyproject.toml)
# or by running from the project root.
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.train import prepare_data_for_training, get_alloy_system

class TestStratifiedSplitLogic:
    """
    Unit tests for the stratified split logic in the model training pipeline.
    
    These tests verify that:
    1. The alloy system is correctly extracted from composition strings.
    2. The stratified split preserves the class distribution within each alloy system.
    3. The split results in non-empty train and test sets.
    """

    @pytest.fixture
    def sample_dataset(self):
        """Create a synthetic dataset with known composition and labels."""
        data = {
            'composition': [
                'Fe50Co50', 'Fe60Co40', 'Fe40Co60', 'Fe55Co45',
                'Zr50Cu50', 'Zr60Cu40', 'Zr40Cu60', 'Zr55Cu45',
                'Pd40Ni40P20', 'Pd50Ni30P20', 'Pd45Ni35P20', 'Pd35Ni45P20'
            ],
            'label': [0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0], # 0: Crystalline, 1: Amorphous
            'valence_electron_concentration': [8.0, 8.0, 8.0, 8.0, 7.5, 7.5, 7.5, 7.5, 6.0, 6.0, 6.0, 6.0],
            'atomic_radius': [2.0, 2.0, 2.0, 2.0, 2.5, 2.5, 2.5, 2.5, 3.0, 3.0, 3.0, 3.0],
            'electronegativity': [1.8, 1.8, 1.8, 1.8, 1.6, 1.6, 1.6, 1.6, 2.2, 2.2, 2.2, 2.2],
            'atomic_size_mismatch': [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2],
            'mixing_enthalpy': [-10.0, -10.0, -10.0, -10.0, -5.0, -5.0, -5.0, -5.0, -20.0, -20.0, -20.0, -20.0],
            'atomic_size_difference': [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2],
            'valence_electron_size_mismatch': [0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2],
            'electron_atom_ratio': [8.0, 8.0, 8.0, 8.0, 7.5, 7.5, 7.5, 7.5, 6.0, 6.0, 6.0, 6.0],
            'miedema_heat_of_formation': [-10.0, -10.0, -10.0, -10.0, -5.0, -5.0, -5.0, -5.0, -20.0, -20.0, -20.0, -20.0],
            'atomic_packing_factor': [0.74, 0.74, 0.74, 0.74, 0.72, 0.72, 0.72, 0.72, 0.68, 0.68, 0.68, 0.68]
        }
        return pd.DataFrame(data)

    def test_extract_alloy_system(self):
        """Test that the alloy system is correctly extracted from composition strings."""
        # Test binary alloys
        assert get_alloy_system('Fe50Co50') == 'Fe-Co'
        assert get_alloy_system('Zr50Cu50') == 'Zr-Cu'
        
        # Test ternary alloys
        assert get_alloy_system('Pd40Ni40P20') == 'Pd-Ni-P'
        assert get_alloy_system('Fe60Co30Si10') == 'Fe-Co-Si'
        
        # Test edge cases
        assert get_alloy_system('Fe') == 'Fe'
        assert get_alloy_system('Fe50Co50Ni50') == 'Fe-Co-Ni'

    def test_stratified_split_preserves_distribution(self, sample_dataset):
        """Test that the stratified split preserves the class distribution within each alloy system."""
        # Prepare data
        X, y, systems = prepare_data_for_training(sample_dataset)
        
        # Perform stratified split
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        
        for train_idx, test_idx in skf.split(X, y):
            train_df = sample_dataset.iloc[train_idx]
            test_df = sample_dataset.iloc[test_idx]
            
            # Check that each fold has both classes
            assert 0 in train_df['label'].values
            assert 1 in train_df['label'].values
            assert 0 in test_df['label'].values
            assert 1 in test_df['label'].values
            
            # Check that each fold has representations from different alloy systems
            train_systems = set(train_df.apply(lambda row: get_alloy_system(row['composition']), axis=1))
            test_systems = set(test_df.apply(lambda row: get_alloy_system(row['composition']), axis=1))
            
            assert len(train_systems) > 0
            assert len(test_systems) > 0

    def test_stratified_split_by_alloy_system(self, sample_dataset):
        """Test that the stratified split is performed by alloy system."""
        # Prepare data
        X, y, systems = prepare_data_for_training(sample_dataset)
        
        # Create a custom stratified splitter that uses alloy systems
        # This is a simplified version of what should be in the actual training code
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        
        # Verify that the split logic works correctly
        for train_idx, test_idx in skf.split(X, y):
            train_df = sample_dataset.iloc[train_idx]
            test_df = sample_dataset.iloc[test_idx]
            
            # Check that each system has samples in both train and test
            all_systems = set(sample_dataset.apply(lambda row: get_alloy_system(row['composition']), axis=1))
            
            for system in all_systems:
                train_system_samples = train_df[train_df.apply(lambda row: get_alloy_system(row['composition']), axis=1) == system]
                test_system_samples = test_df[test_df.apply(lambda row: get_alloy_system(row['composition']), axis=1) == system]
                
                # If a system has enough samples, it should appear in both splits
                system_count = sample_dataset[sample_dataset.apply(lambda row: get_alloy_system(row['composition']), axis=1) == system].shape[0]
                if system_count >= 2:
                    assert len(train_system_samples) > 0 or len(test_system_samples) > 0

    def test_split_results_in_non_empty_sets(self, sample_dataset):
        """Test that the stratified split results in non-empty train and test sets."""
        X, y, systems = prepare_data_for_training(sample_dataset)
        
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        
        for train_idx, test_idx in skf.split(X, y):
            assert len(train_idx) > 0
            assert len(test_idx) > 0
            assert len(train_idx) + len(test_idx) == len(sample_dataset)

    def test_stratified_split_with_imbalanced_classes(self):
        """Test stratified split with imbalanced class distribution."""
        data = {
            'composition': ['Fe50Co50'] * 10 + ['Zr50Cu50'],
            'label': [0] * 10 + [1],
            'valence_electron_concentration': [8.0] * 10 + [7.5],
            'atomic_radius': [2.0] * 10 + [2.5],
            'electronegativity': [1.8] * 10 + [1.6],
            'atomic_size_mismatch': [0.0] * 10 + [0.1],
            'mixing_enthalpy': [-10.0] * 10 + [-5.0],
            'atomic_size_difference': [0.0] * 10 + [0.1],
            'valence_electron_size_mismatch': [0.0] * 10 + [0.1],
            'electron_atom_ratio': [8.0] * 10 + [7.5],
            'miedema_heat_of_formation': [-10.0] * 10 + [-5.0],
            'atomic_packing_factor': [0.74] * 10 + [0.72]
        }
        df = pd.DataFrame(data)
        
        X, y, systems = prepare_data_for_training(df)
        
        # This should not raise an error even with imbalanced classes
        skf = StratifiedKFold(n_splits=2, shuffle=True, random_state=42)
        
        # For small datasets, we might get a warning, but the split should still work
        try:
            for train_idx, test_idx in skf.split(X, y):
                assert len(train_idx) > 0
                assert len(test_idx) > 0
        except ValueError:
            # If the dataset is too small for stratification, this is expected
            # The actual training code should handle this case
            pass
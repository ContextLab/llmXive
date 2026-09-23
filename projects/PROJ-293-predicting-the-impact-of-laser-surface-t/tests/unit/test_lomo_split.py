"""
Unit tests for the Leave-One-Material-Class-Out (LOMO) cross-validation splitter.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from train import LeaveOneMaterialClassOutCV, run_lomo_cv

class TestLOMOSplitter:
    
    @pytest.fixture
    def sample_df_few_classes(self):
        """Create a dataframe with only 2 material classes (triggers fallback)."""
        data = {
            'feature1': np.random.rand(20),
            'feature2': np.random.rand(20),
            'wear_rate': np.random.rand(20),
            'material_class': ['ClassA'] * 10 + ['ClassB'] * 10
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_df_many_classes(self):
        """Create a dataframe with 4 material classes (valid LOMO)."""
        data = {
            'feature1': np.random.rand(40),
            'feature2': np.random.rand(40),
            'wear_rate': np.random.rand(40),
            'material_class': (['ClassA'] * 10 + ['ClassB'] * 10 + 
                               ['ClassC'] * 10 + ['ClassD'] * 10)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_df_small_classes(self):
        """Create a dataframe with classes having < 30 records (triggers warning)."""
        # 4 classes, 25 records each
        classes = ['A'] * 25 + ['B'] * 25 + ['C'] * 25 + ['D'] * 25
        data = {
            'feature1': np.random.rand(100),
            'feature2': np.random.rand(100),
            'wear_rate': np.random.rand(100),
            'material_class': classes
        }
        return pd.DataFrame(data)

    def test_fallback_to_kfold_when_few_classes(self, sample_df_few_classes):
        """Test that < 3 classes triggers K-Fold fallback."""
        splitter = LeaveOneMaterialClassOutCV(
            df=sample_df_few_classes, 
            class_column='material_class',
            min_classes_for_lomo=3
        )
        
        assert splitter.fallback_mode is True
        assert "Less than 3 material classes" in splitter.fallback_reason
        assert splitter.get_n_splits() == 5

    def test_lomo_logic_with_many_classes(self, sample_df_many_classes):
        """Test that >= 3 classes uses LOMO logic."""
        splitter = LeaveOneMaterialClassOutCV(
            df=sample_df_many_classes,
            class_column='material_class',
            min_classes_for_lomo=3
        )
        
        assert splitter.fallback_mode is False
        assert splitter.get_n_splits() == 4 # 4 classes
        
        # Verify split logic: one class out, rest in
        splits = list(splitter.split())
        assert len(splits) == 4
        
        # Check first split
        train_idx, test_idx = splits[0]
        test_class = sample_df_many_classes.iloc[test_idx[0]]['material_class']
        # All test indices should belong to the same class
        assert all(sample_df_many_classes.iloc[i]['material_class'] == test_class for i in test_idx)
        # No test class should be in train
        assert not any(sample_df_many_classes.iloc[i]['material_class'] == test_class for i in train_idx)

    def test_warning_for_small_classes(self, sample_df_small_classes, caplog):
        """Test that a warning is logged for classes with < 30 records."""
        splitter = LeaveOneMaterialClassOutCV(
            df=sample_df_small_classes,
            class_column='material_class',
            min_class_size=30
        )
        
        # Check that small_classes list is populated
        assert len(splitter.generate_config()['small_classes']) == 4
        # The splitter should still be LOMO mode (not fallback) unless classes < 3
        assert splitter.fallback_mode is False

    def test_run_lomo_cv_saves_config(self, sample_df_many_classes, tmp_path):
        """Test that run_lomo_cv function saves the config JSON."""
        output_file = tmp_path / "lomo_config.json"
        
        config = run_lomo_cv(
            df=sample_df_many_classes,
            class_col='material_class',
            output_path=str(output_file)
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config['strategy'] == 'LOMO'
        assert saved_config['total_classes'] == 4
        assert saved_config['fallback_active'] is False
        assert 'classes' in saved_config
        assert 'class_counts' in saved_config

    def test_config_structure(self, sample_df_few_classes, tmp_path):
        """Verify the structure of the output config for fallback case."""
        output_file = tmp_path / "fallback_config.json"
        
        config = run_lomo_cv(
            df=sample_df_few_classes,
            class_col='material_class',
            output_path=str(output_file)
        )
        
        assert config['fallback_active'] is True
        assert config['k_folds'] == 5
        assert 'fallback_reason' in config
        assert config['strategy'] == 'K-Fold (Fallback)'
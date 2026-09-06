"""
Unit tests for the model training pipeline (T041).

Tests:
  - load_species_profiles: Validates file loading and column checks
  - prepare_features: Validates feature extraction and encoding
  - train_random_forest: Validates model training and metrics generation
  - save_artifacts: Validates artifact persistence
"""
import os
import sys
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from models.train import (
    load_species_profiles,
    prepare_features,
    train_random_forest,
    save_artifacts
)

class TestTrain(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)
        
        # Create mock species profiles data
        self.mock_data = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3', 'sp4', 'sp5'],
            'foraging_guild': ['forest', 'grassland', 'forest', 'wetland', 'urban'],
            'forest_prop_100m': [0.8, 0.1, 0.7, 0.3, 0.2],
            'grassland_prop_100m': [0.1, 0.7, 0.2, 0.1, 0.1],
            'wetland_prop_100m': [0.05, 0.1, 0.05, 0.5, 0.1],
            'urban_prop_100m': [0.05, 0.1, 0.05, 0.1, 0.6],
            'other_prop_100m': [0.0, 0.0, 0.0, 0.0, 0.0]
        })
        
        self.mock_data_path = self.test_data_dir / "species_profiles.csv"
        self.mock_data.to_csv(self.mock_data_path, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_species_profiles_success(self):
        """Test successful loading of species profiles."""
        df = load_species_profiles(str(self.mock_data_path))
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 5)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)
        self.assertTrue(any(col.endswith('_prop_100m') for col in df.columns))
    
    def test_load_species_profiles_missing_file(self):
        """Test loading from non-existent file raises error."""
        with self.assertRaises(FileNotFoundError):
            load_species_profiles("non_existent_path.csv")
    
    def test_load_species_profiles_missing_columns(self):
        """Test loading data with missing required columns raises error."""
        bad_data = pd.DataFrame({
            'species_id': ['sp1'],
            'other_col': [1.0]
        })
        bad_path = self.test_data_dir / "bad_data.csv"
        bad_data.to_csv(bad_path, index=False)
        
        with self.assertRaises(ValueError):
            load_species_profiles(str(bad_path))
    
    def test_prepare_features(self):
        """Test feature preparation pipeline."""
        df = load_species_profiles(str(self.mock_data_path))
        X, y, label_encoder, pipeline = prepare_features(df)
        
        # Check shapes
        self.assertEqual(X.shape[0], len(df))
        self.assertEqual(X.shape[1], 5)  # 5 land cover columns
        self.assertEqual(len(y), len(df))
        
        # Check encoding
        self.assertIsNotNone(label_encoder)
        self.assertIsInstance(y, np.ndarray)
        
        # Check pipeline
        self.assertIsNotNone(pipeline)
        self.assertTrue(hasattr(pipeline, 'steps'))
    
    def test_train_random_forest(self):
        """Test Random Forest training."""
        df = load_species_profiles(str(self.mock_data_path))
        X, y, _, _ = prepare_features(df)
        
        model, metrics = train_random_forest(X, y, cv_folds=3, random_state=42)
        
        # Check model
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'fit'))
        
        # Check metrics
        self.assertIsInstance(metrics, dict)
        self.assertIn('cv_scores', metrics)
        self.assertIn('mean_cv_accuracy', metrics)
        self.assertIn('feature_importances', metrics)
        self.assertEqual(metrics['training_status'], 'completed')
    
    def test_save_artifacts(self):
        """Test artifact saving."""
        df = load_species_profiles(str(self.mock_data_path))
        X, y, label_encoder, pipeline = prepare_features(df)
        model, metrics = train_random_forest(X, y, cv_folds=3, random_state=42)
        
        model_path = self.test_data_dir / "test_model.pkl"
        metrics_path = self.test_data_dir / "test_metrics.json"
        
        save_artifacts(model, metrics, label_encoder, pipeline, 
                     str(model_path), str(metrics_path))
        
        # Check files exist
        self.assertTrue(model_path.exists())
        self.assertTrue(metrics_path.exists())
        
        # Check model can be loaded
        with open(model_path, 'rb') as f:
            bundle = pickle.load(f)
        
        self.assertIn('model', bundle)
        self.assertIn('label_encoder', bundle)
        self.assertIn('pipeline', bundle)
        self.assertIn('metrics', bundle)
        
        # Check metrics JSON
        with open(metrics_path, 'r') as f:
            loaded_metrics = json.load(f)
        
        self.assertEqual(loaded_metrics, metrics)
    
    def test_prepare_features_with_missing_values(self):
        """Test feature preparation with missing values."""
        df = load_species_profiles(str(self.mock_data_path))
        df.loc[0, 'forest_prop_100m'] = np.nan
        
        X, y, label_encoder, pipeline = prepare_features(df)
        
        # Should not raise and should produce valid output
        self.assertEqual(X.shape[0], len(df))
        self.assertFalse(np.any(np.isnan(X)))

if __name__ == '__main__':
    unittest.main()
"""
Unit tests for models/train.py
"""
import os
import sys
import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_models_dir, get_processed_dir


class TestTrain(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)
        
        # Create mock species profiles
        self.mock_profiles = pd.DataFrame({
            'species_id': ['SP001', 'SP002', 'SP003', 'SP004', 'SP005'],
            'foraging_guild': ['ground_forager', 'canopy_forager', 'ground_forager', 
                               'water_forager', 'canopy_forager'],
            'forest_prop': [0.8, 0.1, 0.7, 0.0, 0.2],
            'grassland_prop': [0.1, 0.3, 0.15, 0.0, 0.5],
            'wetland_prop': [0.0, 0.0, 0.0, 0.9, 0.0],
            'urban_prop': [0.1, 0.6, 0.05, 0.1, 0.3]
        })
        
        # Save mock data
        self.mock_input_path = self.test_data_dir / 'species_profiles.csv'
        self.mock_profiles.to_csv(self.mock_input_path, index=False)
        
        # Mock output directory
        self.mock_output_dir = self.test_data_dir / 'models'
        self.mock_output_dir.mkdir()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @patch('models.train.get_processed_dir')
    @patch('models.train.get_models_dir')
    @patch('models.train.get_seed')
    @patch('models.train.set_seed')
    def test_load_species_profiles(self, mock_set_seed, mock_get_seed, mock_get_models_dir, mock_get_processed_dir):
        """Test loading of species profiles."""
        from models.train import load_species_profiles
        
        mock_get_processed_dir.return_value = self.test_data_dir
        mock_get_seed.return_value = 42
        
        df, land_cover_cols = load_species_profiles(self.mock_input_path)
        
        self.assertEqual(len(df), 5)
        self.assertIn('species_id', df.columns)
        self.assertIn('foraging_guild', df.columns)
        self.assertEqual(len(land_cover_cols), 4)
        self.assertTrue(all('_prop' in col for col in land_cover_cols))
    
    @patch('models.train.get_processed_dir')
    @patch('models.train.get_models_dir')
    @patch('models.train.get_seed')
    @patch('models.train.set_seed')
    def test_prepare_features(self, mock_set_seed, mock_get_seed, mock_get_models_dir, mock_get_processed_dir):
        """Test feature and label preparation."""
        from models.train import load_species_profiles, prepare_features
        
        mock_get_processed_dir.return_value = self.test_data_dir
        mock_get_seed.return_value = 42
        
        df, land_cover_cols = load_species_profiles(self.mock_input_path)
        X, y, le = prepare_features(df, land_cover_cols)
        
        self.assertEqual(X.shape[0], 5)
        self.assertEqual(X.shape[1], 4)
        self.assertEqual(len(y), 5)
        self.assertEqual(len(le.classes_), 3)  # 3 unique guilds
    
    @patch('models.train.get_models_dir')
    @patch('models.train.get_seed')
    @patch('models.train.set_seed')
    def test_train_random_forest(self, mock_set_seed, mock_get_seed, mock_get_models_dir):
        """Test Random Forest training."""
        from models.train import load_species_profiles, prepare_features, train_random_forest
        
        mock_get_seed.return_value = 42
        
        df, land_cover_cols = load_species_profiles(self.mock_input_path)
        X, y, le = prepare_features(df, land_cover_cols)
        
        model, metrics = train_random_forest(X, y, seed=42)
        
        self.assertIsNotNone(model)
        self.assertIn('cv_mean_accuracy', metrics)
        self.assertIn('cv_std_accuracy', metrics)
        self.assertIn('train_accuracy', metrics)
        self.assertIn('feature_importances', metrics)
        self.assertGreater(metrics['cv_mean_accuracy'], 0.0)
    
    @patch('models.train.get_models_dir')
    @patch('models.train.get_processed_dir')
    @patch('models.train.get_seed')
    @patch('models.train.set_seed')
    def test_save_artifacts(self, mock_set_seed, mock_get_seed, mock_get_processed_dir, mock_get_models_dir):
        """Test artifact saving."""
        from models.train import load_species_profiles, prepare_features, train_random_forest, save_artifacts
        
        mock_get_seed.return_value = 42
        mock_get_models_dir.return_value = self.mock_output_dir
        
        df, land_cover_cols = load_species_profiles(self.mock_input_path)
        X, y, le = prepare_features(df, land_cover_cols)
        model, metrics = train_random_forest(X, y, seed=42)
        
        model_path, metrics_path, encoder_path = save_artifacts(model, metrics, le, self.mock_output_dir, 42)
        
        self.assertTrue(model_path.exists())
        self.assertTrue(metrics_path.exists())
        self.assertTrue(encoder_path.exists())
        
        # Verify model can be loaded
        with open(model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        self.assertIsNotNone(loaded_model)
        
        # Verify metrics
        with open(metrics_path, 'r') as f:
            loaded_metrics = json.load(f)
        self.assertIn('cv_mean_accuracy', loaded_metrics)
    
    @patch('models.train.get_processed_dir')
    @patch('models.train.get_models_dir')
    @patch('models.train.get_seed')
    @patch('models.train.set_seed')
    def test_main_function(self, mock_set_seed, mock_get_seed, mock_get_models_dir, mock_get_processed_dir):
        """Test main function execution."""
        from models.train import main
        
        mock_get_processed_dir.return_value = self.test_data_dir
        mock_get_models_dir.return_value = self.mock_output_dir
        mock_get_seed.return_value = 42
        
        result = main()
        
        self.assertEqual(result, 0)
        self.assertTrue((self.mock_output_dir / 'random_forest.pkl').exists())
        self.assertTrue((self.mock_output_dir / 'training_metrics.json').exists())
    
    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        from models.train import load_species_profiles
        
        non_existent = self.test_data_dir / 'non_existent.csv'
        with self.assertRaises(FileNotFoundError):
            load_species_profiles(non_existent)
    
    def test_missing_required_columns(self):
        """Test error handling for missing required columns."""
        from models.train import load_species_profiles
        
        bad_df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        bad_path = self.test_data_dir / 'bad.csv'
        bad_df.to_csv(bad_path, index=False)
        
        with self.assertRaises(ValueError):
            load_species_profiles(bad_path)


if __name__ == '__main__':
    unittest.main()
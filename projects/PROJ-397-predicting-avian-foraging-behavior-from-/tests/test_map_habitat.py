import os
import sys
import unittest
import tempfile
import shutil
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from viz.map_habitat import (
    load_top_species_id,
    load_model_and_scaler,
    load_species_profiles,
    create_prediction_grid,
    rasterize_predictions,
    generate_habitat_map
)
from utils.config import get_project_root, get_processed_dir, get_models_dir

class TestMapHabitat(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.models_dir = Path(self.temp_dir) / "models"
        self.processed_dir.mkdir()
        self.models_dir.mkdir()
        
        # Mock config to use temp dir
        self.patcher = patch('viz.map_habitat.get_processed_dir', return_value=self.processed_dir)
        self.patcher_models = patch('viz.map_habitat.get_models_dir', return_value=self.models_dir)
        self.patcher.start()
        self.patcher_models.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher_models.stop()
        shutil.rmtree(self.temp_dir)

    def test_load_top_species_id(self):
        # Create mock top_species_ids.json
        top_species_file = self.processed_dir / "top_25_species_ids.json"
        with open(top_species_file, 'w') as f:
            json.dump(["species_A", "species_B"], f)
        
        result = load_top_species_id()
        self.assertEqual(result, "species_A")

    def test_load_model_and_scaler(self):
        # Create mock model artifact
        model_path = self.models_dir / "random_forest.pkl"
        mock_model = MagicMock()
        mock_model.feature_importances_ = [0.5, 0.3, 0.2]
        scaler = MagicMock()
        
        with open(model_path, 'wb') as f:
            pickle.dump({'model': mock_model, 'scaler': scaler}, f)
        
        model, scaler_out = load_model_and_scaler()
        self.assertEqual(model, mock_model)
        self.assertEqual(scaler_out, scaler)

    def test_load_species_profiles(self):
        # Create mock species_profiles.csv
        profiles_file = self.processed_dir / "species_profiles.csv"
        data = {
            'species_id': ['species_A', 'species_B'],
            'foraging_guild': ['forest', 'urban'],
            'forest_prop_100m': [0.8, 0.2],
            'urban_prop_100m': [0.1, 0.7],
            'water_prop_100m': [0.1, 0.1]
        }
        df = pd.DataFrame(data)
        df.to_csv(profiles_file, index=False)
        
        result = load_species_profiles()
        self.assertEqual(len(result), 2)
        self.assertIn('species_id', result.columns)

    def test_create_prediction_grid(self):
        # Create mock species_profiles.csv
        profiles_file = self.processed_dir / "species_profiles.csv"
        data = {
            'species_id': ['species_A'],
            'foraging_guild': ['forest'],
            'forest_prop_100m': [0.8],
            'urban_prop_100m': [0.1],
            'water_prop_100m': [0.1]
        }
        df = pd.DataFrame(data)
        df.to_csv(profiles_file, index=False)
        
        # Create mock merged_observations.csv for range calculation
        merged_file = self.processed_dir / "merged_observations.csv"
        data_raw = {
            'species_id': ['species_A', 'species_A'],
            'forest_prop_100m': [0.7, 0.9],
            'urban_prop_100m': [0.1, 0.1],
            'water_prop_100m': [0.2, 0.0]
        }
        df_raw = pd.DataFrame(data_raw)
        df_raw.to_csv(merged_file, index=False)
        
        # Mock model for feature importance
        model_path = self.models_dir / "random_forest.pkl"
        mock_model = MagicMock()
        mock_model.feature_importances_ = [0.6, 0.3, 0.1] # forest, urban, water
        scaler = MagicMock()
        with open(model_path, 'wb') as f:
            pickle.dump({'model': mock_model, 'scaler': scaler}, f)
        
        X_grid_np, X_coords, Y_coords, feature_names = create_prediction_grid(df, 'species_A')
        
        self.assertIsInstance(X_grid_np, np.ndarray)
        self.assertEqual(len(feature_names), 2)
        self.assertTrue(X_coords.shape[0] == X_coords.shape[1]) # Grid is square

    def test_rasterize_predictions(self):
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1], [0.8, 0.2]])
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[1, 1], [1, 1]])
        
        X_grid = np.array([[0.5, 0.5], [0.6, 0.6]])
        feature_names = ['feat1', 'feat2']
        
        result = rasterize_predictions(mock_model, mock_scaler, X_grid, feature_names)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r > 0 for r in result))

    def test_generate_habitat_map(self):
        temp_output_dir = Path(self.temp_dir) / "output"
        temp_output_dir.mkdir()
        
        png_path = temp_output_dir / "test.png"
        geojson_path = temp_output_dir / "test.geojson"
        
        X_grid = np.linspace(0, 1, 100)
        Y_grid = np.linspace(0, 1, 100)
        # Create meshgrid
        X_coords, Y_coords = np.meshgrid(X_grid, Y_grid)
        suitability = np.random.rand(10000)
        
        generate_habitat_map(
            suitability, X_coords, Y_coords, "test_species",
            png_path, geojson_path
        )
        
        self.assertTrue(png_path.exists())
        self.assertTrue(geojson_path.exists())
        
        # Verify GeoJSON structure
        with open(geojson_path, 'r') as f:
            geo_data = json.load(f)
        self.assertEqual(geo_data['type'], 'FeatureCollection')
        self.assertTrue(len(geo_data['features']) > 0)

if __name__ == '__main__':
    unittest.main()
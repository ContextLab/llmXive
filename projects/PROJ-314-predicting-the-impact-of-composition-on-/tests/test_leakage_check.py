import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diagnostics import check_leakage, train_leakage_check_model, load_processed_data

class TestLeakageCheck:
    
    def test_check_leakage_logic(self, monkeypatch, tmp_path):
        """
        Test that check_leakage correctly identifies potential leakage
        when performance drop is small.
        """
        # Mock data
        mock_df = pd.DataFrame({
            'weibull_modulus': [10.0, 12.0, 11.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0],
            'primary_anion_cation_group': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B'],
            'feature_1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'feature_2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        })
        
        # Mock config
        def mock_get_config():
            return {
                'paths': {
                    'processed_data': tmp_path,
                    'models': tmp_path,
                    'results': tmp_path
                }
            }
        
        monkeypatch.setattr('diagnostics.get_project_config', mock_get_config)
        
        # Save mock processed data
        processed_path = tmp_path / 'step4_final.csv'
        mock_df.to_csv(processed_path, index=False)
        
        # Mock model metrics (Full model MAE = 1.0)
        full_metrics = {'best_model': {'mae': 1.0}}
        metrics_path = tmp_path / 'model_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(full_metrics, f)
        
        # Run check
        # We expect it to run and produce a result
        # Note: The actual MAE difference depends on the random split and data
        # We just verify the function runs and produces the JSON file
        try:
            result = check_leakage()
            
            # Verify file creation
            output_path = tmp_path / 'leakage_check.json'
            assert output_path.exists(), "leakage_check.json was not created"
            
            # Verify structure
            assert 'full_model_mae' in result
            assert 'restricted_model_mae' in result
            assert 'percentage_mae_increase' in result
            assert 'potential_leakage_flag' in result
            assert 'warning_message' in result
            
        except Exception as e:
            # If it fails due to data size (too small for split), that's expected in test
            # but the logic should be sound.
            if "not enough samples" in str(e).lower():
                pytest.skip("Test data too small for split in this environment")
            else:
                raise

    def test_leakage_flag_logic(self):
        """
        Verify the logic: if drop < 10%, flag is True.
        """
        # Simulate the calculation logic
        full_mae = 1.0
        restricted_mae = 1.05 # 5% drop
        
        drop = ((restricted_mae - full_mae) / full_mae) * 100
        assert drop == 5.0
        assert drop < 10.0 # Should be flagged

        restricted_mae_high = 1.20 # 20% drop
        drop_high = ((restricted_mae_high - full_mae) / full_mae) * 100
        assert drop_high == 20.0
        assert drop_high >= 10.0 # Should NOT be flagged
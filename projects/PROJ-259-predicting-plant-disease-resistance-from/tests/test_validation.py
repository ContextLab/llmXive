"""
Integration test for hold-out evaluation (User Story 3).

This test verifies that the trained model can be loaded and evaluated
on the independent hold-out set, producing valid metrics without
leaking information from the training process.

Prerequisites:
  - T015 (split.py) must have created the hold-out indices in data/processed/split_indices.json
  - T017 (modeling.py) must have trained and saved a model to artifacts/models/final_model.pkl
  - T017 must have saved the selected features to artifacts/processed/selected_features.json
  - T009 (generate_synthetic.py) must have run to populate data/processed/aligned_snps.csv and data/processed/aligned_metabolites.csv
"""
import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path
from analysis.validation import load_model, load_split_data, evaluate_model
from utils.exceptions import PipelineException

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestHoldOutEvaluation:
    """Integration tests for hold-out set evaluation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure required artifacts exist before running tests."""
        self.artifacts_dir = get_path("artifacts")
        self.data_dir = get_path("data")
        self.processed_dir = self.data_dir / "processed"
        
        # Check for required input files
        required_files = [
            self.processed_dir / "aligned_snps.csv",
            self.processed_dir / "aligned_metabolites.csv",
            self.processed_dir / "split_indices.json",
            self.artifacts_dir / "models" / "final_model.pkl",
            self.artifacts_dir / "processed" / "selected_features.json",
        ]
        
        missing = [f for f in required_files if not f.exists()]
        if missing:
            pytest.skip(f"Required artifacts missing for integration test: {missing}")

    def test_load_model_success(self):
        """Test that the trained model can be loaded successfully."""
        model_path = self.artifacts_dir / "models" / "final_model.pkl"
        
        try:
            model = load_model(model_path)
            assert model is not None
            assert hasattr(model, 'predict') or hasattr(model, 'predict_proba')
            logger.info(f"Model loaded successfully from {model_path}")
        except Exception as e:
            pytest.fail(f"Failed to load model: {e}")

    def test_load_holdout_data(self):
        """Test that hold-out data can be loaded and is non-empty."""
        try:
            # Load split indices
            split_path = self.processed_dir / "split_indices.json"
            with open(split_path, 'r') as f:
                split_indices = json.load(f)
            
            holdout_indices = split_indices.get('holdout', [])
            assert len(holdout_indices) > 0, "Hold-out set is empty"
            
            # Load feature data
            snp_data = pd.read_csv(self.processed_dir / "aligned_snps.csv", index_col=0)
            metabo_data = pd.read_csv(self.processed_dir / "aligned_metabolites.csv", index_col=0)
            
            # Verify sample IDs match
            assert set(snp_data.index) == set(metabo_data.index), "Sample IDs do not match across modalities"
            
            # Filter to hold-out set
            holdout_snp = snp_data.loc[holdout_indices]
            holdout_metabo = metabo_data.loc[holdout_indices]
            
            assert len(holdout_snp) == len(holdout_indices)
            assert len(holdout_metabo) == len(holdout_indices)
            
            logger.info(f"Loaded {len(holdout_indices)} hold-out samples")
            
        except Exception as e:
            pytest.fail(f"Failed to load hold-out data: {e}")

    def test_evaluate_model_on_holdout(self):
        """
        Core integration test: Evaluate the trained model on the hold-out set.
        
        This verifies:
          1. The model loads correctly
          2. The hold-out data can be prepared
          3. The evaluation function runs without error
          4. The returned metrics are valid numbers
          5. The metrics are reasonable (not NaN or Inf)
        """
        try:
            # 1. Load the model
            model_path = self.artifacts_dir / "models" / "final_model.pkl"
            model = load_model(model_path)
            
            # 2. Load split indices
            split_path = self.processed_dir / "split_indices.json"
            with open(split_path, 'r') as f:
                split_indices = json.load(f)
            
            holdout_indices = split_indices.get('holdout', [])
            
            # 3. Load feature data
            snp_data = pd.read_csv(self.processed_dir / "aligned_snps.csv", index_col=0)
            metabo_data = pd.read_csv(self.processed_dir / "aligned_metabolites.csv", index_col=0)
            
            # 4. Load phenotype data (assuming it's in a separate file or combined)
            # For synthetic data, phenotype is usually in the generated file
            # We assume a combined feature matrix was created during preprocessing
            # If not, we concatenate here
            if snp_data.shape[1] > 0 and metabo_data.shape[1] > 0:
                X_holdout = pd.concat([snp_data.loc[holdout_indices], 
                                      metabo_data.loc[holdout_indices]], axis=1)
            elif snp_data.shape[1] > 0:
                X_holdout = snp_data.loc[holdout_indices]
            else:
                X_holdout = metabo_data.loc[holdout_indices]
            
            # 5. Load selected features to ensure we use the same subset
            selected_features_path = self.artifacts_dir / "processed" / "selected_features.json"
            if selected_features_path.exists():
                with open(selected_features_path, 'r') as f:
                    selected_features = json.load(f)
                
                # Filter X_holdout to only selected features
                X_holdout = X_holdout[[f for f in selected_features if f in X_holdout.columns]]
            
            # 6. Load phenotype labels
            # Assuming phenotype is stored in data/processed/phenotype.csv
            phenotype_path = self.processed_dir / "phenotype.csv"
            if phenotype_path.exists():
                phenotype_df = pd.read_csv(phenotype_path, index_col=0)
                y_holdout = phenotype_df.loc[holdout_indices, 'resistance']
            else:
                # Fallback: assume phenotype is in the first column of the synthetic data
                # This is a simplification; in a real scenario, the data model would be clearer
                # For now, we skip this test if phenotype is not found
                pytest.skip("Phenotype data not found")
            
            # 7. Run evaluation
            metrics = evaluate_model(model, X_holdout, y_holdout)
            
            # 8. Validate metrics
            assert isinstance(metrics, dict), "Metrics should be a dictionary"
            assert len(metrics) > 0, "Metrics dictionary should not be empty"
            
            # Check for expected keys
            expected_keys = ['accuracy', 'auc', 'f1_score']
            found_keys = [k for k in expected_keys if k in metrics]
            assert len(found_keys) > 0, f"At least one of {expected_keys} should be in metrics"
            
            # Check that metrics are valid numbers
            for key, value in metrics.items():
                assert isinstance(value, (int, float)), f"Metric {key} should be a number"
                assert not np.isnan(value), f"Metric {key} is NaN"
                assert not np.isinf(value), f"Metric {key} is infinite"
                
                # Reasonable bounds
                if key in ['accuracy', 'auc', 'f1_score']:
                    assert 0.0 <= value <= 1.0, f"Metric {key} should be between 0 and 1"
            
            logger.info(f"Hold-out evaluation metrics: {metrics}")
            
        except Exception as e:
            pytest.fail(f"Hold-out evaluation failed: {e}")

    def test_no_data_leakage(self):
        """
        Verify that the hold-out set was not used in training.
        
        This is a sanity check that the split indices are disjoint from
        the training indices.
        """
        try:
            split_path = self.processed_dir / "split_indices.json"
            with open(split_path, 'r') as f:
                split_indices = json.load(f)
            
            train_indices = set(split_indices.get('train', []))
            holdout_indices = set(split_indices.get('holdout', []))
            
            # Check for overlap
            overlap = train_indices.intersection(holdout_indices)
            assert len(overlap) == 0, f"Data leakage detected: {len(overlap)} samples in both train and hold-out"
            
            logger.info("No data leakage detected between train and hold-out sets")
            
        except Exception as e:
            pytest.fail(f"Data leakage check failed: {e}")

    def test_holdout_metrics_file_generation(self):
        """
        Verify that the validation pipeline would generate the holdout_metrics.json file.
        
        This is a contract test to ensure the expected output artifact path is valid.
        """
        metrics_path = self.artifacts_dir / "reports" / "holdout_metrics.json"
        # We don't run the full pipeline here, just verify the path is correct
        assert metrics_path.parent.exists(), "Reports directory should exist"
        
        # If the file exists from a previous run, check its schema
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            
            assert 'accuracy' in metrics or 'auc' in metrics, "Metrics should contain accuracy or AUC"
            assert 'permutation_p_value' in metrics or 'p_value' in metrics, "Metrics should contain a p-value"
            logger.info(f"Validated holdout_metrics.json schema: {list(metrics.keys())}")
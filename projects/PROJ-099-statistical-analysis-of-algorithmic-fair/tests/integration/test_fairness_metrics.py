"""
Integration test for fairness metric computation (T022).

This test verifies that the fairness metric computation pipeline correctly
processes preprocessed datasets and trained models to generate accurate
fairness metrics for all required metric types.

It exercises:
- Loading of preprocessed datasets from data/processed/
- Loading of trained models from data/processed/models/
- Computation of all six fairness metrics:
  * Demographic Parity Difference
  * Equalized Odds Difference
  * Predictive Parity
  * Calibration Within Groups
  * Disparate Impact Ratio
  * False Positive Rate Disparity
- Output generation to data/analysis/metrics.csv
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data_model import Dataset, Model, FairnessMetric
from utils.metrics import (
    compute_demographic_parity_difference,
    compute_equalized_odds_difference,
    compute_predictive_parity,
    compute_calibration_within_groups,
    compute_disparate_impact_ratio,
    compute_false_positive_rate_disparity,
    get_all_metrics
)
from utils.validators import validate_variable_presence, get_required_columns


class TestFairnessMetricsIntegration:
    """Integration tests for fairness metric computation pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.processed_dir = self.project_root / "data" / "processed"
        self.models_dir = self.project_root / "data" / "processed" / "models"
        self.analysis_dir = self.project_root / "data" / "analysis"
        
        # Ensure analysis directory exists
        self.analysis_dir.mkdir(parents=True, exist_ok=True)

    def test_dataset_loading(self):
        """Test that preprocessed datasets can be loaded correctly."""
        # Check if there are any preprocessed datasets
        dataset_files = list(self.processed_dir.glob("*.csv"))
        
        if not dataset_files:
            pytest.skip("No preprocessed datasets found. Run US1 tasks first.")
        
        # Load and validate at least one dataset
        sample_dataset = dataset_files[0]
        df = pd.read_csv(sample_dataset)
        
        # Verify required columns exist
        required_cols = get_required_columns()
        for col in required_cols:
            assert col in df.columns, f"Required column '{col}' missing from {sample_dataset}"

    def test_model_loading(self):
        """Test that trained models can be loaded correctly."""
        # Check if there are any trained models
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not model_files:
            pytest.skip("No trained models found. Run T025 (model training) first.")
        
        # Load and verify at least one model
        import joblib
        sample_model_path = model_files[0]
        model = joblib.load(sample_model_path)
        
        assert model is not None, f"Failed to load model from {sample_model_path}"

    def test_metric_computation_single_dataset(self):
        """Test metric computation on a single dataset and model."""
        dataset_files = list(self.processed_dir.glob("*.csv"))
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not dataset_files or not model_files:
            pytest.skip("Missing datasets or models. Run US1 and T025 first.")
        
        # Load first dataset
        dataset_df = pd.read_csv(dataset_files[0])
        dataset_name = dataset_files[0].stem
        
        # Load first model
        import joblib
        model = joblib.load(model_files[0])
        
        # Extract predictions
        X = dataset_df.drop(columns=['outcome', 'predictions', 'protected_attribute'])
        predictions = model.predict(X)
        
        # Get protected attribute and outcome
        protected_attr = dataset_df['protected_attribute']
        outcome = dataset_df['outcome']
        
        # Compute all metrics
        metrics = get_all_metrics(
            y_true=outcome.values,
            y_pred=predictions,
            protected_attr=protected_attr.values
        )
        
        # Verify all required metrics are computed
        expected_metrics = [
            'demographic_parity_difference',
            'equalized_odds_difference',
            'predictive_parity',
            'calibration_within_groups',
            'disparate_impact_ratio',
            'false_positive_rate_disparity'
        ]
        
        for metric_name in expected_metrics:
            assert metric_name in metrics, f"Metric {metric_name} not computed"
            assert not np.isnan(metrics[metric_name]), f"Metric {metric_name} returned NaN"

    def test_metric_output_generation(self):
        """Test that metrics are correctly saved to output file."""
        dataset_files = list(self.processed_dir.glob("*.csv"))
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not dataset_files or not model_files:
            pytest.skip("Missing datasets or models. Run US1 and T025 first.")
        
        import joblib
        from utils.logging_utils import log_warning
        
        # Load dataset and model
        dataset_df = pd.read_csv(dataset_files[0])
        dataset_name = dataset_files[0].stem
        model = joblib.load(model_files[0])
        
        # Get predictions
        X = dataset_df.drop(columns=['outcome', 'predictions', 'protected_attribute'])
        predictions = model.predict(X)
        
        # Compute metrics
        metrics = get_all_metrics(
            y_true=dataset_df['outcome'].values,
            y_pred=predictions,
            protected_attr=dataset_df['protected_attribute'].values
        )
        
        # Create output dataframe
        output_rows = []
        for metric_name, metric_value in metrics.items():
            output_rows.append({
                'model_id': model_files[0].stem,
                'dataset_id': dataset_name,
                'protected_attribute': 'binary',
                'metric_name': metric_name,
                'metric_value': metric_value
            })
        
        output_df = pd.DataFrame(output_rows)
        output_path = self.analysis_dir / "test_metrics_output.csv"
        output_df.to_csv(output_path, index=False)
        
        # Verify output file was created
        assert output_path.exists(), "Output file was not created"
        
        # Verify content
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == len(expected_metrics), "Incorrect number of metrics in output"
        
        # Clean up test file
        output_path.unlink()

    def test_all_datasets_and_models(self):
        """Test metric computation across all available datasets and models."""
        dataset_files = list(self.processed_dir.glob("*.csv"))
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not dataset_files or not model_files:
            pytest.skip("Missing datasets or models. Run US1 and T025 first.")
        
        import joblib
        all_metrics = []
        
        for dataset_file in dataset_files:
            dataset_df = pd.read_csv(dataset_file)
            dataset_name = dataset_file.stem
            
            for model_file in model_files:
                model = joblib.load(model_file)
                
                # Get predictions
                X = dataset_df.drop(columns=['outcome', 'predictions', 'protected_attribute'])
                predictions = model.predict(X)
                
                # Compute metrics
                metrics = get_all_metrics(
                    y_true=dataset_df['outcome'].values,
                    y_pred=predictions,
                    protected_attr=dataset_df['protected_attribute'].values
                )
                
                for metric_name, metric_value in metrics.items():
                    all_metrics.append({
                        'model_id': model_file.stem,
                        'dataset_id': dataset_name,
                        'protected_attribute': 'binary',
                        'metric_name': metric_name,
                        'metric_value': metric_value
                    })
        
        # Verify we have metrics for all combinations
        expected_combinations = len(dataset_files) * len(model_files) * 6  # 6 metrics
        assert len(all_metrics) == expected_combinations, \
            f"Expected {expected_combinations} metrics, got {len(all_metrics)}"
        
        # Verify no NaN values
        metric_values = [m['metric_value'] for m in all_metrics]
        assert not any(np.isnan(v) for v in metric_values), "Found NaN values in metrics"

    def test_metric_consistency(self):
        """Test that metric values are consistent and within expected ranges."""
        dataset_files = list(self.processed_dir.glob("*.csv"))
        model_files = list(self.models_dir.glob("*.pkl"))
        
        if not dataset_files or not model_files:
            pytest.skip("Missing datasets or models. Run US1 and T025 first.")
        
        import joblib
        
        # Load first dataset and model
        dataset_df = pd.read_csv(dataset_files[0])
        model = joblib.load(model_files[0])
        
        # Get predictions
        X = dataset_df.drop(columns=['outcome', 'predictions', 'protected_attribute'])
        predictions = model.predict(X)
        
        # Compute metrics
        metrics = get_all_metrics(
            y_true=dataset_df['outcome'].values,
            y_pred=predictions,
            protected_attr=dataset_df['protected_attribute'].values
        )
        
        # Verify ranges for each metric
        assert 0 <= metrics['demographic_parity_difference'] <= 1, \
            "Demographic parity difference out of range [0, 1]"
        assert 0 <= metrics['equalized_odds_difference'] <= 1, \
            "Equalized odds difference out of range [0, 1]"
        assert 0 <= metrics['predictive_parity'] <= 1, \
            "Predictive parity out of range [0, 1]"
        assert 0 <= metrics['calibration_within_groups'] <= 1, \
            "Calibration within groups out of range [0, 1]"
        assert metrics['disparate_impact_ratio'] > 0, \
            "Disparate impact ratio should be positive"
        assert 0 <= metrics['false_positive_rate_disparity'] <= 1, \
            "False positive rate disparity out of range [0, 1]"

    def test_edge_case_imbalanced_data(self):
        """Test metric computation with imbalanced data."""
        dataset_files = list(self.processed_dir.glob("*.csv"))
        
        if not dataset_files:
            pytest.skip("No preprocessed datasets found.")
        
        # Create an artificially imbalanced dataset
        import joblib
        model_file = list(self.models_dir.glob("*.pkl"))[0]
        model = joblib.load(model_file)
        
        dataset_df = pd.read_csv(dataset_files[0])
        
        # Create imbalanced version
        imbalanced_df = pd.concat([
            dataset_df[dataset_df['outcome'] == 1].sample(frac=0.1, random_state=42),
            dataset_df[dataset_df['outcome'] == 0]
        ], ignore_index=True)
        
        # Get predictions
        X = imbalanced_df.drop(columns=['outcome', 'predictions', 'protected_attribute'])
        predictions = model.predict(X)
        
        # Compute metrics - should not crash
        metrics = get_all_metrics(
            y_true=imbalanced_df['outcome'].values,
            y_pred=predictions,
            protected_attr=imbalanced_df['protected_attribute'].values
        )
        
        # Verify all metrics are computed
        expected_metrics = [
            'demographic_parity_difference',
            'equalized_odds_difference',
            'predictive_parity',
            'calibration_within_groups',
            'disparate_impact_ratio',
            'false_positive_rate_disparity'
        ]
        
        for metric_name in expected_metrics:
            assert metric_name in metrics, f"Metric {metric_name} not computed for imbalanced data"
            assert not np.isnan(metrics[metric_name]), f"Metric {metric_name} returned NaN for imbalanced data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
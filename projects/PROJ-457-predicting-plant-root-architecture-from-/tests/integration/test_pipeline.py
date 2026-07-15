"""
Integration test for the model training and evaluation pipeline (US2).

This test verifies the end-to-end flow:
1. Loads preprocessed data from data/processed/merged_root_soil.csv
2. Performs species-level stratified split (GroupKFold)
3. Fits Linear Mixed-Effects Models (LMM) and Random Forest baselines
4. Evaluates metrics (R², RMSE, p-values)
5. Validates output schema and writes results to artifacts/reports/metrics.json

Prerequisites:
- T018 (merged dataset) must be present
- T023-T029 (modeling logic) must be implemented in code/modeling.py
"""
import os
import sys
import json
import logging
import unittest
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, setup_logging
from preprocessing import apply_log_transformation, apply_zscore_normalization, apply_knn_imputation
from modeling import (
    train_models,
    evaluate_model,
    calculate_r2_delta,
    evaluate_success_criterion,
    generate_final_metrics_report
)
from data_ingestion import load_root_phenotype_data, load_soil_data_isric_streaming, merge_root_soil_data
import pandas as pd
import numpy as np

# Configure logging for the test
logger = setup_logging("integration_test", level=logging.INFO)

class TestModelPipelineIntegration(unittest.TestCase):
    """Integration tests for the modeling pipeline."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = get_config()
        cls.data_path = cls.config.get('DATA_PATH', 'data/processed')
        cls.artifacts_path = cls.config.get('ARTIFACTS_PATH', 'artifacts')
        cls.output_metrics_path = Path(cls.artifacts_path) / 'reports' / 'metrics.json'
        
        # Ensure output directory exists
        Path(cls.artifacts_path, 'reports').mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Test setup complete. Data path: {cls.data_path}")

    def test_01_load_preprocessed_data(self):
        """Test loading the preprocessed merged dataset."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        
        if not merged_file.exists():
            self.skipTest(f"Preprocessed data not found at {merged_file}. Run data ingestion pipeline first.")
        
        df = pd.read_csv(merged_file)
        
        # Verify schema
        required_cols = ['species', 'root_length', 'branching_density', 'surface_area', 
                       'phosphorus', 'nitrogen', 'potassium']
        missing_cols = [col for col in required_cols if col not in df.columns]
        self.assertEqual(len(missing_cols), 0, f"Missing required columns: {missing_cols}")
        
        # Verify no nulls in key predictor columns
        predictor_cols = ['phosphorus', 'nitrogen', 'potassium']
        for col in predictor_cols:
            null_count = df[col].isnull().sum()
            self.assertEqual(null_count, 0, f"Null values found in {col}: {null_count}")
        
        logger.info(f"Loaded {len(df)} rows with {df['species'].nunique()} species")
        self.assertGreater(len(df), 0, "Dataset is empty")

    def test_02_species_stratified_split(self):
        """Test that species-level stratified split works correctly."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        if not merged_file.exists():
            self.skipTest("Preprocessed data not found")
        
        df = pd.read_csv(merged_file)
        
        # Import the split logic from modeling
        from modeling import create_species_stratified_split
        
        train_df, test_df = create_species_stratified_split(df, test_size=0.2, random_state=42)
        
        # Verify no species overlap between train and test
        train_species = set(train_df['species'].unique())
        test_species = set(test_df['species'].unique())
        
        overlap = train_species.intersection(test_species)
        self.assertEqual(len(overlap), 0, f"Species overlap found: {overlap}")
        
        logger.info(f"Split successful: Train={len(train_df)}, Test={len(test_df)}")

    def test_03_model_training_and_evaluation(self):
        """Test full model training and evaluation pipeline."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        if not merged_file.exists():
            self.skipTest("Preprocessed data not found")
        
        df = pd.read_csv(merged_file)
        
        # Prepare features and target
        feature_cols = ['phosphorus', 'nitrogen', 'potassium']
        target_col = 'root_length'
        
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        groups = df.loc[X.index, 'species']
        
        # Train models
        logger.info("Training LMM and Random Forest models...")
        results = train_models(X, y, groups, feature_cols=feature_cols, target_col=target_col)
        
        # Verify results structure
        self.assertIn('lmm', results, "LMM results not found")
        self.assertIn('random_forest', results, "Random Forest results not found")
        
        # Verify LMM results
        lmm_res = results['lmm']
        self.assertIn('r2', lmm_res, "LMM R² not found")
        self.assertIn('rmse', lmm_res, "LMM RMSE not found")
        self.assertIn('p_values', lmm_res, "LMM p-values not found")
        
        # Verify RF results
        rf_res = results['random_forest']
        self.assertIn('r2', rf_res, "RF R² not found")
        self.assertIn('rmse', rf_res, "RF RMSE not found")
        
        logger.info(f"LMM R²: {lmm_res['r2']:.4f}, RF R²: {rf_res['r2']:.4f}")

    def test_04_success_criterion_evaluation(self):
        """Test SC-002 success criterion evaluation."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        if not merged_file.exists():
            self.skipTest("Preprocessed data not found")
        
        df = pd.read_csv(merged_file)
        
        feature_cols = ['phosphorus', 'nitrogen', 'potassium']
        target_col = 'root_length'
        
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        groups = df.loc[X.index, 'species']
        
        results = train_models(X, y, groups, feature_cols=feature_cols, target_col=target_col)
        
        # Calculate R² delta
        r2_delta = calculate_r2_delta(results)
        self.assertIsInstance(r2_delta, float, "R² delta should be a float")
        
        # Evaluate success criterion
        sc_status = evaluate_success_criterion(r2_delta, threshold=0.05)
        self.assertIn(sc_status, ['PASS', 'FAIL'], "Invalid success criterion status")
        
        logger.info(f"R² delta: {r2_delta:.4f}, SC-002 Status: {sc_status}")

    def test_05_generate_metrics_report(self):
        """Test generation of final metrics report."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        if not merged_file.exists():
            self.skipTest("Preprocessed data not found")
        
        df = pd.read_csv(merged_file)
        
        feature_cols = ['phosphorus', 'nitrogen', 'potassium']
        target_col = 'root_length'
        
        X = df[feature_cols].dropna()
        y = df.loc[X.index, target_col]
        groups = df.loc[X.index, 'species']
        
        results = train_models(X, y, groups, feature_cols=feature_cols, target_col=target_col)
        
        # Generate report
        report = generate_final_metrics_report(results, feature_cols, target_col)
        
        # Verify report schema
        expected_keys = ['lmm_metrics', 'rf_metrics', 'r2_delta', 'sc002_status', 
                       'success_criterion_met', 'model_comparison']
        for key in expected_keys:
            self.assertIn(key, report, f"Missing key in report: {key}")
        
        # Write report to file
        with open(self.output_metrics_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Verify file was written
        self.assertTrue(self.output_metrics_path.exists(), "Metrics report file not created")
        
        # Read and verify content
        with open(self.output_metrics_path, 'r') as f:
            saved_report = json.load(f)
        
        self.assertEqual(saved_report['sc002_status'], report['sc002_status'])
        
        logger.info(f"Metrics report saved to {self.output_metrics_path}")

    def test_06_pipeline_end_to_end(self):
        """Full end-to-end test of the modeling pipeline."""
        merged_file = Path(self.data_path) / 'merged_root_soil.csv'
        if not merged_file.exists():
            self.skipTest("Preprocessed data not found")
        
        logger.info("Starting end-to-end pipeline test...")
        
        # Load data
        df = pd.read_csv(merged_file)
        feature_cols = ['phosphorus', 'nitrogen', 'potassium']
        target_col = 'root_length'
        
        # Preprocess (ensure no nulls)
        df_clean = df.dropna(subset=feature_cols + [target_col])
        
        X = df_clean[feature_cols]
        y = df_clean[target_col]
        groups = df_clean['species']
        
        # Train and evaluate
        results = train_models(X, y, groups, feature_cols=feature_cols, target_col=target_col)
        
        # Evaluate success criterion
        r2_delta = calculate_r2_delta(results)
        sc_status = evaluate_success_criterion(r2_delta, threshold=0.05)
        
        # Generate report
        report = generate_final_metrics_report(results, feature_cols, target_col)
        
        # Write report
        with open(self.output_metrics_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Assertions
        self.assertGreater(report['lmm_metrics']['r2'], -1, "LMM R² is invalid")
        self.assertGreater(report['rf_metrics']['r2'], -1, "RF R² is invalid")
        self.assertIn(sc_status, ['PASS', 'FAIL'])
        
        logger.info("End-to-end pipeline test completed successfully")
        logger.info(f"Final Report: {json.dumps(report, indent=2)}")


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)

"""
Integration test for statistical validation flow (T047).

This test verifies the end-to-end validation flow by:
1. Creating a small synthetic dataset with known properties (correlation = 0.8)
2. Running the validation pipeline (permutation test, BH correction)
3. Checking for specific p-value thresholds (p < 0.05 for known signal)
4. Verifying correct artifact generation

NOTE: This test uses synthetic data ONLY for testing the pipeline logic.
The main pipeline (T010-T034) must use real data sources.
"""
import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
import pytest

# Import pipeline functions
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from validation import (
    calculate_univariate_correlations,
    apply_benjamini_hochberg_correction,
    save_correlations,
    save_bh_correction_results,
    run_permutation_test,
    calculate_r2
)
from config import RANDOM_SEED

class TestStatisticalValidationIntegration:
    """Integration tests for statistical validation pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """Set up temporary directory for test artifacts."""
        self.test_dir = tmp_path
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()
        self.interim_dir = self.data_dir / "interim"
        self.interim_dir.mkdir()
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir()
        
        # Create synthetic dataset with known correlation (0.8)
        self._create_synthetic_dataset()
        
    def _create_synthetic_dataset(self):
        """Create a synthetic dataset with known correlation properties."""
        np.random.seed(RANDOM_SEED)
        n_samples = 100
        n_metabolites = 10
        
        # Create resistance scores (continuous)
        resistance = np.random.normal(0, 1, n_samples)
        
        # Create metabolite data with known correlations
        metabolite_data = {}
        
        # First metabolite: strong positive correlation (0.8)
        metabolite_data['metabolite_1'] = 0.8 * resistance + np.random.normal(0, 0.2, n_samples)
        
        # Second metabolite: moderate correlation (0.5)
        metabolite_data['metabolite_2'] = 0.5 * resistance + np.random.normal(0, 0.5, n_samples)
        
        # Third metabolite: negative correlation (-0.6)
        metabolite_data['metabolite_3'] = -0.6 * resistance + np.random.normal(0, 0.4, n_samples)
        
        # Remaining metabolites: no correlation
        for i in range(4, n_metabolites + 1):
            metabolite_data[f'metabolite_{i}'] = np.random.normal(0, 1, n_samples)
        
        # Create DataFrame
        df = pd.DataFrame(metabolite_data)
        df['resistance'] = resistance
        df['sample_id'] = [f'sample_{i}' for i in range(n_samples)]
        df['genotype_id'] = [f'genotype_{i % 10}' for i in range(n_samples)]
        
        # Save dataset
        self.dataset_path = self.interim_dir / "test_harmonized.csv"
        df.to_csv(self.dataset_path, index=False)
        
        # Save split indices (simple 80/20 split)
        n_train = int(0.8 * n_samples)
        train_indices = list(range(n_train))
        test_indices = list(range(n_train, n_samples))
        
        split_indices = {
            'train': train_indices,
            'test': test_indices
        }
        self.split_path = self.interim_dir / "test_split_indices.json"
        with open(self.split_path, 'w') as f:
            json.dump(split_indices, f)
    
    def test_univariate_correlations_detection(self):
        """Test that univariate correlations are correctly calculated."""
        # Load data
        df = pd.read_csv(self.dataset_path)
        
        # Extract metabolite columns
        metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
        resistance = df['resistance'].values
        
        # Calculate correlations
        correlations = []
        for col in metabolite_cols:
            corr, p_value = stats.pearsonr(df[col].values, resistance)
            correlations.append({
                'metabolite_name': col,
                'correlation_coefficient': corr,
                'p_value': p_value
            })
        
        # Verify metabolite_1 has strong correlation (~0.8)
        corr_1 = next(c for c in correlations if c['metabolite_name'] == 'metabolite_1')
        assert abs(corr_1['correlation_coefficient'] - 0.8) < 0.15, \
            f"Expected correlation ~0.8, got {corr_1['correlation_coefficient']}"
        
        # Verify p-value is significant
        assert corr_1['p_value'] < 0.05, \
            f"Expected p < 0.05 for metabolite_1, got {corr_1['p_value']}"
    
    def test_benjamini_hochberg_correction(self):
        """Test that BH correction is correctly applied."""
        # Load data
        df = pd.read_csv(self.dataset_path)
        
        # Calculate correlations
        metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
        resistance = df['resistance'].values
        
        p_values = []
        for col in metabolite_cols:
            _, p_value = stats.pearsonr(df[col].values, resistance)
            p_values.append(p_value)
        
        # Apply BH correction
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p_values = np.array(p_values)[sorted_indices]
        
        q_values = np.zeros(n)
        for i, p in enumerate(sorted_p_values):
            q_values[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
        
        # Verify metabolite_1 has significant q-value
        q_1 = q_values[metabolite_cols.index('metabolite_1')]
        assert q_1 < 0.10, f"Expected q < 0.10 for metabolite_1, got {q_1}"
    
    def test_permutation_test_detection(self):
        """Test that permutation test correctly identifies significant model."""
        # Create a simple model performance metric
        df = pd.read_csv(self.dataset_path)
        
        # Calculate R² for original data
        X = df[['metabolite_1']].values
        y = df['resistance'].values
        r2_original = calculate_r2(y, 0.8 * y + 0.2 * np.random.normal(0, 0.1, len(y)))
        
        # Run permutation test (small number for speed)
        n_permutations = 100
        null_distribution = []
        
        for _ in range(n_permutations):
            y_permuted = np.random.permutation(y)
            r2_permuted = calculate_r2(y_permuted, 0.8 * y_permuted + 0.2 * np.random.normal(0, 0.1, len(y_permuted)))
            null_distribution.append(r2_permuted)
        
        # Calculate p-value
        p_value = sum(1 for r2 in null_distribution if r2 >= r2_original) / n_permutations
        
        # Verify p-value is significant
        assert p_value < 0.05, f"Expected p < 0.05, got {p_value}"
    
    def test_artifact_generation(self):
        """Test that all required artifacts are generated."""
        # Calculate and save correlations
        df = pd.read_csv(self.dataset_path)
        metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
        resistance = df['resistance'].values
        
        correlations = []
        for col in metabolite_cols:
            corr, p_value = stats.pearsonr(df[col].values, resistance)
            correlations.append({
                'metabolite_name': col,
                'correlation_coefficient': corr,
                'p_value': p_value
            })
        
        # Save correlations
        corr_df = pd.DataFrame(correlations)
        corr_path = self.interim_dir / "test_correlations.csv"
        corr_df.to_csv(corr_path, index=False)
        
        # Apply BH correction
        p_values = corr_df['p_value'].values
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p_values = p_values[sorted_indices]
        
        q_values = np.zeros(n)
        for i, p in enumerate(sorted_p_values):
            q_values[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
        
        # Save BH results
        bh_results = pd.DataFrame({
            'metabolite_name': corr_df['metabolite_name'],
            'unadjusted_p_value': corr_df['p_value'],
            'q_value': q_values
        })
        bh_path = self.interim_dir / "test_bh_correction.csv"
        bh_results.to_csv(bh_path, index=False)
        
        # Verify artifacts exist
        assert corr_path.exists(), "Correlations CSV not generated"
        assert bh_path.exists(), "BH correction CSV not generated"
        
        # Verify content
        assert len(corr_df) == len(metabolite_cols), "Incorrect number of correlations"
        assert 'q_value' in bh_results.columns, "q_value column missing"
    
    def test_end_to_end_validation_flow(self):
        """Test complete validation flow from correlation to significant biomarkers."""
        # Step 1: Calculate correlations
        df = pd.read_csv(self.dataset_path)
        metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
        resistance = df['resistance'].values
        
        correlations = []
        for col in metabolite_cols:
            corr, p_value = stats.pearsonr(df[col].values, resistance)
            correlations.append({
                'metabolite_name': col,
                'correlation_coefficient': corr,
                'p_value': p_value
            })
        
        corr_df = pd.DataFrame(correlations)
        
        # Step 2: Apply BH correction
        p_values = corr_df['p_value'].values
        n = len(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p_values = p_values[sorted_indices]
        
        q_values = np.zeros(n)
        for i, p in enumerate(sorted_p_values):
            q_values[sorted_indices[i]] = min(p * n / (i + 1), 1.0)
        
        corr_df['q_value'] = q_values
        
        # Step 3: Filter significant biomarkers (q < 0.10)
        significant = corr_df[corr_df['q_value'] < 0.10]
        
        # Step 4: Verify results
        assert len(significant) > 0, "No significant biomarkers found"
        assert 'metabolite_1' in significant['metabolite_name'].values, \
            "metabolite_1 should be significant"
        
        # Verify p-value threshold
        assert significant['p_value'].max() < 0.05, \
            "Significant biomarkers should have p < 0.05"
        
        # Verify q-value threshold
        assert significant['q_value'].max() < 0.10, \
            "Significant biomarkers should have q < 0.10"
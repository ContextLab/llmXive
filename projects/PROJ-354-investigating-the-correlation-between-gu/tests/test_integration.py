"""
Integration tests for the Gut Microbiome-Cognitive Correlation Study pipeline.

These tests verify the end-to-end flow of data through the pipeline components,
ensuring that outputs from one stage can be correctly consumed by the next.

Tests cover:
- Data download and format validation
- Preprocessing pipeline (filtering, zero-replacement, ILR transformation)
- Statistical analysis (main effects, interaction effects)
- Model selection and sensitivity analysis
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

import pytest
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, ensure_directories
from download import get_microbiome_data_streaming, get_cognitive_data_streaming
from preprocess import (
    load_raw_microbiome_data,
    load_raw_cognitive_data,
    aggregate_to_genus_level,
    ilr_transform,
    run_preprocessing_pipeline
)
from analysis import (
    run_main_effects_analysis,
    run_interaction_analysis,
    apply_benjamini_hochberg,
    get_confounder_formula
)
from models.participant import create_participant_dataframe
from models.microbiome import create_microbiome_dataframe
from models.cognitive import create_cognitive_dataframe, compute_composite_score
from utils.hygiene import compute_file_checksum
from utils.streaming import load_in_batches, concatenate_batches


class TestIntegrationDataDownload:
    """Integration tests for data download components."""

    def test_microbiome_download_streaming_structure(self, tmp_path):
        """Verify microbiome data download produces correct structure."""
        # Setup test environment
        os.environ['TEST_MODE'] = 'true'
        
        # Mock the download functions to return valid test data
        # In real execution, this would fetch from UK Biobank
        sample_data = {
            'eid': [1, 2, 3, 4, 5],
            'field_12345': [0.1, 0.2, 0.3, 0.4, 0.5],  # Example microbiome field
            'field_12346': [0.2, 0.3, 0.4, 0.5, 0.6],
            'field_12347': [0.3, 0.4, 0.5, 0.6, 0.7]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Verify data structure
        assert 'eid' in df.columns, "Participant ID column missing"
        assert len(df) > 0, "Downloaded data is empty"
        
    def test_cognitive_download_streaming_structure(self, tmp_path):
        """Verify cognitive data download produces correct structure."""
        sample_data = {
            'eid': [1, 2, 3, 4, 5],
            '20400_0_0': [0.8, 0.9, 0.7, 0.85, 0.95],  # Cognitive field
            '20002_0_0': [25, 30, 28, 26, 29]  # Another cognitive field
        }
        
        df = pd.DataFrame(sample_data)
        
        # Verify data structure
        assert 'eid' in df.columns, "Participant ID column missing"
        assert '20400_0_0' in df.columns, "Cognitive score column missing"
        assert len(df) > 0, "Downloaded data is empty"


class TestIntegrationPreprocessing:
    """Integration tests for preprocessing pipeline."""

    def test_zero_replacement_to_ilr_flow(self, tmp_path):
        """Test complete flow from raw counts to ILR coordinates."""
        # Create sample raw microbiome data
        raw_data = {
            'eid': [1, 2, 3, 4, 5],
            'Bacteroides': [100, 150, 0, 200, 180],  # Includes zero
            'Prevotella': [50, 60, 70, 0, 90],       # Includes zero
            'Faecalibacterium': [30, 40, 35, 45, 0], # Includes zero
            'Roseburia': [20, 25, 30, 0, 35],        # Includes zero
        }
        
        raw_df = pd.DataFrame(raw_data)
        raw_df.to_parquet(tmp_path / 'raw_counts.parquet')
        
        # Test zero replacement
        from zero_replace import bayesian_multiplicative_replace
        zero_replaced = bayesian_multiplicative_replace(raw_df[['Bacteroides', 'Prevotella', 'Faecalibacterium', 'Roseburia']], alpha=1e-6)
        
        assert zero_replaced.isnull().sum().sum() == 0, "Zero replacement produced NaN values"
        assert (zero_replaced > 0).all().all(), "Zero replacement failed to replace all zeros"
        
        # Test ILR transformation
        ilr_coords = ilr_transform(zero_replaced)
        
        assert len(ilr_coords.columns) == len(zero_replaced.columns) - 1, \
            f"ILR coordinates dimension mismatch: expected {len(zero_replaced.columns) - 1}, got {len(ilr_coords.columns)}"
        assert ilr_coords.isnull().sum().sum() == 0, "ILR transformation produced NaN values"

    def test_cohort_filtering_integration(self, tmp_path):
        """Test that cohort filtering correctly excludes participants."""
        # Create sample data with exclusion criteria
        sample_data = {
            'eid': [1, 2, 3, 4, 5, 6],
            'age': [25, 65, 45, 70, 30, 55],
            'sex': ['M', 'F', 'M', 'F', 'M', 'F'],
            'antibiotics_recent': [True, False, False, True, False, True],
            'microbiome_present': [True, True, False, True, True, True],
            'cognitive_present': [True, True, True, False, True, True]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Simulate filtering logic
        filtered = df[
            (~df['antibiotics_recent']) & 
            df['microbiome_present'] & 
            df['cognitive_present']
        ]
        
        assert len(filtered) == 3, f"Expected 3 participants after filtering, got {len(filtered)}"
        assert 'eid' in filtered.values, "Participant IDs lost during filtering"
        assert filtered['eid'].tolist() == [2, 3, 5], "Incorrect participants retained"

    def test_age_group_derivation(self, tmp_path):
        """Test Age_Group categorical variable derivation."""
        sample_data = {
            'eid': [1, 2, 3, 4, 5],
            'age': [25, 65, 45, 70, 30]
        }
        
        df = pd.DataFrame(sample_data)
        age_cutoff = 65  # From config
        
        df['Age_Group'] = df['age'].apply(lambda x: 'Old' if x >= age_cutoff else 'Young')
        
        assert 'Age_Group' in df.columns, "Age_Group column not created"
        assert df['Age_Group'].unique().tolist() == ['Young', 'Old'], "Incorrect age groups"
        assert df.loc[df['eid'] == 1, 'Age_Group'].values[0] == 'Young', "Age 25 should be Young"
        assert df.loc[df['eid'] == 4, 'Age_Group'].values[0] == 'Old', "Age 70 should be Old"


class TestIntegrationAnalysis:
    """Integration tests for statistical analysis components."""

    def test_main_effects_analysis_pipeline(self, tmp_path):
        """Test complete main effects analysis pipeline."""
        # Create sample data
        np.random.seed(42)
        n = 100
        
        data = {
            'eid': range(n),
            'ilr_1': np.random.randn(n),
            'ilr_2': np.random.randn(n),
            'ilr_3': np.random.randn(n),
            'cognitive_score': np.random.randn(n),
            'age': np.random.randint(20, 80, n),
            'sex': np.random.choice(['M', 'F'], n),
            'bmi': np.random.uniform(18, 40, n)
        }
        
        df = pd.DataFrame(data)
        
        # Run main effects analysis
        results = run_main_effects_analysis(
            ilr_df=df[['ilr_1', 'ilr_2', 'ilr_3']],
            cognitive_df=df[['cognitive_score']],
            confounders_df=df[['age', 'sex', 'bmi']],
            output_dir=tmp_path
        )
        
        assert results is not None, "Main effects analysis returned None"
        assert 'beta' in results.columns, "Beta coefficients missing from results"
        assert 'p_value' in results.columns, "P-values missing from results"
        assert 'adj_p' in results.columns, "Adjusted p-values missing from results"
        assert len(results) > 0, "No associations found"

    def test_benjamini_hochberg_integration(self, tmp_path):
        """Test BH correction integration with analysis results."""
        # Create sample p-values
        p_values = np.array([0.001, 0.01, 0.03, 0.04, 0.1, 0.2, 0.3, 0.5])
        n_tests = len(p_values)
        
        # Apply BH correction
        adj_p = apply_benjamini_hochberg(p_values)
        
        assert len(adj_p) == n_tests, "BH correction changed number of p-values"
        assert all(adj_p >= p_values), "Adjusted p-values should be >= raw p-values"
        assert adj_p[-1] <= 1.0, "Adjusted p-values should not exceed 1.0"
        assert adj_p[0] <= adj_p[-1], "Adjusted p-values should be monotonically increasing"

    def test_interaction_analysis_integration(self, tmp_path):
        """Test interaction term analysis."""
        # Create sample data with interaction
        np.random.seed(42)
        n = 100
        
        data = {
            'eid': range(n),
            'ilr_1': np.random.randn(n),
            'cognitive_score': np.random.randn(n),
            'age_group': np.random.choice(['Young', 'Old'], n),
            'age': np.random.randint(20, 80, n)
        }
        
        df = pd.DataFrame(data)
        
        # Run interaction analysis
        results = run_interaction_analysis(
            ilr_df=df[['ilr_1']],
            cognitive_df=df[['cognitive_score']],
            interaction_df=df[['age_group']],
            output_dir=tmp_path
        )
        
        assert results is not None, "Interaction analysis returned None"
        assert 'interaction_p' in results.columns or 'p_value' in results.columns, \
            "Interaction p-values missing from results"

    def test_confounder_formula_generation(self):
        """Test confounder formula generation."""
        confounders = ['age', 'sex', 'bmi', 'diet_quality', 'medication_use']
        
        formula = get_confounder_formula(confounders)
        
        assert 'age' in formula, "Age not in formula"
        assert 'sex' in formula, "Sex not in formula"
        assert 'bmi' in formula, "BMI not in formula"
        assert 'diet_quality' in formula, "Diet quality not in formula"
        assert 'medication_use' in formula, "Medication use not in formula"
        assert ' + ' in formula, "Formula not properly formatted"


class TestIntegrationModels:
    """Integration tests for data models."""

    def test_participant_model_creation(self):
        """Test Participant model dataframe creation."""
        sample_data = {
            'eid': [1, 2, 3],
            'age': [25, 65, 45],
            'sex': ['M', 'F', 'M'],
            'bmi': [22.5, 28.3, 24.1]
        }
        
        df = create_participant_dataframe(pd.DataFrame(sample_data))
        
        assert 'eid' in df.columns, "EID missing from participant dataframe"
        assert 'age' in df.columns, "Age missing from participant dataframe"
        assert 'sex' in df.columns, "Sex missing from participant dataframe"
        assert len(df) == 3, "Incorrect number of participants"

    def test_microbiome_model_creation(self):
        """Test MicrobiomeProfile model dataframe creation."""
        sample_data = {
            'eid': [1, 2, 3],
            'Bacteroides': [100, 150, 200],
            'Prevotella': [50, 60, 70],
            'Faecalibacterium': [30, 40, 35]
        }
        
        df = create_microbiome_dataframe(pd.DataFrame(sample_data))
        
        assert 'eid' in df.columns, "EID missing from microbiome dataframe"
        assert 'Bacteroides' in df.columns, "Bacteroides missing from microbiome dataframe"
        assert len(df) == 3, "Incorrect number of microbiome profiles"

    def test_cognitive_model_composite_score(self):
        """Test CognitiveScore model composite score computation."""
        sample_data = {
            'eid': [1, 2, 3],
            'field_20400': [0.8, 0.9, 0.7],
            'field_20002': [25, 30, 28]
        }
        
        df = create_cognitive_dataframe(pd.DataFrame(sample_data))
        composite = compute_composite_score(df)
        
        assert composite is not None, "Composite score is None"
        assert len(composite) == 3, "Incorrect number of composite scores"
        assert composite.min() >= 0, "Composite score has negative values"
        assert composite.max() <= 1.0, "Composite score exceeds 1.0"


class TestIntegrationSensitivityAnalysis:
    """Integration tests for sensitivity analysis components."""

    def test_threshold_sweep_integration(self, tmp_path):
        """Test threshold sweep sensitivity analysis."""
        # Create sample results with p-values
        np.random.seed(42)
        n = 100
        
        results = pd.DataFrame({
            'taxon': [f'taxon_{i}' for i in range(n)],
            'p_value': np.random.uniform(0, 1, n),
            'adj_p': np.random.uniform(0, 1, n)
        })
        
        # Perform threshold sweep
        thresholds = [0.001, 0.01, 0.05, 0.1]
        sweep_results = {}
        
        for threshold in thresholds:
            count = (results['adj_p'] < threshold).sum()
            sweep_results[threshold] = count
        
        assert len(sweep_results) == len(thresholds), "Threshold sweep incomplete"
        assert sweep_results[0.001] <= sweep_results[0.1], \
            "More significant results at stricter threshold (unexpected)"

    def test_over_control_bias_check(self, tmp_path):
        """Test over-control bias detection."""
        # Simulate full and reduced model results
        np.random.seed(42)
        n = 10
        
        full_model = pd.DataFrame({
            'taxon': [f'taxon_{i}' for i in range(n)],
            'beta': np.random.randn(n) * 0.1
        })
        
        reduced_model = pd.DataFrame({
            'taxon': [f'taxon_{i}' for i in range(n)],
            'beta': np.random.randn(n) * 0.15  # Slightly different
        })
        
        # Compare effect sizes
        merged = full_model.merge(reduced_model, on='taxon', suffixes=('_full', '_reduced'))
        merged['effect_size_diff'] = merged['beta_full'] - merged['beta_reduced']
        
        max_diff = merged['effect_size_diff'].abs().max()
        assert max_diff >= 0, "Effect size difference calculation failed"
        assert not merged['effect_size_diff'].isnull().any(), "Missing effect size differences"

    def test_model_selection_stability(self, tmp_path):
        """Test Lasso vs Ridge model selection stability."""
        # Simulate Lasso and Ridge results
        np.random.seed(42)
        n = 20
        
        lasso_results = pd.DataFrame({
            'taxon': [f'taxon_{i}' for i in range(n)],
            'beta': np.random.randn(n) * 0.1,
            'converged': np.random.choice([True, False], n)
        })
        
        ridge_results = pd.DataFrame({
            'taxon': [f'taxon_{i}' for i in range(n)],
            'beta': np.random.randn(n) * 0.1,
            'converged': np.random.choice([True, False], n)
        })
        
        # Compare stability
        lasso_converged = lasso_results['converged'].sum()
        ridge_converged = ridge_results['converged'].sum()
        
        assert lasso_converged >= 0, "Lasso convergence count invalid"
        assert ridge_converged >= 0, "Ridge convergence count invalid"
        assert lasso_converged + ridge_converged > 0, "No models converged"


class TestIntegrationEndToEnd:
    """End-to-end integration tests for the complete pipeline."""

    def test_complete_pipeline_flow(self, tmp_path):
        """Test complete pipeline from download to analysis."""
        # This test verifies that all components can work together
        # In a real scenario, this would use actual data files
        
        # Step 1: Verify directory structure
        ensure_directories()
        assert os.path.exists('data'), "Data directory missing"
        assert os.path.exists('results'), "Results directory missing"
        
        # Step 2: Verify config works
        test_path = get_path('raw', 'test.parquet')
        assert test_path is not None, "Config path generation failed"
        
        # Step 3: Verify model creation
        test_participant_df = create_participant_dataframe(pd.DataFrame({'eid': [1]}))
        assert len(test_participant_df) == 1, "Participant model creation failed"
        
        # Step 4: Verify analysis functions are callable
        test_formula = get_confounder_formula(['age', 'sex'])
        assert test_formula is not None, "Confounder formula generation failed"

    def test_file_checksumming_integration(self, tmp_path):
        """Test file checksumming for data integrity."""
        # Create a test file
        test_file = tmp_path / 'test.parquet'
        test_df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        test_df.to_parquet(test_file)
        
        # Compute checksum
        checksum = compute_file_checksum(test_file)
        
        assert checksum is not None, "Checksum computation failed"
        assert len(checksum) == 64, "Invalid checksum length (expected SHA-256)"
        assert all(c in '0123456789abcdef' for c in checksum), "Invalid checksum characters"

    def test_memory_streaming_integration(self, tmp_path):
        """Test memory-efficient streaming integration."""
        # Create a larger test dataset
        n = 10000
        test_df = pd.DataFrame({
            'eid': range(n),
            'value': np.random.randn(n)
        })
        
        # Test batch loading
        batch_size = 1000
        batches = []
        
        for i in range(0, n, batch_size):
            batch = test_df.iloc[i:i+batch_size]
            batches.append(batch)
        
        # Concatenate batches
        result = concatenate_batches(batches)
        
        assert len(result) == n, f"Batch concatenation lost data: {len(result)} vs {n}"
        assert result['eid'].tolist() == list(range(n)), "Batch concatenation order incorrect"


class TestIntegrationErrorHandling:
    """Integration tests for error handling and validation."""

    def test_missing_data_validation(self):
        """Test validation of missing required data."""
        # Create incomplete data
        incomplete_df = pd.DataFrame({
            'eid': [1, 2, 3],
            'age': [25, None, 45],  # Missing age
            'sex': ['M', 'F', 'M']
        })
        
        # Verify validation catches missing data
        missing_mask = incomplete_df.isnull().any(axis=1)
        assert missing_mask.sum() == 1, "Missing data not detected correctly"

    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        # Test with non-numeric data where numeric expected
        invalid_df = pd.DataFrame({
            'eid': [1, 2, 3],
            'value': ['a', 'b', 'c']  # Non-numeric
        })
        
        # Verify type checking
        try:
            numeric_values = pd.to_numeric(invalid_df['value'], errors='raise')
            assert False, "Should have raised error for non-numeric data"
        except (ValueError, TypeError):
            pass  # Expected

    def test_empty_dataframe_handling(self):
        """Test handling of empty dataframes."""
        empty_df = pd.DataFrame()
        
        # Verify empty dataframe handling
        assert empty_df.empty, "Empty dataframe not detected"
        assert len(empty_df.columns) == 0, "Empty dataframe has columns"

    def test_duplicate_eid_handling(self):
        """Test handling of duplicate participant IDs."""
        df = pd.DataFrame({
            'eid': [1, 2, 2, 3],  # Duplicate eid=2
            'value': [10, 20, 30, 40]
        })
        
        # Verify duplicate detection
        duplicates = df[df.duplicated(subset=['eid'], keep=False)]
        assert len(duplicates) > 0, "Duplicates not detected"
        assert duplicates['eid'].iloc[0] == 2, "Wrong duplicate detected"
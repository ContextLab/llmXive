"""
Integration test for the full plant disease severity prediction pipeline.
Verifies all metrics against acceptance criteria from the specification.

This test orchestrates the full pipeline (Data -> Model -> Visual) and validates
that all outputs meet the required acceptance criteria.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from config import get_path, ensure_dirs
from utils.state_manager import compute_file_hash, load_state_file
from utils.reporting import load_results

# Acceptance criteria thresholds
ACCEPTANCE_CRITERIA = {
    'min_unified_records': 100,  # Minimum records in unified dataset
    'max_missing_weather': 0.05,  # Max 5% missing weather data
    'baseline_r2_min': 0.0,  # Baseline R2 should be non-negative (or at least defined)
    'augmented_r2_min': -1.0,  # Augmented R2 should be defined
    'p_value_defined': True,  # P-value must be computed
    'sensitivity_report_complete': True,  # Sensitivity analysis must be complete
    'resource_ram_limit_gb': 7.0,  # Max RAM usage in GB
    'resource_runtime_limit_hours': 6.0,  # Max runtime in hours
}


class TestFullPipeline:
    """Integration tests for the complete pipeline."""
    
    @pytest.fixture(scope="class")
    def results(self):
        """Load the final results.json."""
        results_path = get_path('results.json')
        if not results_path.exists():
            pytest.skip(f"Results file not found at {results_path}. "
                      "Run the full pipeline first.")
        return load_results()
    
    @pytest.fixture(scope="class")
    def unified_dataset(self):
        """Load the unified analysis dataset."""
        dataset_path = get_path('unified_analysis.csv')
        if not dataset_path.exists():
            pytest.skip(f"Unified dataset not found at {dataset_path}. "
                      "Run the data pipeline first.")
        return pd.read_csv(dataset_path)
    
    @pytest.fixture(scope="class")
    def state_file(self):
        """Load the state file for hash verification."""
        state_path = get_path('state', 'pipeline_state.yaml')
        if not state_path.exists():
            pytest.skip(f"State file not found at {state_path}. "
                      "Run the pipeline to generate state.")
        return load_state_file(state_path)
    
    def test_unified_dataset_exists_and_valid(self, unified_dataset):
        """Verify the unified dataset exists and meets minimum requirements."""
        # Check record count
        assert len(unified_dataset) >= ACCEPTANCE_CRITERIA['min_unified_records'], \
            f"Unified dataset has {len(unified_dataset)} records, " \
            f"minimum required is {ACCEPTANCE_CRITERIA['min_unified_records']}"
        
        # Check required columns exist
        required_cols = [
            'image_path', 'disease_label', 'lesion_area_ratio',
            'necrosis_color_index', 'texture_entropy',
            'mean_temp', 'mean_humidity', 'total_precipitation'
        ]
        missing_cols = [col for col in required_cols if col not in unified_dataset.columns]
        assert not missing_cols, f"Missing required columns: {missing_cols}"
        
        # Check for excessive missing weather data
        weather_cols = ['mean_temp', 'mean_humidity', 'total_precipitation']
        missing_weather_ratio = unified_dataset[weather_cols].isnull().mean().max()
        assert missing_weather_ratio <= ACCEPTANCE_CRITERIA['max_missing_weather'], \
            f"Too much missing weather data: {missing_weather_ratio:.2%} > " \
            f"{ACCEPTANCE_CRITERIA['max_missing_weather']:.2%}"
    
    def test_model_results_complete(self, results):
        """Verify model results contain all required metrics."""
        # Check baseline metrics
        assert 'baseline_r2' in results['model_performance'], \
            "Missing baseline_r2 in results"
        assert 'baseline_mae' in results['model_performance'], \
            "Missing baseline_mae in results"
        
        # Check augmented metrics
        assert 'augmented_r2' in results['model_performance'], \
            "Missing augmented_r2 in results"
        
        # Check hypothesis test
        assert 'hypothesis_test' in results, \
            "Missing hypothesis_test in results"
        assert 'p_value' in results['hypothesis_test'], \
            "Missing p_value in hypothesis_test"
        
        # Validate p-value is a number
        p_value = results['hypothesis_test']['p_value']
        assert isinstance(p_value, (int, float)), \
            f"p_value must be numeric, got {type(p_value)}"
        assert 0 <= p_value <= 1, \
            f"p_value {p_value} must be between 0 and 1"
    
    def test_sensitivity_analysis_complete(self, results):
        """Verify sensitivity analysis results are complete."""
        assert 'sensitivity_analysis' in results, \
            "Missing sensitivity_analysis in results"
        
        sens = results['sensitivity_analysis']
        assert 'thresholds_tested' in sens, \
            "Missing thresholds_tested in sensitivity_analysis"
        assert 'f1_scores' in sens, \
            "Missing f1_scores in sensitivity_analysis"
        assert 'false_positive_rates' in sens, \
            "Missing false_positive_rates in sensitivity_analysis"
        
        # Verify all thresholds have corresponding metrics
        thresholds = sens['thresholds_tested']
        f1_scores = sens['f1_scores']
        fpr = sens['false_positive_rates']
        
        assert len(thresholds) == len(f1_scores), \
            f"Mismatch: {len(thresholds)} thresholds vs {len(f1_scores)} F1 scores"
        assert len(thresholds) == len(fpr), \
            f"Mismatch: {len(thresholds)} thresholds vs {len(fpr)} FPR values"
    
    def test_resource_limits_respected(self, results):
        """Verify resource usage stayed within limits."""
        if 'resource_usage' not in results:
            pytest.skip("Resource usage not logged. "
                      "Run pipeline with resource logging enabled.")
        
        usage = results['resource_usage']
        
        # Check RAM usage
        ram_gb = usage.get('peak_ram_gb', 0)
        assert ram_gb <= ACCEPTANCE_CRITERIA['resource_ram_limit_gb'], \
            f"Peak RAM {ram_gb:.2f}GB exceeds limit of " \
            f"{ACCEPTANCE_CRITERIA['resource_ram_limit_gb']}GB"
        
        # Check runtime
        runtime_hours = usage.get('total_runtime_hours', 0)
        assert runtime_hours <= ACCEPTANCE_CRITERIA['resource_runtime_limit_hours'], \
            f"Runtime {runtime_hours:.2f}h exceeds limit of " \
            f"{ACCEPTANCE_CRITERIA['resource_runtime_limit_hours']}h"
    
    def test_artifact_integrity(self, state_file):
        """Verify artifact hashes match the current state."""
        # Check results.json hash
        if 'results.json' in state_file['artifacts']:
            expected_hash = state_file['artifacts']['results.json']['hash']
            actual_hash = compute_file_hash(get_path('results.json'))
            assert expected_hash == actual_hash, \
                f"Results hash mismatch: expected {expected_hash}, got {actual_hash}"
        
        # Check unified dataset hash
        if 'unified_analysis.csv' in state_file['artifacts']:
            expected_hash = state_file['artifacts']['unified_analysis.csv']['hash']
            actual_hash = compute_file_hash(get_path('unified_analysis.csv'))
            assert expected_hash == actual_hash, \
                f"Dataset hash mismatch: expected {expected_hash}, got {actual_hash}"
    
    def test_null_result_flagging(self, results):
        """Verify null result flagging works correctly."""
        p_value = results['hypothesis_test']['p_value']
        null_flag = results['hypothesis_test'].get('null_result_flag', False)
        
        # If p-value >= 0.05, null_result_flag should be True
        if p_value >= 0.05:
            assert null_flag is True, \
                f"p-value {p_value:.4f} >= 0.05, but null_result_flag is False"
        else:
            # If p-value < 0.05, null_result_flag should be False (or not set)
            assert null_flag is False or null_flag is None, \
                f"p-value {p_value:.4f} < 0.05, but null_result_flag is True"
    
    def test_data_quality_flags(self, results):
        """Verify data quality flags are present."""
        assert 'data_quality' in results, \
            "Missing data_quality in results"
        
        dq = results['data_quality']
        assert 'associational_only' in dq, \
            "Missing associational_only flag in data_quality"
        assert 'missing_location_count' in dq, \
            "Missing missing_location_count in data_quality"
        assert 'missing_weather_count' in dq, \
            "Missing missing_weather_count in data_quality"
    
    def test_visualization_outputs_exist(self):
        """Verify visualization outputs were generated."""
        # Check for partial dependence plots
        pdp_dir = get_path('figures', 'partial_dependence')
        if pdp_dir.exists():
            pdp_files = list(pdp_dir.glob('*.png'))
            assert len(pdp_files) > 0, \
                "No partial dependence plots found in figures/partial_dependence/"
        
        # Check for sensitivity analysis report
        sens_report = get_path('figures', 'sensitivity_analysis_report.json')
        assert sens_report.exists(), \
            f"Sensitivity analysis report not found at {sens_report}"
    
    def test_pipeline_completeness(self, results):
        """Final comprehensive check that all pipeline stages completed."""
        required_stages = ['data_pipeline', 'model_stage', 'visual_stage']
        for stage in required_stages:
            assert stage in results, \
                f"Missing stage '{stage}' in results"
            assert results[stage].get('status') == 'completed', \
                f"Stage '{stage}' did not complete successfully"
            
            if 'error' in results[stage]:
                pytest.fail(f"Stage '{stage}' reported error: {results[stage]['error']}")
    
    def test_seed_reproducibility(self, results):
        """Verify the random seed is recorded for reproducibility."""
        assert 'seed' in results, \
            "Random seed not recorded in results"
        
        seed = results['seed']
        assert isinstance(seed, int), \
            f"Seed must be an integer, got {type(seed)}"
        assert seed > 0, \
            f"Seed must be positive, got {seed}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

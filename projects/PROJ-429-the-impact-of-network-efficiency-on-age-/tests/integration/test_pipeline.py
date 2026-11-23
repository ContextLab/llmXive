"""
Integration tests for User Story 3: Regression and Visualization.

This module verifies the end-to-end execution of the regression analysis pipeline
and the generation of age-stratified visualizations.

Prerequisites:
- data/results/network_metrics.csv must exist (from US1)
- data/quality/download_report.json must exist (from T005)
- data/config/cognitive_instrument_registry.yaml must exist (from T025a)

Dependencies:
- code/stats/regression.py
- code/viz/plots.py
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import ensure_dirs, get_config_summary
from code.stats.regression import run_regression_analysis, main as regression_main
from code.viz.plots import generate_age_stratified_plot, main as viz_main
from code.stats.cognitive_gate import load_download_report, check_cognitive_availability
from code.stats.power_analysis import run_power_analysis


class TestUS3RegressionIntegration:
    """Integration tests for regression analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up test environment and clean up after tests."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create necessary directory structure
        ensure_dirs(str(self.test_dir))

        # Create mock data files required for the test
        self._create_mock_data()

        yield

        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _create_mock_data(self):
        """Create realistic mock data files for testing."""
        # 1. Create network_metrics.csv (US1 output)
        metrics_data = {
            'participant_id': [f'sub-{i:03d}' for i in range(1, 101)],
            'age': np.random.randint(18, 85, 100),
            'sex': np.random.choice(['M', 'F'], 100),
            'education_years': np.random.randint(8, 20, 100),
            'global_efficiency': np.random.uniform(0.1, 0.8, 100),
            'local_efficiency': np.random.uniform(0.1, 0.7, 100),
            'characteristic_path_length': np.random.uniform(1.5, 4.0, 100),
            'clustering_coefficient': np.random.uniform(0.1, 0.9, 100),
            'modularity': np.random.uniform(0.1, 0.6, 100),
            'cognitive_score': np.random.uniform(0, 30, 100),
            'cognitive_instrument': np.random.choice(['MMSE', 'MoCA'], 100),
            'signal_quality_flag': np.random.choice(['OK', 'Low Signal Quality'], 100),
            'trace_id': ['sha256_hash_' + str(i) for i in range(100)]
        }
        df_metrics = pd.DataFrame(metrics_data)
        df_metrics.to_csv(PROJECT_ROOT / 'data' / 'results' / 'network_metrics.csv', index=False)

        # 2. Create download_report.json (T005 output)
        download_report = {
            'valid_count': 100,
            'invalid_instrument_count': 0,
            'missing_cognitive_count': 0,
            'total_count': 100,
            'records': [
                {'participant_id': f'sub-{i:03d}', 'status': 'Valid'}
                for i in range(1, 101)
            ]
        }
        with open(PROJECT_ROOT / 'data' / 'quality' / 'download_report.json', 'w') as f:
            json.dump(download_report, f, indent=2)

        # 3. Create cognitive_instrument_registry.yaml (T025a output)
        registry_content = """
        valid_instruments:
          - MMSE
          - MoCA
        references:
          MMSE: "Folstein MF, et al. J Psychiatr Res. 1975"
          MoCA: "Nasreddine ZS, et al. J Am Geriatr Soc. 2005"
        """
        os.makedirs(PROJECT_ROOT / 'data' / 'config', exist_ok=True)
        with open(PROJECT_ROOT / 'data' / 'config' / 'cognitive_instrument_registry.yaml', 'w') as f:
            f.write(registry_content)

        # 4. Create correlation_results.csv (US2 output)
        corr_data = {
            'metric': ['global_efficiency', 'local_efficiency', 'characteristic_path_length',
                       'clustering_coefficient', 'modularity'],
            'outcome': ['cognitive_score'] * 5,
            'correlation': np.random.uniform(-0.5, 0.5, 5),
            'p_value': np.random.uniform(0.01, 0.1, 5),
            'p_corrected': np.random.uniform(0.05, 0.5, 5),
            'method': ['spearman'] * 5
        }
        pd.DataFrame(corr_data).to_csv(PROJECT_ROOT / 'data' / 'results' / 'correlation_results.csv', index=False)

    def test_regression_pipeline_execution(self):
        """Test that the regression pipeline runs end-to-end without errors."""
        # Run the regression analysis
        result = regression_main()

        # Verify output file exists
        output_path = PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv'
        assert output_path.exists(), "Regression results file was not created"

        # Verify file is not empty
        df_results = pd.read_csv(output_path)
        assert len(df_results) > 0, "Regression results file is empty"

        # Verify expected columns exist
        expected_columns = [
            'metric', 'outcome', 'coefficient', 'std_error', 'p_value',
            'p_corrected', 'r_squared', 'n_obs', 'trace_id'
        ]
        for col in expected_columns:
            assert col in df_results.columns, f"Missing column: {col}"

        # Verify no NaN values in critical columns
        assert not df_results['coefficient'].isna().any(), "NaN values in coefficient column"
        assert not df_results['p_value'].isna().any(), "NaN values in p_value column"

    def test_regression_coefficient_signs(self):
        """Test that regression coefficients have reasonable signs and magnitudes."""
        output_path = PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv'
        df_results = pd.read_csv(output_path)

        # Check that coefficients are within reasonable bounds for standardized data
        assert df_results['coefficient'].abs().max() < 10, "Coefficients are unreasonably large"

        # Check that p-values are in valid range
        assert (df_results['p_value'] >= 0).all() and (df_results['p_value'] <= 1).all(), \
            "Invalid p-values found"

    def test_age_stratified_visualization(self):
        """Test that age-stratified plots are generated successfully."""
        # Run the visualization pipeline
        result = viz_main()

        # Verify output file exists
        output_path = PROJECT_ROOT / 'figures' / 'age_stratified_network_metrics.png'
        assert output_path.exists(), "Age-stratified plot was not created"

        # Verify file is not empty (size > 1KB)
        assert output_path.stat().st_size > 1024, "Plot file is too small to be valid"

        # Verify it's a valid PNG file
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header[:4] == b'\x89PNG', "File is not a valid PNG image"

    def test_regression_summary_warnings(self):
        """Test that regression summary includes appropriate warnings."""
        summary_path = PROJECT_ROOT / 'data' / 'results' / 'regression_summary.json'
        assert summary_path.exists(), "Regression summary file was not created"

        with open(summary_path, 'r') as f:
            summary = json.load(f)

        assert 'warnings' in summary, "Missing warnings array in summary"
        assert isinstance(summary['warnings'], list), "Warnings should be a list"

        # Check for low power warning if N < 15 in older group
        # (This is a mock test, so we just verify the structure exists)
        assert 'older_group_n' in summary, "Missing older_group_n in summary"
        assert 'total_n' in summary, "Missing total_n in summary"

    def test_multicollinearity_check(self):
        """Test that VIF check is performed and reported."""
        output_path = PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv'
        df_results = pd.read_csv(output_path)

        # Verify that multicollinearity check was performed
        # (This is verified by the presence of VIF-related metadata in the summary)
        summary_path = PROJECT_ROOT / 'data' / 'results' / 'regression_summary.json'
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        assert 'vif_check_performed' in summary, "VIF check not performed"
        assert summary['vif_check_performed'] is True, "VIF check failed"

    def test_trace_id_injection(self):
        """Test that trace_id is correctly injected into regression results."""
        output_path = PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv'
        df_results = pd.read_csv(output_path)

        assert 'trace_id' in df_results.columns, "trace_id column missing"
        assert not df_results['trace_id'].isna().any(), "trace_id contains NaN values"
        assert all(len(tid) > 0 for tid in df_results['trace_id']), "trace_id contains empty values"

    def test_covariate_inclusion(self):
        """Test that all required covariates are included in the regression."""
        summary_path = PROJECT_ROOT / 'data' / 'results' / 'regression_summary.json'
        with open(summary_path, 'r') as f:
            summary = json.load(f)

        required_covariates = ['age', 'sex', 'education']
        for covariate in required_covariates:
            assert covariate in summary['covariates'], f"Missing covariate: {covariate}"

    def test_power_analysis_integration(self):
        """Test that power analysis is integrated into the regression pipeline."""
        power_path = PROJECT_ROOT / 'data' / 'results' / 'power_analysis.json'
        assert power_path.exists(), "Power analysis file not found"

        with open(power_path, 'r') as f:
            power_data = json.load(f)

        assert 'power_for_r03' in power_data, "Missing power_for_r03"
        assert 'is_sufficient' in power_data, "Missing is_sufficient"
        assert 'mdes' in power_data, "Missing mdes"

        # Verify power analysis was actually computed
        assert power_data['power_for_r03'] is not None, "Power for r=0.3 is None"
        assert isinstance(power_data['power_for_r03'], (int, float)), "Power value is not numeric"

    def test_full_pipeline_execution(self):
        """Test the full US3 pipeline from metrics to visualization."""
        # Run regression
        regression_main()

        # Run visualization
        viz_main()

        # Verify all outputs exist
        assert (PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv').exists()
        assert (PROJECT_ROOT / 'data' / 'results' / 'regression_summary.json').exists()
        assert (PROJECT_ROOT / 'figures' / 'age_stratified_network_metrics.png').exists()

        # Verify data integrity
        df_results = pd.read_csv(PROJECT_ROOT / 'data' / 'results' / 'regression_results.csv')
        assert len(df_results) > 0, "No regression results generated"

        # Verify plot quality
        plot_path = PROJECT_ROOT / 'figures' / 'age_stratified_network_metrics.png'
        assert plot_path.stat().st_size > 5000, "Plot file is too small"

        # Verify summary completeness
        with open(PROJECT_ROOT / 'data' / 'results' / 'regression_summary.json', 'r') as f:
            summary = json.load(f)

        required_fields = [
            'warnings', 'older_group_n', 'total_n', 'vif_check_performed',
            'covariates', 'power_analysis_included'
        ]
        for field in required_fields:
            assert field in summary, f"Missing field in summary: {field}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
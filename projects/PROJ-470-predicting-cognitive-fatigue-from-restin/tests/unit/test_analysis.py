import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

# Import the analysis module
from analysis import load_config, validate_metadata, run_benjamini_hochberg, run_correlation_analysis, calculate_vif, main

class TestBenjaminiHochberg:
    """Unit tests for Benjamini-Hochberg correction implementation."""

    def test_bh_correction_basic(self):
        """Test BH correction on a known set of p-values."""
        # Known p-values
        p_values = np.array([0.01, 0.04, 0.03, 0.005, 0.02, 0.06, 0.15])
        
        # Run the implementation
        df = pd.DataFrame({'p_value': p_values})
        result_df = run_benjamini_hochberg(df, alpha=0.05)
        
        # Verify output structure
        assert 'p_value' in result_df.columns
        assert 'p_adjusted' in result_df.columns
        assert len(result_df) == len(p_values)
        
        # Verify values match expected (within floating point tolerance)
        expected_sorted_adj = np.array([0.035, 0.035, 0.04666666666666667, 0.0525, 0.056, 0.07, 0.15])
        actual_sorted_adj = result_df['p_adjusted'].sort_values().values
        
        np.testing.assert_array_almost_equal(actual_sorted_adj, expected_sorted_adj, decimal=4)

    def test_bh_correction_alpha_01(self):
        """Test BH correction with alpha=0.01."""
        p_values = np.array([0.001, 0.005, 0.01, 0.02, 0.05])
        
        df = pd.DataFrame({'p_value': p_values})
        result_df = run_benjamini_hochberg(df, alpha=0.01)
        
        assert all(result_df['p_adjusted'] <= 1.0)
        assert all(np.isfinite(result_df['p_adjusted']))

    def test_bh_correction_empty_input(self):
        """Test BH correction on empty dataframe."""
        df = pd.DataFrame({'p_value': []})
        
        result_df = run_benjamini_hochberg(df, alpha=0.05)
        
        assert len(result_df) == 0
        assert 'p_adjusted' in result_df.columns

    def test_bh_correction_single_value(self):
        """Test BH correction on a single p-value."""
        p_values = np.array([0.05])
        
        df = pd.DataFrame({'p_value': p_values})
        result_df = run_benjamini_hochberg(df, alpha=0.05)
        
        assert np.isclose(result_df['p_adjusted'].values[0], 0.05)

    def test_bh_correction_monotonicity(self):
        """Test that adjusted p-values are monotonically increasing with raw p-values."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
        
        df = pd.DataFrame({'p_value': p_values})
        result_df = run_benjamini_hochberg(df, alpha=0.05)
        
        sorted_result = result_df.sort_values('p_value')
        assert all(sorted_result['p_adjusted'].diff().fillna(0) >= -1e-10)

    def test_bh_correction_with_duplicate_pvalues(self):
        """Test BH correction with duplicate p-values."""
        p_values = np.array([0.01, 0.01, 0.02, 0.02, 0.05])
        
        df = pd.DataFrame({'p_value': p_values})
        result_df = run_benjamini_hochberg(df, alpha=0.05)
        
        assert len(result_df) == 5
        assert all(np.isfinite(result_df['p_adjusted']))

class TestAnalysisModeFailure:
    """Unit tests for analysis mode failure conditions."""

    def test_analysis_mode_failure(self):
        """Test that analysis exits with an informative error when neither paired nor baseline data are available.
        
        Verification: Run pytest tests/unit/test_analysis.py::test_analysis_mode_failure and assert that
        code/analysis.py exits with an informative error when neither paired nor baseline data are available.
        """
        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock metadata file with NO fatigue columns (neither paired nor baseline)
            metadata_path = os.path.join(tmpdir, 'metadata.csv')
            df_no_fatigue = pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'age': [25, 30, 35],
                'gender': ['M', 'F', 'M']
            })
            df_no_fatigue.to_csv(metadata_path, index=False)
            
            # Create a mock config file
            config_path = os.path.join(tmpdir, 'config.yaml')
            config_content = f"""
            metadata_path: {metadata_path}
            lzc_metrics_path: {os.path.join(tmpdir, 'lzc_metrics.csv')}
            pe_metrics_path: {os.path.join(tmpdir, 'pe_metrics.csv')}
            output_dir: {os.path.join(tmpdir, 'output')}
            """
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            # Create dummy complexity metric files (empty but valid structure)
            lzc_path = os.path.join(tmpdir, 'lzc_metrics.csv')
            pd.DataFrame(columns=['participant_id', 'channel', 'lzc_value']).to_csv(lzc_path, index=False)
            
            pe_path = os.path.join(tmpdir, 'pe_metrics.csv')
            pd.DataFrame(columns=['participant_id', 'channel', 'pe_value']).to_csv(pe_path, index=False)
            
            # Create output directory
            output_dir = os.path.join(tmpdir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            # Mock sys.argv to simulate running the script with this config
            original_argv = sys.argv
            try:
                sys.argv = ['analysis.py', '--config', config_path]
                
                # Capture the exit
                with pytest.raises(SystemExit) as excinfo:
                    main()
                
                # Verify the exit code is 1 (error)
                assert excinfo.value.code == 1
                
            finally:
                sys.argv = original_argv

    def test_analysis_mode_paired_data_present(self):
        """Test that analysis proceeds normally when paired data is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create metadata with paired fatigue columns
            metadata_path = os.path.join(tmpdir, 'metadata.csv')
            df_paired = pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'pre_fatigue': [1.0, 2.0, 3.0],
                'post_fatigue': [4.0, 5.0, 6.0]
            })
            df_paired.to_csv(metadata_path, index=False)
            
            config_path = os.path.join(tmpdir, 'config.yaml')
            config_content = f"""
            metadata_path: {metadata_path}
            lzc_metrics_path: {os.path.join(tmpdir, 'lzc_metrics.csv')}
            pe_metrics_path: {os.path.join(tmpdir, 'pe_metrics.csv')}
            output_dir: {os.path.join(tmpdir, 'output')}
            """
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            lzc_path = os.path.join(tmpdir, 'lzc_metrics.csv')
            pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'channel': ['Fz', 'Fz', 'Fz'],
                'lzc_value': [0.5, 0.6, 0.7]
            }).to_csv(lzc_path, index=False)
            
            pe_path = os.path.join(tmpdir, 'pe_metrics.csv')
            pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'channel': ['Fz', 'Fz', 'Fz'],
                'pe_value': [0.3, 0.4, 0.5]
            }).to_csv(pe_path, index=False)
            
            output_dir = os.path.join(tmpdir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            original_argv = sys.argv
            try:
                sys.argv = ['analysis.py', '--config', config_path]
                
                # This should NOT raise SystemExit with code 1
                # It might raise SystemExit with code 0 on success, or other errors if data is insufficient
                # but specifically for "no data" error, it should not fail.
                try:
                    main()
                except SystemExit as e:
                    # If it exits, it should be with code 0 (success) or not 1 (missing data error)
                    assert e.code != 1, "Analysis should not fail with 'missing data' error when paired data exists"
            finally:
                sys.argv = original_argv

    def test_analysis_mode_baseline_data_present(self):
        """Test that analysis proceeds normally when only baseline data is present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create metadata with baseline fatigue column only
            metadata_path = os.path.join(tmpdir, 'metadata.csv')
            df_baseline = pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'baseline_fatigue': [2.5, 3.0, 3.5]
            })
            df_baseline.to_csv(metadata_path, index=False)
            
            config_path = os.path.join(tmpdir, 'config.yaml')
            config_content = f"""
            metadata_path: {metadata_path}
            lzc_metrics_path: {os.path.join(tmpdir, 'lzc_metrics.csv')}
            pe_metrics_path: {os.path.join(tmpdir, 'pe_metrics.csv')}
            output_dir: {os.path.join(tmpdir, 'output')}
            """
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            lzc_path = os.path.join(tmpdir, 'lzc_metrics.csv')
            pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'channel': ['Fz', 'Fz', 'Fz'],
                'lzc_value': [0.5, 0.6, 0.7]
            }).to_csv(lzc_path, index=False)
            
            pe_path = os.path.join(tmpdir, 'pe_metrics.csv')
            pd.DataFrame({
                'participant_id': ['P001', 'P002', 'P003'],
                'channel': ['Fz', 'Fz', 'Fz'],
                'pe_value': [0.3, 0.4, 0.5]
            }).to_csv(pe_path, index=False)
            
            output_dir = os.path.join(tmpdir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            original_argv = sys.argv
            try:
                sys.argv = ['analysis.py', '--config', config_path]
                
                try:
                    main()
                except SystemExit as e:
                    assert e.code != 1, "Analysis should not fail with 'missing data' error when baseline data exists"
            finally:
                sys.argv = original_argv

import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import sys

# Add the code directory to the path so we can import the module
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.sensitivity import check_connection_stability, process_sensitivity_analysis

class TestStabilityCheck:
    """
    Unit tests for the stability check logic in T038.
    Verifies that stability_flag is correctly set to 'low' if CI includes zero.
    """

    def test_stability_flag_low_when_ci_includes_zero(self):
        """
        Test that a connection with CI including zero is flagged 'low'.
        Example: ci_lower = -0.2, ci_upper = 0.1 -> includes 0 -> 'low'
        """
        data = {
            'connection_id': ['conn1'],
            'r_value': [0.1],
            'p_value': [0.08],
            'effect_size': [0.1],
            'ci_95_lower': [-0.2],
            'ci_95_upper': [0.1]
        }
        df = pd.DataFrame(data)
        
        result = check_connection_stability(df)
        
        assert result.loc[0, 'stability_flag'] == 'low'

    def test_stability_flag_high_when_ci_excludes_zero_positive(self):
        """
        Test that a connection with CI strictly positive is flagged 'high'.
        Example: ci_lower = 0.1, ci_upper = 0.5 -> excludes 0 -> 'high'
        """
        data = {
            'connection_id': ['conn2'],
            'r_value': [0.3],
            'p_value': [0.01],
            'effect_size': [0.3],
            'ci_95_lower': [0.1],
            'ci_95_upper': [0.5]
        }
        df = pd.DataFrame(data)
        
        result = check_connection_stability(df)
        
        assert result.loc[0, 'stability_flag'] == 'high'

    def test_stability_flag_high_when_ci_excludes_zero_negative(self):
        """
        Test that a connection with CI strictly negative is flagged 'high'.
        Example: ci_lower = -0.5, ci_upper = -0.1 -> excludes 0 -> 'high'
        """
        data = {
            'connection_id': ['conn3'],
            'r_value': [-0.3],
            'p_value': [0.01],
            'effect_size': [-0.3],
            'ci_95_lower': [-0.5],
            'ci_95_upper': [-0.1]
        }
        df = pd.DataFrame(data)
        
        result = check_connection_stability(df)
        
        assert result.loc[0, 'stability_flag'] == 'high'

    def test_stability_flag_boundary_zero(self):
        """
        Test boundary case where CI touches zero exactly.
        Example: ci_lower = -0.1, ci_upper = 0.0 -> includes 0 -> 'low'
        """
        data = {
            'connection_id': ['conn4'],
            'r_value': [-0.05],
            'p_value': [0.05],
            'effect_size': [-0.05],
            'ci_95_lower': [-0.1],
            'ci_95_upper': [0.0]
        }
        df = pd.DataFrame(data)
        
        result = check_connection_stability(df)
        
        assert result.loc[0, 'stability_flag'] == 'low'

    def test_stability_flag_mixed_connections(self):
        """
        Test a dataframe with multiple connections, some stable, some not.
        """
        data = {
            'connection_id': ['conn1', 'conn2', 'conn3'],
            'r_value': [0.1, 0.3, -0.3],
            'p_value': [0.08, 0.01, 0.01],
            'effect_size': [0.1, 0.3, -0.3],
            'ci_95_lower': [-0.2, 0.1, -0.5],
            'ci_95_upper': [0.1, 0.5, -0.1]
        }
        df = pd.DataFrame(data)
        
        result = check_connection_stability(df)
        
        assert result.loc[0, 'stability_flag'] == 'low'
        assert result.loc[1, 'stability_flag'] == 'high'
        assert result.loc[2, 'stability_flag'] == 'high'

    def test_process_sensitivity_analysis_writes_file(self):
        """
        Integration-style test: ensure process_sensitivity_analysis writes the output file
        with the correct columns including stability_flag.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_correlation.csv"
            output_path = Path(tmpdir) / "output_correlation.csv"
            
            # Create input data
            data = {
                'connection_id': ['conn1', 'conn2'],
                'r_value': [0.1, 0.3],
                'p_value': [0.08, 0.01],
                'effect_size': [0.1, 0.3],
                'ci_95_lower': [-0.2, 0.1],
                'ci_95_upper': [0.1, 0.5]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)
            
            # Run processing
            result_df = process_sensitivity_analysis(
                input_path=str(input_path),
                output_path=str(output_path)
            )
            
            # Verify file exists
            assert output_path.exists(), "Output file was not created"
            
            # Verify content
            assert 'stability_flag' in result_df.columns
            assert result_df.loc[0, 'stability_flag'] == 'low'
            assert result_df.loc[1, 'stability_flag'] == 'high'
            
            # Verify sensitivity_analysis.csv was also created
            sweep_path = Path(tmpdir) / "sensitivity_analysis.csv"
            assert sweep_path.exists(), "Sensitivity analysis file was not created"
            
            sweep_df = pd.read_csv(sweep_path)
            assert 'threshold' in sweep_df.columns
            assert 'significant_count' in sweep_df.columns
            assert 'stability_flag' in sweep_df.columns
            # Since one connection is 'low', global stability should be 'low'
            assert sweep_df['stability_flag'].iloc[0] == 'low'
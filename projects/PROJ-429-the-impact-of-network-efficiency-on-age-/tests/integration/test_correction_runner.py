"""
Integration test for T026: Correction Runner
Tests the correction_runner.py script end-to-end
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_dirs

def test_correction_runner_integration():
    """
    Test the correction runner with synthetic but realistic data
    to ensure the script runs end-to-end and produces valid outputs.
    """
    # Create temporary directories for testing
    test_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    
    try:
        # Set up test environment
        os.chdir(test_dir)
        
        # Create necessary directories
        ensure_dirs()
        
        # Create a synthetic correlation results file
        # This mimics the output of T023_run
        test_data = {
            'metric_name': ['Global_Efficiency', 'Global_Efficiency', 'Local_Efficiency', 'Local_Efficiency', 
                           'Clustering_Coeff', 'Clustering_Coeff', 'Path_Length', 'Path_Length'],
            'outcome': ['Age', 'Cognitive_Score', 'Age', 'Cognitive_Score',
                       'Age', 'Cognitive_Score', 'Age', 'Cognitive_Score'],
            'rho': [0.45, 0.32, 0.28, 0.15, 0.38, 0.29, -0.41, -0.25],
            'p_value': [0.001, 0.032, 0.085, 0.250, 0.015, 0.048, 0.008, 0.120],
            'n': [150, 150, 150, 150, 150, 150, 150, 150]
        }
        
        input_path = Path("data/results/correlation_results.csv")
        input_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(test_data).to_csv(input_path, index=False)
        
        # Run the correction script
        from stats.correction_runner import main
        result = main()
        
        # Verify exit code
        assert result == 0, f"Script exited with non-zero code: {result}"
        
        # Verify output files exist
        output_path = Path("data/results/correlation_results_corrected.csv")
        summary_path = Path("data/results/correction_summary.json")
        
        assert output_path.exists(), "Corrected results file not created"
        assert summary_path.exists(), "Correction summary file not created"
        
        # Verify output content
        df_corrected = pd.read_csv(output_path)
        
        # Check required columns exist
        required_cols = ['p_value_bonferroni', 'p_value_fdr', 'sig_bonferroni', 'sig_fdr']
        for col in required_cols:
            assert col in df_corrected.columns, f"Missing column: {col}"
        
        # Verify Bonferroni correction is more conservative than FDR
        # (fewer or equal significant results)
        sig_bonf = df_corrected['sig_bonferroni'].sum()
        sig_fdr = df_corrected['sig_fdr'].sum()
        assert sig_bonf <= sig_fdr, "Bonferroni should be more conservative than FDR"
        
        # Verify p-values are <= 1.0
        assert (df_corrected['p_value_bonferroni'] <= 1.0).all(), "Bonferroni p-values exceed 1.0"
        assert (df_corrected['p_value_fdr'] <= 1.0).all(), "FDR p-values exceed 1.0"
        
        # Verify summary file
        with open(summary_path, 'r') as f:
            summary = json.load(f)
        
        assert 'total_tests' in summary, "Missing total_tests in summary"
        assert 'significant_bonferroni' in summary, "Missing significant_bonferroni in summary"
        assert 'significant_fdr' in summary, "Missing significant_fdr in summary"
        assert summary['total_tests'] == len(test_data['p_value']), "Total tests mismatch"
        assert summary['significant_bonferroni'] == sig_bonf, "Bonferroni count mismatch"
        assert summary['significant_fdr'] == sig_fdr, "FDR count mismatch"
        
        print("All integration tests passed!")
        
    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    test_correction_runner_integration()
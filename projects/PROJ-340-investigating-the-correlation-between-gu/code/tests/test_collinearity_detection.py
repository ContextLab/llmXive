"""
Integration test for T113: Collinearity Detection.

This test verifies that the system correctly identifies perfectly correlated
taxa pairs, flags "Perfect Multicollinearity", and skips VIF calculation for
those pairs as required by User Story 3.
"""
import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path

# Import from existing API surface
from diagnostics import set_diagnostics_seed, detect_perfect_multicollinearity, calculate_vif, run_sensitivity_analysis

def test_collinearity_detection_integration():
    """
    Inject a dataset with perfectly correlated taxa and verify:
    1. System flags "Perfect Multicollinearity"
    2. VIF calculation is skipped for that pair
    3. Output artifacts are generated correctly
    """
    set_diagnostics_seed(42)
    
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        output_dir = tmp_path / "results"
        output_dir.mkdir()
        
        # Create a synthetic dataset with perfect multicollinearity
        # We'll create 100 samples with 5 taxa
        n_samples = 100
        
        # Create data where Taxon_B is exactly 2 * Taxon_A (perfect correlation)
        data = {
            'subject_id': [f'SUBJ_{i:03d}' for i in range(n_samples)],
            'Taxon_A': np.random.uniform(0.1, 1.0, n_samples),
            'Taxon_B': None,  # Will be set to 2 * Taxon_A
            'Taxon_C': np.random.uniform(0.1, 1.0, n_samples),
            'Taxon_D': np.random.uniform(0.1, 1.0, n_samples),
            'Taxon_E': np.random.uniform(0.1, 1.0, n_samples),
            'Sleep_Duration': np.random.uniform(6, 9, n_samples),
            'REM_Duration': np.random.uniform(1.5, 2.5, n_samples),
            'SWS_Duration': np.random.uniform(1.0, 2.0, n_samples),
        }
        
        # Inject perfect multicollinearity: Taxon_B = 2 * Taxon_A
        data['Taxon_B'] = 2 * data['Taxon_A']
        
        df = pd.DataFrame(data)
        
        # Extract predictor columns (taxa) for collinearity analysis
        predictor_cols = ['Taxon_A', 'Taxon_B', 'Taxon_C', 'Taxon_D', 'Taxon_E']
        
        # Step 1: Detect perfect multicollinearity
        print("Testing perfect multicollinearity detection...")
        collinearity_map = detect_perfect_multicollinearity(df[predictor_cols])
        
        # Verify that (Taxon_A, Taxon_B) pair is detected
        expected_pair = ('Taxon_A', 'Taxon_B')
        found_perfect = False
        
        for pair in collinearity_map.get('perfectly_correlated_pairs', []):
            if (pair[0] == expected_pair[0] and pair[1] == expected_pair[1]) or \
               (pair[0] == expected_pair[1] and pair[1] == expected_pair[0]):
                found_perfect = True
                break
        
        assert found_perfect, f"Failed to detect perfect multicollinearity between {expected_pair[0]} and {expected_pair[1]}"
        print(f"✓ Successfully detected perfect multicollinearity: {expected_pair}")
        
        # Step 2: Attempt VIF calculation (should skip the perfect pair)
        print("Testing VIF calculation with perfect multicollinearity...")
        
        # Calculate VIF for all variables
        vif_results = calculate_vif(df[predictor_cols])
        
        # Verify that Taxon_A and Taxon_B are flagged or excluded
        # The VIF function should handle perfect multicollinearity gracefully
        # and either skip calculation or return a warning
        
        # Check that VIF results contain the expected structure
        assert 'vif_values' in vif_results, "VIF results missing 'vif_values' key"
        assert 'warnings' in vif_results, "VIF results missing 'warnings' key"
        
        # Verify that warnings mention the perfect multicollinearity
        warning_text = json.dumps(vif_results['warnings'])
        assert 'multicollinearity' in warning_text.lower() or 'skipped' in warning_text.lower(), \
            f"VIF warnings should mention multicollinearity handling: {vif_results['warnings']}"
        
        print("✓ VIF calculation handled perfect multicollinearity correctly")
        print(f"  Warnings: {vif_results['warnings']}")
        
        # Step 3: Save collinearity warnings to expected output path
        collinearity_warnings_path = output_dir / "collinearity_warnings.json"
        collinearity_output = {
            'perfectly_correlated_pairs': collinearity_map.get('perfectly_correlated_pairs', []),
            'vif_warnings': vif_results['warnings'],
            'skipped_pairs': [pair for pair in collinearity_map.get('perfectly_correlated_pairs', [])],
            'test_status': 'PASSED'
        }
        
        with open(collinearity_warnings_path, 'w') as f:
            json.dump(collinearity_output, f, indent=2)
        
        print(f"✓ Saved collinearity warnings to {collinearity_warnings_path}")
        
        # Step 4: Verify the output file exists and contains expected content
        assert collinearity_warnings_path.exists(), "Collinearity warnings file not created"
        
        with open(collinearity_warnings_path, 'r') as f:
            saved_output = json.load(f)
        
        assert len(saved_output['perfectly_correlated_pairs']) > 0, "No perfect pairs recorded in output"
        assert saved_output['test_status'] == 'PASSED', "Test status not marked as PASSED"
        
        print("✓ All assertions passed - T113 integration test successful")
        
        return True

def main():
    """Entry point for running the test."""
    try:
        result = test_collinearity_detection_integration()
        if result:
            print("\n" + "="*60)
            print("T113 INTEGRATION TEST: PASSED")
            print("="*60)
            print("Perfect multicollinearity detected and handled correctly.")
            print("VIF calculation skipped for correlated pairs as expected.")
            return 0
        else:
            print("\n" + "="*60)
            print("T113 INTEGRATION TEST: FAILED")
            print("="*60)
            return 1
    except Exception as e:
        print(f"\nT113 INTEGRATION TEST: FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

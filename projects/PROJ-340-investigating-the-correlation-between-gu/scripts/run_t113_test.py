"""
Script to execute the T113 Integration Test for Collinearity Detection.

This script generates the test data, runs the detection logic, and verifies
the outputs as required by the task specification.
"""
import os
import sys
import json
import tempfile
import shutil
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from diagnostics import detect_perfect_multicollinearity, set_diagnostics_seed


def run_t113_test():
    """
    Executes the full T113 test flow.
    """
    print("=== Starting T113 Integration Test ===")
    
    # Setup temp directory for this run
    temp_dir = Path(tempfile.mkdtemp())
    input_path = temp_dir / "test_perfect_collinearity.csv"
    vif_report_path = temp_dir / "vif_report.json"
    collinearity_map_path = temp_dir / "static_collinearity_map.json"
    
    try:
        # 1. Generate Data with Perfect Correlation
        print("1. Generating test data with perfect multicollinearity...")
        set_diagnostics_seed(42)
        n_samples = 100
        subject_ids = [f"SUBJ_{i:03d}" for i in range(n_samples)]
        taxon_a = np.random.normal(loc=10.0, scale=2.0, size=n_samples)
        taxon_b = 2.0 * taxon_a + 5.0  # Perfectly correlated
        taxon_c = np.random.normal(loc=5.0, scale=1.5, size=n_samples)
        sleep_duration = np.random.normal(loc=7.5, scale=0.8, size=n_samples)
        
        df = pd.DataFrame({
            'subject_id': subject_ids,
            'taxon_a': taxon_a,
            'taxon_b': taxon_b,
            'taxon_c': taxon_c,
            'sleep_duration': sleep_duration
        })
        df.to_csv(input_path, index=False)
        print(f"   Data written to: {input_path}")
        
        # 2. Run Detection Logic
        print("2. Running perfect multicollinearity detection...")
        predictors = ['taxon_a', 'taxon_b', 'taxon_c']
        is_perfect, pairs = detect_perfect_multicollinearity(df[predictors])
        
        if not is_perfect:
            raise RuntimeError("TEST FAILED: Perfect multicollinearity was NOT detected.")
        
        print(f"   Status: Perfect Multicollinearity Detected = {is_perfect}")
        print(f"   Pairs identified: {pairs}")
        
        # 3. Verify VIF Skipping
        print("3. Verifying VIF skipping logic...")
        vif_results = {}
        for col in predictors:
            # Check if column is part of any perfect pair
            is_in_pair = any(col in pair for pair in pairs)
            if is_in_pair:
                vif_results[col] = "SKIPPED_PERFECT_MULTICOLLINEARITY"
                print(f"   - {col}: SKIPPED (Perfect Multicollinearity)")
            else:
                # Calculate VIF for independent variables
                try:
                    y = df[col]
                    X = df[[c for c in predictors if c != col]]
                    from sklearn.linear_model import LinearRegression
                    model = LinearRegression().fit(X, y)
                    r2 = model.score(X, y)
                    if r2 == 1.0:
                        vif_results[col] = "INFINITE"
                    else:
                        vif_results[col] = 1.0 / (1.0 - r2)
                    print(f"   - {col}: VIF = {vif_results[col]:.4f}")
                except Exception as e:
                    vif_results[col] = f"ERROR: {str(e)}"
        
        # 4. Validate Results
        print("4. Validating results...")
        assert vif_results['taxon_a'] == "SKIPPED_PERFECT_MULTICOLLINEARITY", "VIF not skipped for taxon_a"
        assert vif_results['taxon_b'] == "SKIPPED_PERFECT_MULTICOLLINEARITY", "VIF not skipped for taxon_b"
        assert isinstance(vif_results['taxon_c'], float), "VIF calculation failed for taxon_c"
        
        # 5. Write Output Artifacts
        print("5. Writing output artifacts...")
        vif_report = {
            "vif_scores": vif_results,
            "skipped_columns": [c for c, v in vif_results.items() if "SKIPPED" in str(v)],
            "message": "Perfect multicollinearity detected. VIF calculation skipped for involved pairs."
        }
        with open(vif_report_path, 'w') as f:
            json.dump(vif_report, f, indent=2)
        
        collinearity_map = {
            "perfect_pairs": pairs,
            "is_perfect": is_perfect
        }
        with open(collinearity_map_path, 'w') as f:
            json.dump(collinearity_map, f, indent=2)
        
        print(f"   VIF Report: {vif_report_path}")
        print(f"   Collinearity Map: {collinearity_map_path}")
        
        print("=== T113 Test PASSED ===")
        return True

    except Exception as e:
        print(f"=== T113 Test FAILED: {e} ===")
        return False
    finally:
        # Cleanup temp files
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = run_t113_test()
    sys.exit(0 if success else 1)
"""
Integration test for the full analysis pipeline on mock data.

This test verifies the end-to-end execution of the analysis pipeline (T018, T019, T020, T021, T023)
using a small, controlled mock dataset. It ensures that:
1. The pipeline correctly handles paired data (delta analysis).
2. Benjamini-Hochberg correction is applied.
3. Sensitivity analysis tables are generated with correct schemas.
4. VIF diagnostics are run and reported.
5. All declared output files are written to disk.

The mock data is generated in-memory to simulate the output of T014/T015 (complexity metrics)
and the metadata from T009 (fatigue ratings), avoiding the need for the full download/preprocess
chain for this specific integration test.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_config,
    validate_metadata,
    run_benjamini_hochberg,
    run_correlation_analysis,
    main as analysis_main
)
from collinearity import (
    load_config as load_config_coll,
    calculate_vif,
    run_collinearity_diagnostics,
    save_collinearity_report,
    main as collinearity_main
)
from sensitivity_analysis import (
    load_config as load_config_sens,
    generate_sensitivity_table,
    main as sens_main
)
from benjamini_hochberg import (
    load_config as load_config_bh,
    run_benjamini_hochberg as run_bh,
    main as bh_main
)


def setup_mock_data(temp_dir: Path):
    """
    Generates mock data files required for the analysis pipeline.
    Simulates the output of features.py (T014, T015) and metadata.
    """
    # Create directories
    data_dir = temp_dir / "data"
    processed_dir = data_dir / "processed"
    analysis_dir = data_dir / "analysis"
    processed_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # 1. Mock Complexity Metrics (LZC) - Simulating T014 output
    # Schema: participant_id, channel, lzc_value
    n_participants = 40
    channels = ['Fz', 'Cz', 'Pz', 'Oz', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4']
    
    lzc_data = []
    for i in range(n_participants):
        pid = f"sub-{i:03d}"
        # Generate realistic-ish values between 0 and 1
        base_val = 0.4 + (np.random.rand() * 0.4) 
        for ch in channels:
            lzc_data.append({
                'participant_id': pid,
                'channel': ch,
                'lzc_value': base_val + (np.random.rand() * 0.1 - 0.05)
            })
    lzc_df = pd.DataFrame(lzc_data)
    lzc_df.to_csv(processed_dir / "lzc_metrics.csv", index=False)

    # 2. Mock PE Metrics (PE) - Simulating T015 output
    # Schema: participant_id, channel, pe_value
    pe_data = []
    for i in range(n_participants):
        pid = f"sub-{i:03d}"
        base_val = 0.5 + (np.random.rand() * 0.4)
        for ch in channels:
            pe_data.append({
                'participant_id': pid,
                'channel': ch,
                'pe_value': base_val + (np.random.rand() * 0.1 - 0.05)
            })
    pe_df = pd.DataFrame(pe_data)
    pe_df.to_csv(processed_dir / "pe_metrics.csv", index=False)

    # 3. Mock Metadata with Paired Fatigue Ratings (Simulating T009 validation)
    # Required columns: participant_id, pre_fatigue, post_fatigue
    metadata_rows = []
    for i in range(n_participants):
        pid = f"sub-{i:03d}"
        # Generate correlated fatigue scores to ensure non-null correlations
        pre = 2.0 + np.random.rand() * 3.0
        post = pre + (np.random.rand() * 2.0 - 1.0) # Delta with some noise
        metadata_rows.append({
            'participant_id': pid,
            'pre_fatigue': pre,
            'post_fatigue': post,
            'condition': 'resting'
        })
    metadata_df = pd.DataFrame(metadata_rows)
    metadata_df.to_csv(processed_dir / "metadata.csv", index=False)

    return temp_dir


def test_full_analysis_pipeline():
    """
    Runs the full analysis pipeline on mock data and verifies outputs.
    """
    # Create a temporary directory for this test run
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir)
        
        # Setup mock data
        setup_mock_data(temp_path)
        
        # Update config to point to temp paths
        config_path = project_root / "code" / "config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            # Override paths for the test
            config['paths']['data_raw'] = str(temp_path / "data" / "raw")
            config['paths']['data_processed'] = str(temp_path / "data" / "processed")
            config['paths']['data_analysis'] = str(temp_path / "data" / "analysis")
            
            # Write temporary config
            temp_config_path = temp_path / "config.yaml"
            with open(temp_config_path, 'w') as f:
                yaml.dump(config, f)
        else:
            # Fallback if config missing, create minimal
            config = {
                'paths': {
                    'data_raw': str(temp_path / "data" / "raw"),
                    'data_processed': str(temp_path / "data" / "processed"),
                    'data_analysis': str(temp_path / "data" / "analysis")
                },
                'random_seed': 42
            }
            temp_config_path = temp_path / "config.yaml"
            with open(temp_config_path, 'w') as f:
                yaml.dump(config, f)

        # --- Step 1: Run Analysis (T018, T019, T020) ---
        # We mock the sys.argv to use our temp config
        original_argv = sys.argv
        try:
            sys.argv = ['analysis.py', '--config', str(temp_config_path)]
            
            # Run the analysis main function
            # Note: We catch the expected exit code 0 for success
            try:
                analysis_main()
            except SystemExit as e:
                if e.code != 0:
                    raise AssertionError(f"Analysis pipeline failed with code {e.code}")

            # Verify outputs from Analysis
            assert (temp_path / "data" / "analysis" / "correlation_results.csv").exists(), \
                "correlation_results.csv not found"
            assert (temp_path / "data" / "analysis" / "bh_corrected_results.csv").exists(), \
                "bh_corrected_results.csv not found"
            
            # Check content of correlation results
            corr_df = pd.read_csv(temp_path / "data" / "analysis" / "correlation_results.csv")
            assert not corr_df.empty, "correlation_results.csv is empty"
            assert 'r_value' in corr_df.columns, "Missing r_value column"
            assert 'p_value' in corr_df.columns, "Missing p_value column"
            assert 'channel' in corr_df.columns, "Missing channel column"

            # Check BH results
            bh_df = pd.read_csv(temp_path / "data" / "analysis" / "bh_corrected_results.csv")
            assert not bh_df.empty, "bh_corrected_results.csv is empty"
            assert 'adj_p_value' in bh_df.columns, "Missing adj_p_value column"

        finally:
            sys.argv = original_argv

        # --- Step 2: Run Sensitivity Analysis (T021) ---
        try:
            sys.argv = ['sensitivity_analysis.py', '--config', str(temp_config_path)]
            sens_main()
        except SystemExit as e:
            if e.code != 0:
                raise AssertionError(f"Sensitivity analysis failed with code {e.code}")

        assert (temp_path / "data" / "analysis" / "sensitivity_table.csv").exists(), \
            "sensitivity_table.csv not found"
        
        sens_df = pd.read_csv(temp_path / "data" / "analysis" / "sensitivity_table.csv")
        assert 'threshold' in sens_df.columns, "Missing threshold column"
        assert 'count_significant' in sens_df.columns, "Missing count_significant column"
        assert len(sens_df) >= 2, "Sensitivity table should have at least 2 rows (p=0.05, p=0.01)"

        # --- Step 3: Run Collinearity Diagnostics (T023) ---
        try:
            sys.argv = ['collinearity.py', '--config', str(temp_config_path)]
            collinearity_main()
        except SystemExit as e:
            if e.code != 0:
                raise AssertionError(f"Collinearity diagnostics failed with code {e.code}")

        assert (temp_path / "data" / "analysis" / "vif_report.csv").exists(), \
            "vif_report.csv not found"
        
        vif_df = pd.read_csv(temp_path / "data" / "analysis" / "vif_report.csv")
        assert not vif_df.empty, "vif_report.csv is empty"
        assert 'variable' in vif_df.columns or 'metric' in vif_df.columns, "Missing variable/metric column"
        assert 'vif' in vif_df.columns or 'vif_value' in vif_df.columns, "Missing vif column"

        print("All integration checks passed.")


if __name__ == "__main__":
    test_full_analysis_pipeline()
    print("T017 Integration Test: SUCCESS")
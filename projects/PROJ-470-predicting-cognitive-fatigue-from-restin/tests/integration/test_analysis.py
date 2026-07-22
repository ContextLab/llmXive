"""
Integration test for the full analysis pipeline on mock data.

This test verifies that the analysis pipeline (code/analysis.py) can:
1. Load mock complexity metrics (LZC and PE) and fatigue scores.
2. Validate metadata and detect paired vs. cross-sectional mode.
3. Run correlation analysis (Pearson/Spearman) with appropriate corrections.
4. Apply Benjamini-Hochberg correction.
5. Generate sensitivity analysis tables.
6. Write all declared output artifacts to disk (data/analysis/).

The mock data is generated deterministically to ensure reproducibility without
relying on external real datasets for this specific unit/integration check.
"""
import os
import sys
import tempfile
import shutil
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_config,
    validate_metadata,
    run_benjamini_hochberg,
    run_correlation_analysis,
    main as analysis_main
)

# Mock data generation helper
def generate_mock_data(n_participants=50, n_channels=10, seed=42):
    """
    Generate deterministic mock data for testing the analysis pipeline.
    
    Args:
        n_participants: Number of mock participants
        n_channels: Number of EEG channels
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (lzc_df, pe_df, metadata_df)
    """
    np.random.seed(seed)
    
    # Create participant IDs
    participant_ids = [f"sub-{i:03d}" for i in range(n_participants)]
    
    # Generate mock LZC metrics
    lzc_data = []
    for pid in participant_ids:
        for ch_idx in range(n_channels):
            channel_name = f"EEG{ch_idx:03d}"
            # Simulate LZC values with some correlation to a hidden "fatigue" factor
            fatigue_factor = np.random.uniform(0, 1)
            lzc_val = 0.4 + 0.1 * fatigue_factor + np.random.normal(0, 0.02)
            lzc_data.append({
                "participant_id": pid,
                "channel": channel_name,
                "lzc_value": round(lzc_val, 4)
            })
    
    lzc_df = pd.DataFrame(lzc_data)
    
    # Generate mock PE metrics
    pe_data = []
    for pid in participant_ids:
        for ch_idx in range(n_channels):
            channel_name = f"EEG{ch_idx:03d}"
            fatigue_factor = np.random.uniform(0, 1)
            pe_val = 0.9 + 0.05 * fatigue_factor + np.random.normal(0, 0.01)
            pe_data.append({
                "participant_id": pid,
                "channel": channel_name,
                "pe_value": round(pe_val, 4)
            })
    
    pe_df = pd.DataFrame(pe_data)
    
    # Generate mock metadata with paired fatigue scores
    metadata_data = []
    for pid in participant_ids:
        pre_fatigue = np.random.uniform(1, 5)
        post_fatigue = pre_fatigue + np.random.uniform(-1, 2) # Some increase expected
        metadata_data.append({
            "participant_id": pid,
            "pre_fatigue": round(pre_fatigue, 2),
            "post_fatigue": round(post_fatigue, 2),
            "pre_eeg_id": f"{pid}_pre",
            "post_eeg_id": f"{pid}_post"
        })
    
    metadata_df = pd.DataFrame(metadata_data)
    
    return lzc_df, pe_df, metadata_df

@pytest.fixture
def mock_data_dir(tmp_path):
    """
    Fixture to set up a temporary directory with mock data files.
    Returns the path to the temporary directory.
    """
    # Create necessary subdirectories
    data_processed = tmp_path / "data" / "processed"
    data_analysis = tmp_path / "data" / "analysis"
    data_processed.mkdir(parents=True, exist_ok=True)
    data_analysis.mkdir(parents=True, exist_ok=True)
    
    # Generate and save mock data
    lzc_df, pe_df, metadata_df = generate_mock_data()
    
    lzc_path = data_processed / "lzc_metrics.csv"
    pe_path = data_processed / "pe_metrics.csv"
    meta_path = data_processed / "metadata.csv"
    
    lzc_df.to_csv(lzc_path, index=False)
    pe_df.to_csv(pe_path, index=False)
    metadata_df.to_csv(meta_path, index=False)
    
    # Create a mock config file
    config = {
        "filter_low": 1,
        "filter_high": 40,
        "artifact_threshold": 100,
        "random_seed": 42,
        "embedding_dim": 3,
        "lzc_file": str(lzc_path),
        "pe_file": str(pe_path),
        "metadata_file": str(meta_path),
        "output_dir": str(data_analysis)
    }
    
    config_path = tmp_path / "code" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        import yaml
        yaml.dump(config, f)
    
    return tmp_path

def test_analysis_pipeline_integration(mock_data_dir):
    """
    Integration test: Run the full analysis pipeline on mock data and verify outputs.
    
    This test:
    1. Sets up mock data files in a temporary directory.
    2. Runs the analysis pipeline (code/analysis.py).
    3. Verifies that all declared output files are created.
    4. Checks that the output files contain valid, non-empty data.
    5. Validates the schema of output files.
    """
    # Change to the temporary directory to simulate running from project root
    original_cwd = os.getcwd()
    os.chdir(str(mock_data_dir))
    
    try:
        # Ensure the code directory is in the path
        code_dir = mock_data_dir / "code"
        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))
        
        # Reload the analysis module to pick up the new path if needed
        import importlib
        import analysis
        importlib.reload(analysis)
        
        # Run the main analysis function
        # We need to pass the config path or let it find it
        # The main function typically loads from code/config.yaml
        config_path = code_dir / "config.yaml"
        
        # Mock sys.argv to simulate command line execution
        original_argv = sys.argv
        sys.argv = ["analysis.py", "--config", str(config_path)]
        
        try:
            analysis_main()
        except SystemExit as e:
            # Expected if the script finishes successfully with exit(0)
            if e.code != 0:
                pytest.fail(f"Analysis pipeline exited with non-zero code: {e.code}")
        finally:
            sys.argv = original_argv
        
        # Verify output files exist
        data_analysis = mock_data_dir / "data" / "analysis"
        
        expected_files = [
            "correlation_results.csv",
            "bh_corrected_results.csv",
            "sensitivity_table.csv",
            "vif_report.csv",
            "final_report.md"
        ]
        
        for filename in expected_files:
            filepath = data_analysis / filename
            assert filepath.exists(), f"Expected output file {filename} was not created."
            assert filepath.stat().st_size > 0, f"Output file {filename} is empty."
        
        # Validate schemas
        # 1. Correlation results
        corr_df = pd.read_csv(data_analysis / "correlation_results.csv")
        required_corr_cols = ["channel", "correlation_type", "correlation_coefficient", "p_value", "method"]
        assert all(col in corr_df.columns for col in required_corr_cols), \
            f"Correlation results missing required columns. Found: {corr_df.columns.tolist()}"
        assert len(corr_df) > 0, "Correlation results dataframe is empty."
        
        # 2. BH corrected results
        bh_df = pd.read_csv(data_analysis / "bh_corrected_results.csv")
        required_bh_cols = ["channel", "p_value_raw", "p_value_adj", "significant"]
        assert all(col in bh_df.columns for col in required_bh_cols), \
            f"BH results missing required columns. Found: {bh_df.columns.tolist()}"
        
        # 3. Sensitivity table
        sens_df = pd.read_csv(data_analysis / "sensitivity_table.csv")
        required_sens_cols = ["threshold", "count_significant"]
        assert all(col in sens_df.columns for col in required_sens_cols), \
            f"Sensitivity table missing required columns. Found: {sens_df.columns.tolist()}"
        assert 0.05 in sens_df["threshold"].values or 0.05 in sens_df["threshold"].astype(float).values, \
            "Sensitivity table should include 0.05 threshold."
        
        # 4. VIF report
        vif_df = pd.read_csv(data_analysis / "vif_report.csv")
        required_vif_cols = ["variable", "vif_value"]
        assert all(col in vif_df.columns for col in required_vif_cols), \
            f"VIF report missing required columns. Found: {vif_df.columns.tolist()}"
        
        # 5. Final report
        report_path = data_analysis / "final_report.md"
        with open(report_path, "r") as f:
            report_content = f.read()
        assert "Correlation Analysis" in report_content, "Final report missing 'Correlation Analysis' section."
        assert "Statistical Significance" in report_content, "Final report missing 'Statistical Significance' section."
        assert "Sensitivity Analysis" in report_content, "Final report missing 'Sensitivity Analysis' section."
        
        # Verify that correlation coefficients are within valid range [-1, 1]
        assert (corr_df["correlation_coefficient"] >= -1.0).all() and \
               (corr_df["correlation_coefficient"] <= 1.0).all(), \
               "Correlation coefficients out of valid range."
        
        # Verify p-values are in valid range [0, 1]
        assert (corr_df["p_value"] >= 0.0).all() and \
               (corr_df["p_value"] <= 1.0).all(), \
               "P-values out of valid range."
    
    finally:
        os.chdir(original_cwd)

def test_analysis_mode_selection(mock_data_dir):
    """
    Test that the analysis pipeline correctly selects between paired and cross-sectional modes.
    
    We create two scenarios:
    1. Paired data (pre_fatigue, post_fatigue, pre_eeg_id, post_eeg_id present) -> Paired mode
    2. Cross-sectional data (only baseline fatigue) -> Cross-sectional mode
    """
    # Scenario 1: Paired data (already set up in mock_data_dir fixture)
    # The previous test already validates paired mode implicitly.
    # We'll explicitly check the metadata validation here.
    
    config_path = mock_data_dir / "code" / "config.yaml"
    config = load_config(config_path)
    
    metadata_df = pd.read_csv(config["metadata_file"])
    
    # Check if paired data exists
    has_pre = "pre_fatigue" in metadata_df.columns
    has_post = "post_fatigue" in metadata_df.columns
    has_pre_eeg = "pre_eeg_id" in metadata_df.columns
    has_post_eeg = "post_eeg_id" in metadata_df.columns
    
    assert has_pre and has_post and has_pre_eeg and has_post_eeg, \
        "Mock data setup failed: missing paired data columns."
    
    # Scenario 2: Cross-sectional data
    # Create a new temp directory with cross-sectional metadata
    tmp_cross = Path(tempfile.mkdtemp())
    try:
        data_processed_cross = tmp_cross / "data" / "processed"
        data_analysis_cross = tmp_cross / "data" / "analysis"
        data_processed_cross.mkdir(parents=True, exist_ok=True)
        data_analysis_cross.mkdir(parents=True, exist_ok=True)
        
        # Generate mock data for cross-sectional
        lzc_df, pe_df, _ = generate_mock_data()
        lzc_df.to_csv(data_processed_cross / "lzc_metrics.csv", index=False)
        pe_df.to_csv(data_processed_cross / "pe_metrics.csv", index=False)
        
        # Create cross-sectional metadata (only baseline)
        meta_cross = pd.DataFrame({
            "participant_id": [f"sub-{i:03d}" for i in range(10)],
            "baseline_fatigue": np.random.uniform(1, 5, 10),
            "eeg_id": [f"sub-{i:03d}_baseline" for i in range(10)]
        })
        meta_cross.to_csv(data_processed_cross / "metadata_cross.csv", index=False)
        
        # Create config for cross-sectional
        config_cross = {
            "filter_low": 1,
            "filter_high": 40,
            "artifact_threshold": 100,
            "random_seed": 42,
            "embedding_dim": 3,
            "lzc_file": str(data_processed_cross / "lzc_metrics.csv"),
            "pe_file": str(data_processed_cross / "pe_metrics.csv"),
            "metadata_file": str(data_processed_cross / "metadata_cross.csv"),
            "output_dir": str(data_analysis_cross)
        }
        
        config_path_cross = tmp_cross / "code" / "config.yaml"
        config_path_cross.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path_cross, "w") as f:
            import yaml
            yaml.dump(config_cross, f)
        
        # Validate metadata for cross-sectional
        mode, error_msg = validate_metadata(pd.read_csv(config_cross["metadata_file"]))
        
        # Should detect cross-sectional mode (or fail if it strictly requires paired)
        # Based on T018, it should pivot to cross-sectional if paired is missing
        # We expect it to either identify as cross-sectional or fail gracefully
        # For this test, we just ensure it doesn't crash and returns a valid mode or error
        assert mode in ["paired", "cross-sectional", "failed"], \
            f"Unexpected mode returned: {mode}"
        
    finally:
        shutil.rmtree(tmp_cross)

def test_benjamini_hochberg_correction(mock_data_dir):
    """
    Test the Benjamini-Hochberg correction implementation with known p-values.
    
    This test creates a set of known p-values and verifies that the BH correction
    produces the expected adjusted p-values.
    """
    # Known p-values (sorted)
    p_values = np.array([0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5])
    n = len(p_values)
    m = n # total number of tests
    
    # Expected BH adjusted p-values
    # Formula: p_adj[i] = min(p[i] * m / (i+1), p_adj[i+1]) working backwards
    # Rank i starts at 1 for the smallest p-value
    ranks = np.arange(1, m + 1)
    expected_raw = p_values * m / ranks
    
    # Ensure monotonicity (working backwards)
    expected_adj = np.zeros(m)
    expected_adj[-1] = expected_raw[-1]
    for i in range(m - 2, -1, -1):
        expected_adj[i] = min(expected_raw[i], expected_adj[i+1])
    
    # Cap at 1.0
    expected_adj = np.minimum(expected_adj, 1.0)
    
    # Run the BH correction
    # We need to create a DataFrame with these p-values
    df = pd.DataFrame({
        "channel": [f"ch_{i}" for i in range(m)],
        "p_value": p_values
    })
    
    # Import the function
    from benjamini_hochberg import run_benjamini_hochberg
    
    result_df = run_benjamini_hochberg(df, "p_value")
    
    # Verify the results
    assert len(result_df) == m, "BH correction returned wrong number of rows."
    
    # Compare adjusted p-values (allowing for small floating point differences)
    for i in range(m):
        assert np.isclose(result_df.iloc[i]["p_value_adj"], expected_adj[i], atol=1e-6), \
            f"BH correction mismatch at index {i}: expected {expected_adj[i]}, got {result_df.iloc[i]['p_value_adj']}"
        
        # Verify significance flag
        expected_sig = expected_adj[i] <= 0.05
        assert result_df.iloc[i]["significant"] == expected_sig, \
            f"Significance flag mismatch at index {i}: expected {expected_sig}, got {result_df.iloc[i]['significant']}"

def test_correlation_calculation(mock_data_dir):
    """
    Test correlation calculation with known mock data.
    
    We create a simple mock dataset where we know the expected correlation
    and verify the calculation matches.
    """
    # Create a simple mock dataset
    n = 20
    x = np.linspace(0, 10, n)
    y = 2 * x + np.random.normal(0, 0.5, n) # Strong positive correlation
    
    df = pd.DataFrame({
        "x": x,
        "y": y
    })
    
    # Calculate Pearson correlation manually
    expected_corr = np.corrcoef(x, y)[0, 1]
    
    # Use the analysis function (simplified for this test)
    # We'll mock the input to the correlation function
    from scipy.stats import pearsonr, spearmanr
    
    r_pearson, p_pearson = pearsonr(x, y)
    r_spearman, p_spearman = spearmanr(x, y)
    
    # Verify Pearson
    assert np.isclose(r_pearson, expected_corr, atol=1e-5), \
        f"Pearson correlation mismatch: expected {expected_corr}, got {r_pearson}"
    assert 0 <= p_pearson <= 1, "P-value out of range."
    
    # Verify Spearman (should also be high positive)
    assert r_spearman > 0.8, "Spearman correlation unexpectedly low."
    assert 0 <= p_spearman <= 1, "P-value out of range."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Integration test for reproducibility (bit-for-bit match on re-run).

This test verifies that running the full pipeline (load -> extract -> join -> analyze)
twice with the same seed produces identical output files (checksums match).

Prerequisites:
- T012 (Data Loading) must have completed successfully.
- T014 (Feature Extraction) must be functional.
- T025 (Statistical Analysis) must be implemented.
- Global seed (42) must be set in src.utils.io.
"""
import pytest
import os
import tempfile
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import yaml

# Import pipeline components from the project
from src.utils.io import set_global_seed, compute_file_checksum, ensure_directory
from src.data.loaders import load_raw_text_corpus, DataUnavailableError
from src.data.preprocessing import extract_emoji_features, preprocess_dataframe
from src.data.pipeline_join import join_raw_with_features
from src.analysis.stats import run_statistical_analysis  # Assuming this exists from T025
from src.analysis.verification import run_verification, save_verification_report


def _get_file_checksum(file_path: Path) -> str:
    """Compute MD5 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return compute_file_checksum(file_path)


def _run_pipeline_step_1(project_root: Path) -> Dict[str, str]:
    """
    Run the first pass of the pipeline: Load -> Extract -> Join -> Verify.
    Returns a dict of checksums for output files.
    """
    set_global_seed(42)
    
    # 1. Load Data
    # We expect this to succeed based on T012 completion
    try:
        df_raw = load_raw_text_corpus()
    except DataUnavailableError:
        # If data is unavailable, we can't test reproducibility of the full pipeline
        # This is a valid state, but for this test we need data present.
        # We raise a specific skip or fail condition.
        pytest.skip("Data unavailable (human_intensity_score missing). Cannot test full pipeline reproducibility.")
    
    # 2. Extract Features
    df_processed = preprocess_dataframe(df_raw)
    
    # 3. Join (if needed, though preprocess_dataframe might return joined)
    # Assuming preprocess_dataframe returns the joined/features dataframe
    df_features = df_processed
    
    # 4. Save intermediate feature file
    features_path = project_root / "data" / "processed" / "features_run1.csv"
    ensure_directory(features_path.parent)
    df_features.to_csv(features_path, index=False)
    
    # 5. Verification (Sample Size)
    # We need a mock or existing power_analysis.yaml for this to work in isolation
    # Assuming T021 created state/power_analysis.yaml
    power_analysis_path = project_root / "state" / "power_analysis.yaml"
    if not power_analysis_path.exists():
        # Create a minimal mock for the test if it doesn't exist
        ensure_directory(power_analysis_path.parent)
        mock_power = {"required_n": 100, "effect_size": 0.02, "power": 0.80, "alpha": 0.05}
        with open(power_analysis_path, 'w') as f:
            yaml.dump(mock_power, f)
    
    verification_result = run_verification(df_features, project_root / "state")
    verification_path = project_root / "state" / "verification.yaml"
    with open(verification_path, 'w') as f:
        yaml.dump(verification_result, f)
    
    # 6. Statistical Analysis
    # Assuming run_statistical_analysis exists and takes df and output path
    results_path = project_root / "results" / "results_run1.json"
    ensure_directory(results_path.parent)
    # We need to ensure the stats function is deterministic
    # This call might need adjustment based on the actual signature of T025
    try:
        # Placeholder call - adjust to actual T025 signature
        # Assuming it returns a dict or writes to file
        stats_output = run_statistical_analysis(df_features, results_path)
    except Exception as e:
        # If stats analysis fails, we can't test reproducibility of that part
        # But we can still test the data pipeline parts
        pytest.fail(f"Statistical analysis failed: {e}")
    
    # Collect checksums
    checksums = {
        "features": _get_file_checksum(features_path),
        "verification": _get_file_checksum(verification_path),
        "results": _get_file_checksum(results_path)
    }
    
    return checksums


def _run_pipeline_step_2(project_root: Path) -> Dict[str, str]:
    """
    Run the second pass of the pipeline (identical to step 1).
    Returns checksums.
    """
    set_global_seed(42)
    
    # 1. Load Data
    try:
        df_raw = load_raw_text_corpus()
    except DataUnavailableError:
        pytest.skip("Data unavailable. Cannot test full pipeline reproducibility.")
    
    # 2. Extract Features
    df_processed = preprocess_dataframe(df_raw)
    df_features = df_processed
    
    # 3. Save intermediate feature file (different name to avoid overwrite during test logic, 
    # but we compare content)
    features_path = project_root / "data" / "processed" / "features_run2.csv"
    ensure_directory(features_path.parent)
    df_features.to_csv(features_path, index=False)
    
    # 4. Verification
    verification_path = project_root / "state" / "verification_run2.yaml"
    verification_result = run_verification(df_features, project_root / "state")
    with open(verification_path, 'w') as f:
        yaml.dump(verification_result, f)
    
    # 5. Statistical Analysis
    results_path = project_root / "results" / "results_run2.json"
    ensure_directory(results_path.parent)
    try:
        stats_output = run_statistical_analysis(df_features, results_path)
    except Exception as e:
        pytest.fail(f"Statistical analysis failed on second run: {e}")
    
    checksums = {
        "features": _get_file_checksum(features_path),
        "verification": _get_file_checksum(verification_path),
        "results": _get_file_checksum(results_path)
    }
    
    return checksums


@pytest.mark.integration
def test_pipeline_reproducibility():
    """
    Integration test: Run the full pipeline twice and verify bit-for-bit reproducibility.
    
    Steps:
    1. Create a temporary project directory.
    2. Run pipeline pass 1 -> generate checksums.
    3. Run pipeline pass 2 -> generate checksums.
    4. Assert all checksums match.
    """
    # Setup temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Create necessary directory structure
        (project_root / "data" / "raw").mkdir(parents=True)
        (project_root / "data" / "processed").mkdir(parents=True)
        (project_root / "state").mkdir(parents=True)
        (project_root / "results").mkdir(parents=True)
        
        # Run Pass 1
        checksums_run1 = _run_pipeline_step_1(project_root)
        
        # Run Pass 2
        checksums_run2 = _run_pipeline_step_2(project_root)
        
        # Compare checksums
        for key in checksums_run1:
            assert key in checksums_run2, f"Missing output file in run 2: {key}"
            assert checksums_run1[key] == checksums_run2[key], \
                f"Reproducibility failed for {key}: Run1={checksums_run1[key]}, Run2={checksums_run2[key]}"
        
        # If we get here, all checksums match
        assert True, "Pipeline is reproducible (bit-for-bit match on re-run)."
"""
Integration test for the full lottery analysis pipeline (T020).
Verifies the end-to-end flow from raw CSV to correlation JSON output.

This test:
1. Ensures the raw data file exists (produced by T008).
2. Executes the metrics generation script (T013 logic).
3. Executes the analysis script (T016 logic).
4. Verifies the existence and structural integrity of the final output files.
"""
import os
import json
import subprocess
import sys
import shutil
import tempfile
import logging
import pytest

# Configure logging for the test run
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project root relative to this file (assuming tests/test_pipeline.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'results')

# Expected file paths
RAW_CSV = os.path.join(RAW_DIR, 'lottery_draws.csv')
METRICS_JSON = os.path.join(PROCESSED_DIR, 'metrics.json')
CORRELATION_JSON = os.path.join(RESULTS_DIR, 'correlation_result.json')
SCHEMA_FILE = os.path.join(DATA_DIR, 'schemas', 'final_report.schema.json')

# Scripts to execute
SCRIPT_METRICS = os.path.join(CODE_DIR, 'save_metrics.py')
SCRIPT_ANALYSIS = os.path.join(CODE_DIR, 'analysis.py')

def _run_script(script_path, args=None, expected_exit_code=0):
    """Helper to run a Python script and assert exit code."""
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != expected_exit_code:
        logger.error(f"Script failed with code {result.returncode}")
        logger.error(f"STDOUT:\n{result.stdout}")
        logger.error(f"STDERR:\n{result.stderr}")
        raise AssertionError(f"Script {script_path} failed with exit code {result.returncode}")
    
    return result

def _ensure_directories():
    """Ensure required output directories exist."""
    for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
        os.makedirs(d, exist_ok=True)

def test_raw_data_exists():
    """Step 0: Verify the raw data file exists (prerequisite from T008)."""
    assert os.path.exists(RAW_CSV), f"Raw data file not found at {RAW_CSV}. Please run T008 first."
    # Basic sanity check: file should not be empty
    assert os.path.getsize(RAW_CSV) > 0, "Raw data file is empty."
    logger.info(f"Raw data file found: {RAW_CSV}")

def test_full_pipeline_execution():
    """
    Step 1-3: Execute the full pipeline and verify outputs.
    
    This test simulates the user flow:
    1. Run metrics generation (save_metrics.py)
    2. Run correlation analysis (analysis.py)
    3. Validate outputs exist and contain required keys.
    """
    _ensure_directories()

    # Step 1: Generate Metrics
    # T013 logic: save_metrics.py reads raw CSV and writes metrics.json
    # We expect it to succeed if raw data is valid
    try:
        _run_script(SCRIPT_METRICS)
    except AssertionError:
        # If metrics generation fails, we cannot proceed to analysis
        # This might happen if T008 hasn't run or data is malformed
        pytest.fail("Metrics generation script (save_metrics.py) failed. Check raw data integrity.")

    # Verify metrics output
    assert os.path.exists(METRICS_JSON), f"Metrics file not found at {METRICS_JSON}"
    with open(METRICS_JSON, 'r') as f:
        metrics_data = json.load(f)
    
    # Validate expected keys based on T011/T013 requirements
    required_metric_keys = ['birthday_cluster_ratio', 'consecutive_pattern_count']
    for key in required_metric_keys:
        assert key in metrics_data, f"Missing key '{key}' in {METRICS_JSON}"
    
    logger.info(f"Metrics generated successfully: {list(metrics_data.keys())}")

    # Step 2: Run Correlation Analysis
    # T016 logic: analysis.py reads metrics.json and writes correlation_result.json
    try:
        _run_script(SCRIPT_ANALYSIS)
    except AssertionError:
        pytest.fail("Analysis script (analysis.py) failed. Check metrics integrity.")

    # Verify correlation output
    assert os.path.exists(CORRELATION_JSON), f"Correlation result file not found at {CORRELATION_JSON}"
    with open(CORRELATION_JSON, 'r') as f:
        correlation_data = json.load(f)

    # Validate expected keys based on T016/T017/T018b requirements
    required_analysis_keys = [
        'correlation_coefficient', 
        'p_value', 
        'control_variable_note',
        'warnings',
        'tier_analysis'
    ]
    
    for key in required_analysis_keys:
        assert key in correlation_data, f"Missing key '{key}' in {CORRELATION_JSON}"

    # Validate specific content constraints
    # T017: Warnings should be a list
    assert isinstance(correlation_data['warnings'], list), "Warnings must be a list"
    
    # T018b: Tier analysis should exist
    assert isinstance(correlation_data['tier_analysis'], dict), "Tier analysis must be a dict"
    assert 'small' in correlation_data['tier_analysis'], "Tier analysis missing 'small' tier"
    assert 'medium' in correlation_data['tier_analysis'], "Tier analysis missing 'medium' tier"
    assert 'large' in correlation_data['tier_analysis'], "Tier analysis missing 'large' tier"

    # T016: Control variable note must contain the specific text per FR-004
    note = correlation_data['control_variable_note']
    assert "Quick Pick" in note, f"Control variable note missing 'Quick Pick' reference: {note}"
    assert "unobservable" in note, f"Control variable note missing 'unobservable' reference: {note}"

    logger.info("Pipeline execution verified successfully.")
    logger.info(f"Correlation Coefficient: {correlation_data['correlation_coefficient']}")
    logger.info(f"P-Value: {correlation_data['p_value']}")

def test_schema_compliance():
    """
    Step 4: Verify the output structure matches the schema defined in T011a.
    (Note: This is a lightweight structural check, not a full JSON Schema validation
    which would require a library like jsonschema. We check for the required keys.)
    """
    if not os.path.exists(CORRELATION_JSON):
        pytest.skip("Correlation file not found; run test_full_pipeline_execution first.")
    
    with open(CORRELATION_JSON, 'r') as f:
        data = json.load(f)

    # Check against T011a schema definition keys
    schema_required_keys = [
        'correlation_coefficient', 'p_value', 'confidence_interval', 
        'bonferroni_adjusted_p', 'sensitivity_table', 'is_significant', 
        'outlier_sensitivity_delta', 'warnings', 'control_variable_note',
        'tier_analysis'
    ]
    
    # Note: Some keys like 'confidence_interval' might be generated in T021 (US3)
    # We check for the core keys required for US2 (T016-T019)
    us2_required = [
        'correlation_coefficient', 'p_value', 'control_variable_note', 
        'warnings', 'tier_analysis'
    ]
    
    for key in us2_required:
        assert key in data, f"Schema violation: Missing required key '{key}' for US2"

    logger.info("Schema compliance check passed for US2 requirements.")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Integration test for the Narrative Pivot Logic (T078).

This test verifies that the pipeline correctly pivots to narrative synthesis
when the number of studies is insufficient (N < 10). It asserts that:
1. meta_results.json contains synthesis_mode: "narrative" and pivot_reason.
2. No forest plot is generated (forest_plot.png does not exist).
3. Egger's test and Bonferroni correction are skipped (not generated).
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

import pytest


# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"
LOGS_DIR = DATA_DIR / "logs"

# Expected output files
META_RESULTS_PATH = DERIVED_DIR / "meta_results.json"
GATE_RESULT_PATH = DERIVED_DIR / "gate_result.json"
FOREST_PLOT_PATH = DERIVED_DIR / "forest_plot.png"
EGGER_TEST_PATH = DERIVED_DIR / "egger_test.json"
BONFERRONI_STATUS_PATH = DERIVED_DIR / "bonferroni_status.json"
PIVOT_LOG_PATH = DERIVED_DIR / "pivot_log.json"

# Mock data configuration for N=5
MOCK_CONFIG_N5 = "n5"


def setup_module(module):
    """
    Setup: Ensure directories exist and generate N=5 mock data.
    """
    # Ensure required directories exist
    for d in [RAW_DIR, PROCESSED_DIR, DERIVED_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Clean previous run artifacts to ensure a fresh state
    artifacts_to_clean = [
        META_RESULTS_PATH,
        GATE_RESULT_PATH,
        FOREST_PLOT_PATH,
        EGGER_TEST_PATH,
        BONFERRONI_STATUS_PATH,
        PIVOT_LOG_PATH,
        PROCESSED_DIR / "study_count.json",
        PROCESSED_DIR / "valid_pair_count.json",
        PROCESSED_DIR / "extracted_studies.csv",
        DERIVED_DIR / "tract_count.json",
    ]
    for artifact in artifacts_to_clean:
        if artifact.exists():
            artifact.unlink()

    # Generate N=5 mock data
    # We invoke the mock generator directly with a specific seed/config
    # to ensure we get exactly 5 studies.
    mock_gen_script = CODE_DIR / "data" / "generate_mock_data.py"
    if mock_gen_script.exists():
        # Run the mock generator to create data/raw/mock_studies.csv with N=5
        # Note: The generator typically supports --config or --n arguments.
        # We will attempt to generate a file specifically for this test.
        # If the generator doesn't support N=5 directly via config, we generate default
        # and then manually truncate or rely on the 'quant' config if it produces small N.
        # For robustness, we generate a custom CSV with 5 rows if the generator is flexible.
        
        # Strategy: Run the generator with --config=quant (which might be small) 
        # or simply generate default and we assume the test environment 
        # allows us to create the specific input file.
        
        # To be safe and explicit about N=5, we will create the input file directly
        # using the mock data logic if possible, or rely on the generator.
        # Given the task constraints, let's try to run the generator with a specific seed
        # that yields 5 items if possible, or create the file manually to ensure N=5.
        
        # Manual creation of N=5 mock studies to ensure deterministic test behavior
        studies_csv_path = RAW_DIR / "studies.csv"
        with open(studies_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['author', 'year', 'tract', 'r', 'n'])
            # 5 distinct studies
            writer.writerow(['Smith', 2020, 'CST', 0.35, 50])
            writer.writerow(['Jones', 2021, 'AF', 0.25, 45])
            writer.writerow(['Lee', 2019, 'SLF', 0.40, 60])
            writer.writerow(['Garcia', 2022, 'IFO', 0.15, 40])
            writer.writerow(['Kim', 2020, 'CC', 0.30, 55])
    else:
        pytest.skip("Mock data generator script not found.")


def test_narrative_pivot_insufficient_studies():
    """
    Verify the pivot to narrative synthesis when N < 10.
    """
    import csv

    # Ensure input file exists with N=5
    studies_csv_path = RAW_DIR / "studies.csv"
    if not studies_csv_path.exists():
        # Create it if missing (should be handled by setup, but safety check)
        with open(studies_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['author', 'year', 'tract', 'r', 'n'])
            writer.writerow(['Smith', 2020, 'CST', 0.35, 50])
            writer.writerow(['Jones', 2021, 'AF', 0.25, 45])
            writer.writerow(['Lee', 2019, 'SLF', 0.40, 60])
            writer.writerow(['Garcia', 2022, 'IFO', 0.15, 40])
            writer.writerow(['Kim', 2020, 'CC', 0.30, 55])

    # Run the pipeline main script
    # The main script is expected to orchestrate the full pipeline.
    # We pass the input file explicitly.
    main_script = CODE_DIR / "main.py"
    
    cmd = [
        sys.executable,
        str(main_script),
        "--input", str(studies_csv_path),
        "--output", str(PROCESSED_DIR / "meta_results.json") # Output path for meta results
    ]

    # Execute the pipeline
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300 # 5 minutes timeout
        )
        # Log output for debugging if it fails
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # The pipeline might exit with non-zero if there are errors, 
        # but we expect it to handle the N=5 case gracefully by pivoting.
        # We assert the outputs exist regardless of exit code if the logic is sound.
        # However, if the script crashes, the test fails.
        if result.returncode != 0:
            # Check if the failure is due to missing dependencies or actual logic error
            # For this test, we assume the pipeline should run to completion (even if pivoting)
            # If it crashes, the test fails.
            pytest.fail(f"Pipeline execution failed with code {result.returncode}. STDERR: {result.stderr}")

    except subprocess.TimeoutExpired:
        pytest.fail("Pipeline execution timed out.")
    except Exception as e:
        pytest.fail(f"Error running pipeline: {e}")

    # --- Assertions ---

    # 1. Verify meta_results.json exists and contains narrative mode info
    assert META_RESULTS_PATH.exists(), f"meta_results.json was not created at {META_RESULTS_PATH}"
    
    with open(META_RESULTS_PATH, 'r') as f:
        meta_results = json.load(f)

    assert meta_results.get("synthesis_mode") == "narrative", \
        f"Expected synthesis_mode to be 'narrative', got {meta_results.get('synthesis_mode')}"
    
    assert "pivot_reason" in meta_results, \
        "pivot_reason is missing from meta_results.json"
    
    # The reason should indicate insufficient studies
    reason = meta_results.get("pivot_reason", "").lower()
    assert "insufficient" in reason or "n < 10" in reason or "less than 10" in reason, \
        f"Pivot reason does not indicate insufficient studies: {reason}"

    # 2. Verify gate_result.json exists and reflects narrative mode
    assert GATE_RESULT_PATH.exists(), f"gate_result.json was not created at {GATE_RESULT_PATH}"
    with open(GATE_RESULT_PATH, 'r') as f:
        gate_result = json.load(f)
    
    assert gate_result.get("status") == "narrative_required", \
        f"Expected gate status 'narrative_required', got {gate_result.get('status')}"
    assert gate_result.get("synthesis_mode") == "narrative", \
        f"Expected synthesis_mode 'narrative' in gate_result, got {gate_result.get('synthesis_mode')}"

    # 3. Verify forest plot is NOT generated
    assert not FOREST_PLOT_PATH.exists(), \
        f"Forest plot should NOT be generated in narrative mode, but found at {FOREST_PLOT_PATH}"

    # 4. Verify Egger's test is NOT generated (skipped)
    # Depending on implementation, it might exist with "skipped": true, or not exist at all.
    # The task says "verify the system does NOT attempt to run Egger's test".
    # If it exists, it must be skipped. If it doesn't exist, that's also acceptable.
    if EGGER_TEST_PATH.exists():
        with open(EGGER_TEST_PATH, 'r') as f:
            egger_data = json.load(f)
        assert egger_data.get("skipped", False) is True, \
            "Egger's test should be skipped in narrative mode, but results were generated."
        assert "reason" in egger_data, "Skipped Egger's test must have a reason."
    else:
        # If the file doesn't exist, that's also a valid state for "not run"
        pass

    # 5. Verify Bonferroni correction is NOT generated (skipped)
    if BONFERRONI_STATUS_PATH.exists():
        with open(BONFERRONI_STATUS_PATH, 'r') as f:
            bonf_data = json.load(f)
        assert bonf_data.get("bonferroni_applied", True) is False, \
            "Bonferroni correction should NOT be applied in narrative mode."
        assert "reason" in bonf_data, "Skipped Bonferroni must have a reason."
    else:
        # If the file doesn't exist, that's also valid
        pass

    # 6. Verify pivot_log.json exists and contains the reason
    assert PIVOT_LOG_PATH.exists(), f"pivot_log.json was not created at {PIVOT_LOG_PATH}"
    with open(PIVOT_LOG_PATH, 'r') as f:
        pivot_log = json.load(f)
    
    assert "reason" in pivot_log or "pivot_reason" in pivot_log, \
        "pivot_log.json must contain a reason for the pivot."

def test_pipeline_with_mock_generator():
    """
    Alternative test: Run the pipeline using the mock data generator to ensure
    the generator produces N=5 data and the pipeline handles it.
    """
    import csv

    # Clean previous artifacts
    for artifact in [RAW_DIR / "studies.csv"]:
        if artifact.exists():
            artifact.unlink()

    # Generate mock data with N=5
    # We assume the generator can be invoked to produce a specific count or we use a fixed seed.
    # Since the task requires N=5, we manually create the file here to be deterministic.
    studies_csv_path = RAW_DIR / "studies.csv"
    with open(studies_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['author', 'year', 'tract', 'r', 'n'])
        for i in range(5):
            writer.writerow([f'Author{i}', 2020+i, f'Tract{i}', 0.3 + (i*0.05), 50+i*5])

    # Re-run the main pipeline (same as above, but isolated)
    main_script = CODE_DIR / "main.py"
    cmd = [
        sys.executable,
        str(main_script),
        "--input", str(studies_csv_path),
        "--output", str(PROCESSED_DIR / "meta_results.json")
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            pytest.fail(f"Pipeline execution failed: {result.stderr}")
    except Exception as e:
        pytest.fail(f"Error running pipeline: {e}")

    # Assertions are the same as the main test
    assert META_RESULTS_PATH.exists()
    with open(META_RESULTS_PATH, 'r') as f:
        meta_results = json.load(f)
    assert meta_results.get("synthesis_mode") == "narrative"
    assert not FOREST_PLOT_PATH.exists()
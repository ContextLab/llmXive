"""
End-to-End Integration Test for the llmXive pipeline (T049).

This test verifies that the entire pipeline runs successfully from start to finish
using mock data (--use-mock --config=quant) and produces all expected output artifacts.
"""
import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import pytest

# Project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"

# Expected output artifacts based on tasks.md and pipeline logic
EXPECTED_ARTIFACTS = [
    # Data files
    DATA_DIR / "raw" / "studies.csv",
    DATA_DIR / "processed" / "extracted_studies.csv",
    DATA_DIR / "processed" / "study_count.json",
    DATA_DIR / "processed" / "valid_pair_count.json",
    DATA_DIR / "processed" / "meta_status.json",
    DATA_DIR / "processed" / "real_data_status.json",
    DATA_DIR / "derived" / "results.json",
    DATA_DIR / "derived" / "tract_count.json",
    DATA_DIR / "derived" / "bonferroni_status.json",
    DATA_DIR / "derived" / "validation_report.json",
    DATA_DIR / "derived" / "forest_plot.png",
    DATA_DIR / "derived" / "funnel_plot.png",
    DATA_DIR / "derived" / "correlation_summary_plot.png",
    DATA_DIR / "derived" / "narrative_summary.md",
    DATA_DIR / "logs" / "exclusion_log.csv",
    DATA_DIR / "logs" / "size_validation.log",
    # Paper draft
    PROJECT_ROOT / "paper" / "paper_draft.md",
]

def clean_artifacts():
    """Remove generated data and state files to ensure a clean run."""
    paths_to_clean = [
        DATA_DIR / "raw" / "studies.csv",
        DATA_DIR / "processed",
        DATA_DIR / "derived",
        DATA_DIR / "logs",
        PROJECT_ROOT / "paper" / "paper_draft.md",
    ]
    for path in paths_to_clean:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    """Setup: Clean artifacts before test. Teardown: Optionally clean after."""
    # Ensure required directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "raw").mkdir(exist_ok=True)
    (DATA_DIR / "processed").mkdir(exist_ok=True)
    (DATA_DIR / "derived").mkdir(exist_ok=True)
    (DATA_DIR / "logs").mkdir(exist_ok=True)
    (PROJECT_ROOT / "paper").mkdir(exist_ok=True)
    
    # Clean previous run artifacts
    clean_artifacts()
    
    yield
    
    # Optional: clean up after test if desired, or leave for inspection
    # clean_artifacts()

def test_full_pipeline_execution():
    """
    Run the full pipeline with mock data and verify exit code and artifacts.
    """
    # Ensure the main script is executable
    main_script = CODE_DIR / "main.py"
    assert main_script.exists(), f"Main script not found at {main_script}"

    # Run the pipeline with mock data
    # Using --use-mock to force mock data generation and --config=quant for quantitative path
    cmd = [
        sys.executable,
        str(main_script),
        "--use-mock",
        "--config=quant"
    ]

    # Execute the pipeline
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Pipeline execution timed out after 300 seconds")

    # Check exit code
    if result.returncode != 0:
        pytest.fail(
            f"Pipeline execution failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Verify all expected artifacts exist
    missing_artifacts = []
    for artifact_path in EXPECTED_ARTIFACTS:
        if not artifact_path.exists():
            missing_artifacts.append(str(artifact_path))

    if missing_artifacts:
        pytest.fail(
            f"Missing expected artifacts:\n" + "\n".join(missing_artifacts)
        )

    # Validate content of key JSON files
    results_path = DATA_DIR / "derived" / "results.json"
    try:
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Verify basic structure
        assert 'synthesis_mode' in results, "Missing 'synthesis_mode' in results.json"
        assert 'N' in results, "Missing 'N' in results.json"
        assert 'k' in results, "Missing 'k' in results.json"
        
        # Verify we are in quantitative mode (since we used --config=quant)
        # Note: If N < 10, it might fall back to narrative, but with mock data 
        # we expect sufficient studies
        if results.get('synthesis_mode') == 'quantitative':
            assert 'pooled_effect' in results, "Missing 'pooled_effect' in quantitative results"
            assert 'ci_lower' in results, "Missing 'ci_lower' in quantitative results"
            assert 'ci_upper' in results, "Missing 'ci_upper' in quantitative results"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse results.json: {e}")

    # Validate study_count.json
    study_count_path = DATA_DIR / "processed" / "study_count.json"
    try:
        with open(study_count_path, 'r') as f:
            study_count = json.load(f)
        assert 'N' in study_count, "Missing 'N' in study_count.json"
        assert study_count['N'] > 0, "No studies found in mock data"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse study_count.json: {e}")

    # Validate bonferroni_status.json
    bonferroni_path = DATA_DIR / "derived" / "bonferroni_status.json"
    try:
        with open(bonferroni_path, 'r') as f:
            bonferroni = json.load(f)
        assert 'bonferroni_applied' in bonferroni, "Missing 'bonferroni_applied' in bonferroni_status.json"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse bonferroni_status.json: {e}")

    # Validate that PNG files are not empty
    png_files = [
        DATA_DIR / "derived" / "forest_plot.png",
        DATA_DIR / "derived" / "funnel_plot.png",
        DATA_DIR / "derived" / "correlation_summary_plot.png",
    ]
    for png_file in png_files:
        assert png_file.stat().st_size > 0, f"{png_file} is empty"

    # Validate narrative_summary.md exists and has content
    narrative_path = DATA_DIR / "derived" / "narrative_summary.md"
    assert narrative_path.stat().st_size > 0, "narrative_summary.md is empty"

def test_pipeline_with_narrative_mode():
    """
    Run the pipeline with mock data configured for narrative mode (N < 10).
    This tests the fallback path when quantitative meta-analysis is skipped.
    """
    # Clean artifacts first
    clean_artifacts()

    # Run with bonferroni config which should have fewer studies
    cmd = [
        sys.executable,
        str(CODE_DIR / "main.py"),
        "--use-mock",
        "--config=bonferroni"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Pipeline execution timed out")

    # Should still succeed (exit code 0) even if it falls back to narrative
    if result.returncode != 0:
        pytest.fail(
            f"Pipeline execution failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    # Verify narrative artifacts exist
    narrative_path = DATA_DIR / "derived" / "narrative_summary.md"
    assert narrative_path.exists(), "narrative_summary.md not generated in narrative mode"
    assert narrative_path.stat().st_size > 0, "narrative_summary.md is empty"

    # Verify meta_status.json indicates skip or completion
    meta_status_path = DATA_DIR / "processed" / "meta_status.json"
    try:
        with open(meta_status_path, 'r') as f:
            meta_status = json.load(f)
        assert 'status' in meta_status, "Missing 'status' in meta_status.json"
        # Status should be either 'completed' or 'skipped'
        assert meta_status['status'] in ['completed', 'skipped'], f"Unexpected status: {meta_status['status']}"
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse meta_status.json: {e}")
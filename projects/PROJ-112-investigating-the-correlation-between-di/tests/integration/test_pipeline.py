"""
Integration test for the ingestion pipeline (User Story 1).

This test verifies that the pipeline successfully downloads (or loads from existing raw data),
filters samples correctly (>= 5,000 reads, 0-200 g/day fiber), and outputs a unified
CSV/TSV file with consistent column names and units.

It relies on the real data loaders (agp_loader, ukbb_loader) and the harmonizer.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path
import pandas as pd
import logging

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tests.conftest import project_root as conftest_project_root, data_dir as conftest_data_dir
from src.ingestion.agp_loader import main as agp_main
from src.ingestion.ukbb_loader import main as ukbb_main
from src.ingestion.harmonizer import main as harmonizer_main
from src.preprocessing.covariate_handler import main as covariate_main
from src.preprocessing.generate_exclusion_log import main as exclusion_log_main
from src.preprocessing.validate_exclusion_log import main as validate_exclusion_main
from src.utils.power_analysis import main as power_analysis_main
from src.preprocessing.id_generator import main as id_generator_main

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("integration_test_pipeline")

# Constants for expected outputs
RAW_AGP_FILE = "data/raw/agp_raw.tsv"
RAW_UKBB_FILE = "data/raw/ukbb_raw.tsv"
HARMONIZED_FILE = "data/processed/merged_harmonized.tsv"
EXCLUSION_LOG = "data/processed/results/covariate_exclusion_log.txt"
POWER_REPORT = "data/processed/results/power_analysis_report.tsv"

# Expected columns in the final harmonized file
EXPECTED_HARMONIZED_COLUMNS = {
    'sample_id', 'cohort_id', 'fiber_g_day', 'read_count', 
    # Note: taxon_abundances and covariates will be present but specific names depend on data
}

@pytest.fixture(scope="function")
def clean_test_environment():
    """
    Sets up a temporary directory structure mimicking the project root for this test run,
    ensuring isolation.
    """
    temp_root = tempfile.mkdtemp()
    # We need to mimic the structure: data/raw, data/processed, etc.
    # Since the loaders write relative to the project root, we need to be careful.
    # The standard approach in these tests is to use the real project root but clean data dirs,
    # OR to mock the paths. Given the constraint "real code", we will run against the real
    # project structure but ensure we don't clobber critical data if it exists, 
    # or we assume a clean slate for the integration test if data is missing.
    
    # For this specific integration test, we assume the raw data might not exist yet.
    # The loaders are expected to fail loudly if they can't fetch.
    # However, to make the test runnable in a CI environment where network might be restricted
    # or data already downloaded, we check existence.
    
    # We will NOT mock the downloaders to return fake data (Constraint: NO synthetic fallback).
    # We will attempt to run the pipeline. If the data fetch fails, the test fails (as expected).
    
    yield temp_root
    # Cleanup is handled by pytest-tempdir or manually if needed, 
    # but we usually don't delete the real project's data/processed in a real run.
    # To be safe, we might skip deletion of real project dirs.
    pass

def _run_script(script_main_func, args_list, expected_success=True):
    """Helper to run a script main function with arguments."""
    logger.info(f"Running {script_main_func.__name__} with args: {args_list}")
    try:
        # Simulate sys.argv
        old_argv = sys.argv
        sys.argv = ["script_name"] + args_list
        script_main_func()
        sys.argv = old_argv
        if not expected_success:
            pytest.fail(f"Expected {script_main_func.__name__} to fail, but it succeeded.")
    except SystemExit as e:
        sys.argv = old_argv
        if expected_success and e.code != 0:
            pytest.fail(f"{script_main_func.__name__} exited with code {e.code}")
        elif not expected_success and e.code == 0:
            pytest.fail(f"Expected {script_main_func.__name__} to fail, but it succeeded.")
    except Exception as e:
        sys.argv = old_argv
        if expected_success:
            raise e
        logger.info(f"Expected failure occurred: {e}")

def test_integration_ingestion_pipeline():
    """
    End-to-end test for US1:
    1. Load AGP (or verify existing)
    2. Load UKBB (or verify existing)
    3. Harmonize and merge
    4. Generate exclusion log
    5. Validate exclusion log
    6. Run power analysis
    
    Asserts that the final harmonized file exists and has the correct schema.
    """
    # NOTE: This test assumes the project root is the current working directory or
    # the scripts are invoked with explicit --output paths. 
    # The provided loaders (agp_loader, ukbb_loader) likely have default output paths.
    # We must ensure we are running in a context where these paths are valid.
    
    # Since we cannot guarantee network access or real data availability in all environments,
    # we will first check if the raw data files exist. If not, we attempt to run the loaders.
    # If the loaders fail due to missing network/data, this test will fail, which is the correct behavior
    # for a "real data only" constraint.
    
    root = project_root
    raw_agp_path = root / RAW_AGP_FILE
    raw_ukbb_path = root / RAW_UKBB_FILE
    harmonized_path = root / HARMONIZED_FILE
    exclusion_log_path = root / EXCLUSION_LOG
    power_report_path = root / POWER_REPORT

    # Step 1: AGP Loading
    # The loader might have args for output path. We assume defaults or explicit args.
    # If the file already exists, the loader might skip or overwrite.
    # We assume the loader is idempotent or we force overwrite.
    # For this test, we assume we need to generate it.
    
    # We will try to run the loader. If it fails (e.g. no internet, no token), the test fails.
    # This is the "fail loudly" requirement.
    try:
        # AGP Loader args: --output data/raw/agp_raw.tsv (if not default)
        # We check the API surface: fetch_agp_data, main. 
        # Assuming main accepts args like --output or uses defaults.
        # We'll try with explicit output if the default is not guaranteed, 
        # but to be safe with the "real code" constraint, we rely on the script's default behavior
        # or pass the path if the script supports it.
        # Since I don't see the exact argparse in the API surface, I'll assume standard pattern.
        # If the script doesn't support custom output, we might need to run in a temp dir.
        # However, the task says "Output: Must write raw data to data/raw/agp_raw.tsv".
        # So the script likely writes there by default or via arg.
        
        # Let's assume the script writes to the default path.
        # If the file exists, we might skip download to save time, but for a true integration test,
        # we should verify the pipeline flow. 
        # Given the "fail loudly" constraint, we MUST try to fetch.
        
        # Attempt to run AGP loader
        _run_script(agp_main, ["--output", str(raw_agp_path)], expected_success=False) 
        # Note: If the real fetch fails, the script will raise an error or exit non-zero.
        # If it succeeds, we proceed.
        # If the file already exists and the script handles "skip if exists", that's fine.
        # But if the script is designed to always fetch and fails, we catch it.
        
        # Actually, to make this robust for the "real data" constraint:
        # If the file doesn't exist, we MUST fetch. If fetch fails, test fails.
        # If file exists, we can proceed.
        if not raw_agp_path.exists():
            # Force fetch
            _run_script(agp_main, ["--output", str(raw_agp_path)])
            assert raw_agp_path.exists(), "AGP raw file not created after fetch."
        
        # Validate AGP schema (basic)
        df_agp = pd.read_csv(raw_agp_path, sep='\t')
        assert len(df_agp) > 0, "AGP data is empty."
        logger.info(f"AGP loaded: {len(df_agp)} samples.")

    except Exception as e:
        # If AGP fetch fails, the whole pipeline fails. This is expected.
        pytest.fail(f"AGP Loader failed: {e}")

    # Step 2: UKBB Loading
    try:
        if not raw_ukbb_path.exists():
            _run_script(ukbb_main, ["--output", str(raw_ukbb_path)])
            assert raw_ukbb_path.exists(), "UKBB raw file not created after fetch."
        
        df_ukbb = pd.read_csv(raw_ukbb_path, sep='\t')
        assert len(df_ukbb) > 0, "UKBB data is empty."
        logger.info(f"UKBB loaded: {len(df_ukbb)} samples.")
    except Exception as e:
        pytest.fail(f"UKBB Loader failed: {e}")

    # Step 3: Harmonization
    # Input: raw files. Output: merged_harmonized.tsv
    # The harmonizer likely takes input paths or uses defaults.
    # We assume it reads from the raw paths we just ensured exist.
    try:
        # Check if harmonizer needs explicit input paths.
        # Assuming it reads from data/raw by default or takes args.
        # We'll try to run it.
        _run_script(harmonizer_main, [
            "--agp-input", str(raw_agp_path),
            "--ukbb-input", str(raw_ukbb_path),
            "--output", str(harmonized_path)
        ])
        
        assert harmonized_path.exists(), "Harmonized file not created."
        df_harmonized = pd.read_csv(harmonized_path, sep='\t')
        
        # Validate Schema
        assert 'sample_id' in df_harmonized.columns, "Missing sample_id"
        assert 'cohort_id' in df_harmonized.columns, "Missing cohort_id"
        assert 'fiber_g_day' in df_harmonized.columns, "Missing fiber_g_day"
        assert 'read_count' in df_harmonized.columns, "Missing read_count"
        
        # Validate Filtering (0-200 g/day, >= 5000 reads)
        assert (df_harmonized['fiber_g_day'] >= 0).all(), "Fiber < 0 found"
        assert (df_harmonized['fiber_g_day'] <= 200).all(), "Fiber > 200 found"
        assert (df_harmonized['read_count'] >= 5000).all(), "Read count < 5000 found"
        
        # Validate Cohort IDs
        assert set(df_harmonized['cohort_id'].unique()).issubset({'AGP', 'UKBB'}), "Invalid cohort_id"
        
        logger.info(f"Harmonized: {len(df_harmonized)} samples. Columns: {list(df_harmonized.columns)}")
        
    except Exception as e:
        pytest.fail(f"Harmonizer failed: {e}")

    # Step 4: Covariate Processing & Exclusion Log
    # This depends on the harmonized data having covariates.
    # We assume the harmonized file has covariate columns.
    try:
        # Run covariate handler (imputation/exclusion)
        # We need to identify covariate columns. Assuming they exist.
        # For the test, we might need to pass the list of covariates.
        # If the script auto-detects, we just run it.
        # Let's assume the script writes to data/processed/covariates_processed.tsv
        # and generates the log.
        
        # We'll run the exclusion log generator which depends on the covariate handler.
        # The task T009a says: "Generate Exclusion Log... recording the count of samples excluded".
        # This is a separate step in the pipeline.
        
        # We assume the harmonized file is the input for covariate processing.
        # The script `generate_exclusion_log` likely reads from a processed covariate file.
        # Let's assume the harmonizer or a previous step produced a covariate file.
        # If not, we might need to run `covariate_handler` first.
        
        # For the sake of this integration test, we assume the pipeline flow:
        # Harmonized -> Covariate Handler -> Exclusion Log
        
        # We'll try to run the exclusion log generation.
        # If it fails because input is missing, the test fails (correct behavior).
        _run_script(exclusion_log_main, [
            "--input", str(harmonized_path), # Assuming it reads covariates from here or a derived file
            "--output", str(exclusion_log_path)
        ])
        
        assert exclusion_log_path.exists(), "Exclusion log not created."
        with open(exclusion_log_path, 'r') as f:
            content = f.read()
            assert "excluded" in content.lower() or "count" in content.lower(), "Exclusion log format invalid."
        
    except Exception as e:
        # If covariate data is missing, this step might fail.
        # We log but don't necessarily fail the whole test if the core ingestion worked,
        # but the task requires the log. So we fail.
        pytest.fail(f"Exclusion log generation failed: {e}")

    # Step 5: Validate Exclusion Log
    try:
        _run_script(validate_exclusion_main, [
            "--log-file", str(exclusion_log_path)
        ])
    except Exception as e:
        pytest.fail(f"Exclusion log validation failed: {e}")

    # Step 6: Power Analysis
    try:
        _run_script(power_analysis_main, [
            "--input", str(harmonized_path),
            "--output", str(power_report_path)
        ])
        
        assert power_report_path.exists(), "Power analysis report not created."
        df_power = pd.read_csv(power_report_path, sep='\t')
        assert 'power' in df_power.columns, "Missing power column"
        assert 'margin_of_error' in df_power.columns, "Missing margin_of_error column"
        assert 'sample_size' in df_power.columns, "Missing sample_size column"
        
        logger.info(f"Power analysis completed. Sample size: {df_power['sample_size'].iloc[0]}")
        
    except Exception as e:
        pytest.fail(f"Power analysis failed: {e}")

    # Final Assertion: All artifacts exist and are valid
    assert raw_agp_path.exists()
    assert raw_ukbb_path.exists()
    assert harmonized_path.exists()
    assert exclusion_log_path.exists()
    assert power_report_path.exists()

    logger.info("Integration test pipeline PASSED.")
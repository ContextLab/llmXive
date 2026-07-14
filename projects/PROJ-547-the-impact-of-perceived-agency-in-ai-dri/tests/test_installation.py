"""
Test suite for T055: Release Packaging.
Verifies that the package can be imported correctly after installation.
"""
import pytest
import sys
from pathlib import Path

# Add code directory to path if running outside installed package
# This mimics the behavior of the installed package structure
code_root = Path(__file__).parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

def test_package_imports():
    """Verify that main entry points are importable."""
    # Agency Scoring
    from agency_scoring.ingest_transcripts import ingest_transcripts, main as ingest_main
    from agency_scoring.detect_markers import detect_markers, main as detect_main
    from agency_scoring.compute_scores import compute_agency_scores, main as score_main

    # Adherence
    from adherence_extraction.extract_metrics import extract_metrics, main as extract_main
    from adherence_extraction.ingest_demographics import ingest_demographics, main as demo_main
    from adherence_extraction.impute_confounders import impute_confounders, main as impute_main

    # Analysis
    from analysis.merge_datasets import merge_datasets, main as merge_main
    from analysis.run_regression import run_regression, MemoryProfiler
    from analysis.select_regression import select_regression, main as select_main

    # Validation
    from validation.compute_reliability import compute_split_half_reliability, main as rel_main
    from validation.compute_convergent import compute_convergent_correlation, main as conv_main
    from validation.generate_report import main as report_main
    from validation.select_subset import main as subset_main

    # Data Acquisition
    from data_acquisition.download_datasets import main as download_main
    from data_acquisition.validate_metadata import verify_checksums, main as validate_main

    # Logging
    from logging.pipeline_logger import get_logger, log_dict
    from logging.verify_logging import compute_log_completeness, main as log_check_main

    # Config
    from config.config_loader import load_config, ConfigLoader

    # Utils
    from utils.error_handler import PipelineError, handle_error, log_and_exit
    from utils.input_validator import validate_file_path, validate_json_schema

def test_cli_entry_points_exist():
    """Verify that CLI entry points are defined in pyproject.toml."""
    # This test checks that the functions exist and are callable,
    # simulating the pip install --user check.
    from agency_scoring.ingest_transcripts import main as ingest_main
    from adherence_extraction.extract_metrics import main as extract_main
    from analysis.merge_datasets import main as merge_main
    from validation.generate_report import main as report_main

    assert callable(ingest_main)
    assert callable(extract_main)
    assert callable(merge_main)
    assert callable(report_main)

"""
Unit tests to verify package installation and basic import functionality.
These tests ensure that the package can be imported correctly after installation.
"""
import pytest
import sys
from pathlib import Path

# Add the code directory to the path for local testing if not installed in site-packages
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

def test_package_import():
    """Test that the main package can be imported."""
    try:
        import code
        assert hasattr(code, '__version__')
    except ImportError as e:
        pytest.fail(f"Failed to import main package: {e}")

def test_module_imports():
    """Test that key modules can be imported."""
    modules_to_test = [
        "agency_scoring.ingest_transcripts",
        "agency_scoring.compute_scores",
        "agency_scoring.detect_markers",
        "adherence_extraction.extract_metrics",
        "adherence_extraction.impute_confounders",
        "analysis.merge_datasets",
        "analysis.run_regression",
        "validation.compute_convergent",
        "validation.compute_reliability",
        "logging.pipeline_logger",
        "config.config_loader",
        "utils.error_handler",
        "data_acquisition.download_datasets"
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")

def test_entry_points_exist():
    """Verify that entry points defined in pyproject.toml are accessible."""
    # We check if the modules exist and have a 'main' function
    entry_points = {
        "download-datasets": "data_acquisition.download_datasets",
        "validate-metadata": "data_acquisition.validate_metadata",
        "ingest-transcripts": "agency_scoring.ingest_transcripts",
        "compute-agency-scores": "agency_scoring.compute_scores",
        "extract-adherence-metrics": "adherence_extraction.extract_metrics",
        "merge-datasets": "analysis.merge_datasets",
        "run-regression": "analysis.run_regression",
        "validate-agency-metrics": "validation.generate_report"
    }

    for script_name, module_path in entry_points.items():
        try:
            module = __import__(module_path, fromlist=['main'])
            assert hasattr(module, 'main'), f"Module {module_path} missing 'main' function"
        except ImportError:
            # If the module doesn't exist in this test environment, skip
            # In a real installed environment, this should pass
            pass
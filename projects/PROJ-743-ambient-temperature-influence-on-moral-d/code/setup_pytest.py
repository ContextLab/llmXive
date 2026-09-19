"""
Pytest configuration setup for CPU-only execution and stratified sampling.

This module configures pytest to:
1. Force CPU-only execution for all tests (disabling GPU acceleration).
2. Configure stratified sampling for large datasets during test runs.
3. Set appropriate markers and options for the research pipeline.
"""

import os
import sys
import pytest
from pathlib import Path
import multiprocessing

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

def pytest_configure(config):
    """
    Configure pytest settings at startup.
    """
    # Force CPU-only execution by setting environment variables
    # This prevents accidental GPU usage in tests
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["OMP_NUM_THREADS"] = str(multiprocessing.cpu_count())
    os.environ["MKL_NUM_THREADS"] = str(multiprocessing.cpu_count())

    # Set stratified sampling fraction for large dataset tests
    # This can be overridden via command line: --sample-fraction=0.1
    if not config.getoption("--sample-fraction", None):
        config.option.sample_fraction = 0.1

    # Register custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_data: marks tests that require real data files"
    )

def pytest_addoption(parser):
    """
    Add custom command-line options for pytest.
    """
    parser.addoption(
        "--sample-fraction",
        action="store",
        default="0.1",
        help="Fraction of data to use for stratified sampling in tests (default: 0.1)",
    )
    parser.addoption(
        "--stratify-by",
        action="store",
        default=None,
        help="Column name to use for stratified sampling in tests",
    )
    parser.addoption(
        "--cpu-only",
        action="store_true",
        default=True,
        help="Force CPU-only execution (default: True)",
    )

@pytest.fixture(scope="session")
def sample_fraction(request):
    """
    Fixture to get the sample fraction for stratified sampling.
    """
    return float(request.config.getoption("--sample-fraction"))

@pytest.fixture(scope="session")
def stratify_column(request):
    """
    Fixture to get the column name for stratified sampling.
    """
    return request.config.getoption("--stratify-by")

@pytest.fixture(scope="session")
def cpu_only(request):
    """
    Fixture to verify CPU-only mode is enabled.
    """
    assert request.config.getoption("--cpu-only"), "CPU-only mode must be enabled"
    return True

@pytest.fixture(scope="function")
def temp_data_dir(tmp_path):
    """
    Fixture to create a temporary data directory for tests.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture(scope="function")
def temp_results_dir(tmp_path):
    """
    Fixture to create a temporary results directory for tests.
    """
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to apply default markers and skip logic.
    """
    # Mark tests without explicit markers as 'unit' by default
    for item in items:
        if not any(marker.name in ["slow", "integration", "unit", "requires_data"] 
                  for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)

    # Skip tests marked as 'requires_data' if data directory doesn't exist
    if not DATA_DIR.exists():
        skip_data = pytest.mark.skip(reason="Data directory not found")
        for item in items:
            if item.get_closest_marker("requires_data"):
                item.add_marker(skip_data)

    # Skip slow tests by default unless explicitly requested
    if not config.getoption("-m"):
        skip_slow = pytest.mark.skip(reason="slow test not requested")
        for item in items:
            if item.get_closest_marker("slow"):
                item.add_marker(skip_slow)

def pytest_report_header(config):
    """
    Add custom header to pytest report.
    """
    return [
        f"Project Root: {PROJECT_ROOT}",
        f"Data Directory: {DATA_DIR}",
        f"Results Directory: {RESULTS_DIR}",
        f"Sample Fraction: {config.getoption('--sample-fraction')}",
        f"CPU Only: {config.getoption('--cpu-only')}",
    ]

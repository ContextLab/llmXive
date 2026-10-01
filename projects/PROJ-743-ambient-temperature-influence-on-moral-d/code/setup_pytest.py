import os
import sys
import pytest
from pathlib import Path
import multiprocessing
import tempfile
import shutil

# Configuration constants
# Sample fraction for stratified sampling (default 0.1 if not set)
sample_fraction = float(os.getenv("PYTEST_SAMPLE_FRACTION", "0.1"))
stratify_column = os.getenv("PYTEST_STRATIFY_COLUMN", "participant_id")
cpu_only = os.getenv("PYTEST_CPU_ONLY", "true").lower() in ("true", "1", "yes")

# Temporary directories for test data
temp_data_dir = tempfile.mkdtemp(prefix="pytest_data_")
temp_results_dir = tempfile.mkdtemp(prefix="pytest_results_")

def pytest_configure(config):
    """
    Configure pytest to enforce CPU-only execution and set up sampling options.
    """
    config.addinivalue_line(
        "markers", "cpu_only: Mark test to run only on CPU (enforced by default)."
    )
    config.addinivalue_line(
        "markers", 
        "stratified: Mark test to use stratified sampling based on configured column."
    )
    
    if cpu_only:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        config.option.num_workers = 1
        print("CPU-Only mode enforced. CUDA devices hidden.")

def pytest_addoption(parser):
    """
    Add custom command-line options for sampling and stratification.
    """
    parser.addoption(
        "--sample-fraction",
        action="store",
        default=sample_fraction,
        type=float,
        help="Fraction of data to use for testing (default: 0.1)",
    )
    parser.addoption(
        "--stratify-column",
        action="store",
        default=stratify_column,
        help="Column name to use for stratified sampling (default: participant_id)",
    )
    parser.addoption(
        "--cpu-only",
        action="store_true",
        default=cpu_only,
        help="Force CPU-only execution (default: True)",
    )

def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to skip GPU tests if CPU-only mode is active.
    """
    if config.getoption("--cpu-only") or cpu_only:
        skip_gpu = pytest.mark.skip(reason="Skipping GPU test in CPU-only mode")
        for item in items:
            if "gpu" in item.keywords:
                item.add_marker(skip_gpu)

@pytest.hookimpl(tryfirst=True)
def pytest_report_header(config):
    """
    Add custom header information to the test report.
    """
    return [
        f"CPU-Only Mode: {config.getoption('--cpu-only') or cpu_only}",
        f"Sample Fraction: {config.getoption('--sample-fraction')}",
        f"Stratify Column: {config.getoption('--stratify-column')}",
        f"Temp Data Dir: {temp_data_dir}",
        f"Temp Results Dir: {temp_results_dir}",
    ]

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Fixture to ensure temporary directories exist and are cleaned up.
    """
    Path(temp_data_dir).mkdir(parents=True, exist_ok=True)
    Path(temp_results_dir).mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after tests
    if os.path.exists(temp_data_dir):
        shutil.rmtree(temp_data_dir)
    if os.path.exists(temp_results_dir):
        shutil.rmtree(temp_results_dir)

@pytest.fixture
def sample_data_loader():
    """
    Fixture providing a function to load and stratified sample data.
    """
    def load_and_sample(df, fraction=None, stratify_col=None):
        """
        Load dataframe and apply stratified sampling.
        
        Args:
            df (pd.DataFrame): Input dataframe.
            fraction (float): Fraction of data to sample.
            stratify_col (str): Column to stratify by.
        
        Returns:
            pd.DataFrame: Stratified sample.
        """
        import pandas as pd
        if fraction is None:
            fraction = float(os.getenv("PYTEST_SAMPLE_FRACTION", "0.1"))
        if stratify_col is None:
            stratify_col = os.getenv("PYTEST_STRATIFY_COLUMN", "participant_id")
        
        if stratify_col not in df.columns:
            # Fallback to random sampling if stratify column missing
            return df.sample(frac=fraction, random_state=42)
        
        return df.groupby(stratify_col, group_keys=False).apply(
            lambda x: x.sample(frac=fraction, random_state=42)
        )
    
    return load_and_sample

@pytest.fixture
def cpu_only_mode():
    """
    Fixture ensuring tests run in CPU-only mode.
    """
    original_cuda = os.environ.get("CUDA_VISIBLE_DEVICES")
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    yield
    if original_cuda is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = original_cuda
    else:
        os.environ.pop("CUDA_VISIBLE_DEVICES", None)

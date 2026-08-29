import os
import pytest
from pathlib import Path
from config import (
    PROJECT_ROOT, DATA_DIR, MODELS_DIR, REPORTS_DIR,
    LOG_DIR, ERRORS_DIR, FIGURES_DIR, CONTRACTS_DIR,
    RAW_DATA_DIR, CURATED_DATA_DIR, ARTIFACTS_DIR
)

def test_required_directories_exist():
    """
    Verify that the core project directories exist as per T001.
    """
    required_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests",
        DATA_DIR,
        MODELS_DIR,
        REPORTS_DIR,
        LOG_DIR,
        ERRORS_DIR,
        FIGURES_DIR,
        CONTRACTS_DIR,
        RAW_DATA_DIR,
        CURATED_DATA_DIR,
        ARTIFACTS_DIR,
    ]

    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_data_subdirectories_exist():
    """
    Verify specific data subdirectories exist.
    """
    assert (DATA_DIR / "raw").exists()
    assert (DATA_DIR / "curated").exists()
    assert (DATA_DIR / "artifacts").exists()
    assert (DATA_DIR / "logs").exists()

def test_code_and_tests_packages_exist():
    """
    Verify code and tests directories exist.
    """
    assert (PROJECT_ROOT / "code").exists()
    assert (PROJECT_ROOT / "tests").exists()
    assert (PROJECT_ROOT / "models").exists()
    assert (PROJECT_ROOT / "reports").exists()

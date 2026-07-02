"""
Pytest configuration and shared fixtures for the Brain Network Dynamics pipeline.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import Config

@pytest.fixture(scope="session")
def temp_project_root():
    """Create a temporary directory structure mimicking the project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create necessary directories
        dirs = [
            "code", "code/data", "code/analysis", "code/utils",
            "data/raw", "data/processed", "data/metrics",
            "reports", "logs", "figures",
            "tests/unit", "tests/integration", "docs"
        ]
        for d in dirs:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        
        yield tmp_path

@pytest.fixture
def sample_config(temp_project_root):
    """Provide a Config object pointing to the temporary project root."""
    # Mock the project_root attribute temporarily
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        # Re-import to pick up new path if necessary, or just modify the instance
        config = Config(openneuro_id="ds000000", n_subjects=2, stage="preprocess")
        # Override the project root for the test
        config.project_root = temp_project_root
        config.data_raw = temp_project_root / "data" / "raw"
        config.data_processed = temp_project_root / "data" / "processed"
        config.data_metrics = temp_project_root / "data" / "metrics"
        config.reports_dir = temp_project_root / "reports"
        config.figures_dir = temp_project_root / "figures"
        return config
    finally:
        os.chdir(original_cwd)

@pytest.fixture
def mock_subject_data(temp_project_root):
    """Create a minimal mock subject directory structure for testing."""
    subject_dir = temp_project_root / "data" / "raw" / "sub-01" / "func"
    subject_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a dummy NIfTI file (empty but valid header simulation is hard without nibabel)
    # For now, create a placeholder text file to represent data existence
    dummy_file = subject_dir / "sub-01_task-rest_bold.nii.gz"
    dummy_file.touch()
    
    # Create a dummy JSON sidecar
    json_file = subject_dir / "sub-01_task-rest_bold.json"
    json_file.write_text('{"RepetitionTime": 2.0, "TaskName": "rest"}')
    
    return subject_dir

@pytest.fixture(autouse=True)
def setup_env_vars():
    """Ensure necessary environment variables are set for tests."""
    os.environ.setdefault("OPENNEURO_ID", "ds000000")
    yield
    # Cleanup if needed

@pytest.fixture
def caplog_with_level(caplog):
    """Ensure caplog captures the expected level."""
    caplog.set_level(logging.INFO)
    return caplog

import logging

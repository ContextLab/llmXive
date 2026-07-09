"""
Pytest configuration and fixtures for the llmXive project.

Provides:
- Temporary data directories that are cleaned up after tests.
- A mock config fixture to avoid loading real environment configs during tests.
- A logger fixture for capturing log output.
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import numpy as np

# Ensure we can import from the code directory
# The tests are run from the project root, so we add 'code' to the path
import sys
from pathlib import Path
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.config import Config, set_config, reset_config
from utils.logger import get_logger, setup_file_logging
from utils.io import ensure_dir, save_json

@pytest.fixture(scope="session", autouse=True)
def session_tmp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for the entire test session."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="llmxive_test_session_"))
    yield tmp_dir
    # Cleanup after session
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

@pytest.fixture
def tmp_data_dir(session_tmp_dir: Path) -> Generator[Path, None, None]:
    """
    Create a unique temporary directory for each test function within the session's temp dir.
    Simulates the 'data/processed' or 'data/raw' structure for isolated testing.
    """
    test_dir = session_tmp_dir / "test_data" / str(uuid.uuid4())
    ensure_dir(test_dir)
    yield test_dir
    # Cleanup handled by session_tmp_dir

@pytest.fixture
def mock_config(tmp_data_dir: Path) -> Dict[str, Any]:
    """
    Provides a mock configuration dictionary and sets it as the global config.
    Resets the global config after the test to avoid state leakage.
    """
    # Create a minimal config dict
    config_dict = {
        "project": {
            "name": "test_project",
            "root": str(tmp_data_dir),
            "data_dir": str(tmp_data_dir / "data"),
            "state_dir": str(tmp_data_dir / "state"),
            "seed": 42
        },
        "preprocessing": {
            "motion_threshold": 3.0,
            "exclusion_rate": 0.10
        },
        "modeling": {
            "n_draws": 100,
            "n_warmup": 50,
            "n_chains": 2
        }
    }
    
    # Ensure directories exist in the mock config
    ensure_dir(Path(config_dict["project"]["data_dir"]))
    ensure_dir(Path(config_dict["project"]["state_dir"]))

    # Set as global config
    set_config(Config(**config_dict))
    
    yield config_dict
    
    # Reset global config
    reset_config()

@pytest.fixture
def mock_logger(tmp_data_dir: Path) -> Generator[logging.Logger, None, None]:
    """
    Provides a logger that writes to a temporary file in the test directory.
    """
    log_file = tmp_data_dir / "test.log"
    logger = get_logger("test_logger")
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield logger
    # Handler cleanup is handled by logger reset or file system cleanup

@pytest.fixture(autouse=True)
def fix_random_seed():
    """Ensure deterministic random seeds for tests."""
    np.random.seed(42)
    yield
    np.random.seed(None)

# Helper for uuid in fixtures if not imported
import uuid

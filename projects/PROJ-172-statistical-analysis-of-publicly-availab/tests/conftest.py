"""
Pytest configuration and shared fixtures for the llmXive sports prediction pipeline.

This file sets up the test environment, including:
- Project root path configuration
- Mock fixtures for data loading to prevent external network calls during unit tests
- Temporary directory management for artifact generation
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Generator, Any, Dict, List

import pytest
import pandas as pd

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add the project root to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Also ensure the 'code' directory is importable if needed
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield
    
    # Cleanup if necessary (usually not needed for sys.path)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test artifacts and clean up afterwards.
    Yields the path to the temporary directory.
    """
    tmp_path = Path(tempfile.mkdtemp(prefix="llmxive_test_"))
    yield tmp_path
    if tmp_path.exists():
        shutil.rmtree(tmp_path)

@pytest.fixture
def mock_game_record() -> pd.DataFrame:
    """
    Provide a mock GameRecord DataFrame for testing data loading pipelines.
    Simulates a small subset of real MLB game data structure.
    """
    data = {
        "game_id": ["game_001", "game_002", "game_003"],
        "date": ["2018-05-01", "2018-05-02", "2019-06-15"],
        "home_team": ["NYY", "BOS", "LAD"],
        "away_team": ["TB", "TOR", "SF"],
        "home_score": [5, 2, 7],
        "away_score": [3, 4, 2],
        "home_hits": [10, 6, 12],
        "away_hits": [8, 9, 5],
        "home_errors": [0, 1, 0],
        "away_errors": [1, 0, 2],
        "home_pitches": [145, 132, 158],
        "away_pitches": [138, 140, 125],
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_team_metrics() -> pd.DataFrame:
    """
    Provide a mock TeamMetrics DataFrame for testing feature engineering.
    """
    data = {
        "team": ["NYY", "BOS", "LAD"],
        "season": [2018, 2018, 2019],
        "games_played": [162, 162, 162],
        "wins": [100, 108, 106],
        "losses": [62, 54, 56],
        "runs_scored": [807, 907, 823],
        "runs_allowed": [656, 670, 640],
        "batting_avg": [0.265, 0.273, 0.258],
        "era": [3.76, 4.02, 3.89],
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_data_loader_response(mock_game_record: pd.DataFrame) -> MagicMock:
    """
    Mock the return value of the data loader's fetch method.
    Simulates a successful API response with real data structure.
    """
    mock_response = MagicMock()
    mock_response.data = mock_game_record
    mock_response.is_real_data = True
    mock_response.status_code = 200
    return mock_response

@pytest.fixture
def mock_synthetic_fallback(mock_game_record: pd.DataFrame) -> MagicMock:
    """
    Mock the return value when the data loader triggers synthetic fallback.
    """
    mock_response = MagicMock()
    mock_response.data = mock_game_record
    mock_response.is_real_data = False
    mock_response.status_code = 429  # Simulate rate limit triggering fallback
    return mock_response

@pytest.fixture
def mock_config() -> MagicMock:
    """
    Mock the config module to provide predictable paths and seeds for tests.
    """
    mock_cfg = MagicMock()
    mock_cfg.PROJECT_ROOT = Path(__file__).parent.parent
    mock_cfg.DATA_RAW_DIR = mock_cfg.PROJECT_ROOT / "data" / "raw"
    mock_cfg.DATA_PROCESSED_DIR = mock_cfg.PROJECT_ROOT / "data" / "processed"
    mock_cfg.RANDOM_SEED = 42
    return mock_cfg

@pytest.fixture
def mock_logger() -> MagicMock:
    """
    Mock the logging utility to capture log calls without writing to disk.
    """
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.exception = MagicMock()
    return mock_logger

@pytest.fixture
def sample_processed_data() -> pd.DataFrame:
    """
    Provide a sample processed dataset for model training tests.
    Includes features and target variable.
    """
    data = {
        "game_id": ["g1", "g2", "g3", "g4", "g5"],
        "date": ["2018-01-01", "2018-01-02", "2018-01-03", "2019-01-01", "2019-01-02"],
        "home_avg": [0.260, 0.270, 0.255, 0.265, 0.280],
        "away_avg": [0.240, 0.250, 0.260, 0.255, 0.245],
        "home_era": [3.50, 4.00, 3.80, 3.60, 3.90],
        "away_era": [4.20, 3.90, 4.10, 4.00, 3.70],
        "home_woba": [0.320, 0.330, 0.310, 0.325, 0.340],
        "away_woba": [0.300, 0.310, 0.315, 0.305, 0.290],
        "target_home_win": [1, 0, 1, 1, 1],  # 1 if home wins, 0 otherwise
    }
    return pd.DataFrame(data)

# Global patch fixtures for common modules
@pytest.fixture(autouse=True)
def patch_config():
    """
    Automatically patch the config module to ensure tests run with predictable settings.
    """
    with patch("config") as mock_config:
        mock_config.PROJECT_ROOT = Path(__file__).parent.parent
        mock_config.RANDOM_SEED = 42
        mock_config.DATA_RAW_DIR = mock_config.PROJECT_ROOT / "data" / "raw"
        mock_config.DATA_PROCESSED_DIR = mock_config.PROJECT_ROOT / "data" / "processed"
        yield mock_config

@pytest.fixture(autouse=True)
def patch_logging():
    """
    Automatically patch logging to prevent side effects during tests.
    """
    with patch("utils.logging") as mock_logging:
        mock_logger = MagicMock()
        mock_logging.get_logger.return_value = mock_logger
        mock_logging.log_info = MagicMock()
        mock_logging.log_warning = MagicMock()
        mock_logging.log_error = MagicMock()
        mock_logging.log_debug = MagicMock()
        mock_logging.log_exception = MagicMock()
        yield mock_logging
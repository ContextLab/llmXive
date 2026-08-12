"""
Pytest configuration and shared fixtures for the Sports Prediction Pipeline.

This module sets up the test environment, including temporary directories,
logging configuration, and mock fixtures for data loading to ensure
tests can run in isolation without requiring real external data sources
(unless explicitly testing the loader against real data).
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from typing import Generator, Optional
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

# Add project root to path to allow imports from code/
# Assuming tests/ is at the root level alongside code/
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for tests to avoid noise but allow debugging
@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for all tests to capture output without cluttering stdout."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Silence specific noisy libraries if necessary
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    yield

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test artifacts.
    Ensures tests do not pollute the actual data/ or artifacts/ directories.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_game_data() -> pd.DataFrame:
    """
    Create a minimal, valid sample DataFrame mimicking the structure
    expected by the data loader and feature engineering modules.
    
    This fixture provides REAL-structure data (correct column names/types)
    but with synthetic values for testing logic, not for statistical analysis.
    """
    data = {
        'game_id': ['game_001', 'game_002', 'game_003'],
        'date': ['2019-04-01', '2019-04-02', '2020-07-01'], # Includes 2020 pandemic
        'home_team': ['NYY', 'BOS', 'LAD'],
        'away_team': ['TB', 'NYY', 'SD'],
        'home_score': [5, 3, 2],
        'away_score': [3, 4, 1],
        'home_hits': [10, 8, 6],
        'away_hits': [7, 9, 5],
        'home_errors': [0, 1, 0],
        'away_errors': [1, 0, 2],
        'home_pitches': [145, 132, 120],
        'away_pitches': [138, 140, 115],
        'home_strikes': [95, 88, 80],
        'away_strikes': [85, 92, 75],
        'home_walks': [4, 3, 2],
        'away_walks': [3, 2, 3],
        'home_homeruns': [1, 0, 0],
        'away_homeruns': [0, 1, 0],
        'home_batting_avg': [0.285, 0.270, 0.260],
        'away_batting_avg': [0.260, 0.290, 0.240],
        'home_era': [3.50, 4.20, 3.80],
        'away_era': [3.80, 3.50, 4.00],
        # Advanced metrics (often missing in raw data, used for testing imputation)
        'home_woba': [0.340, 0.330, 0.320],
        'away_woba': [0.320, 0.350, 0.310],
        'home_babip': [0.300, 0.290, 0.280],
        'away_babip': [0.290, 0.310, 0.270],
    }
    df = pd.DataFrame(data)
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    return df

@pytest.fixture
def mock_data_loader() -> MagicMock:
    """
    Mock fixture for the data loader module.
    Replaces the actual network calls and file I/O with controlled returns.
    """
    mock_loader = MagicMock()
    mock_loader.fetch_data.return_value = pd.DataFrame({
        'game_id': ['mock_game'],
        'date': ['2019-01-01'],
        'home_team': ['TEAM_A'],
        'away_team': ['TEAM_B'],
        'home_score': [5],
        'away_score': [3],
        # Add minimal required columns for feature engineering to run
        'home_hits': [10], 'away_hits': [8],
        'home_errors': [0], 'away_errors': [1],
        'home_pitches': [150], 'away_pitches': [145],
        'home_strikes': [100], 'away_strikes': [95],
        'home_walks': [5], 'away_walks': [4],
        'home_homeruns': [2], 'away_homeruns': [1],
        'home_batting_avg': [0.250], 'away_batting_avg': [0.240],
        'home_era': [3.00], 'away_era': [3.50],
    })
    mock_loader.fetch_data.return_value['date'] = pd.to_datetime(mock_loader.fetch_data.return_value['date'])
    mock_loader.is_real_data = True
    return mock_loader

@pytest.fixture
def mock_feature_engineering() -> MagicMock:
    """
    Mock fixture for the feature engineering module.
    """
    mock_fe = MagicMock()
    mock_fe.calculate_traditional_metrics.return_value = pd.DataFrame({
        'game_id': ['mock_game'],
        'home_avg': [0.250],
        'away_avg': [0.240],
        'home_era': [3.00],
        'away_era': [3.50],
        'home_score': [5],
        'away_score': [3],
        'date': ['2019-01-01'],
    })
    mock_fe.calculate_advanced_metrics.return_value = pd.DataFrame({
        'game_id': ['mock_game'],
        'home_woba': [0.330],
        'away_woba': [0.320],
        'home_babip': [0.300],
        'away_babip': [0.290],
    })
    mock_fe.apply_temporal_split.return_value = {
        'train': mock_fe.calculate_traditional_metrics.return_value,
        'test': mock_fe.calculate_traditional_metrics.return_value,
    }
    return mock_fe

@pytest.fixture
def config_paths(temp_dir: Path) -> dict:
    """
    Generate configuration paths pointing to the temporary directory.
    Useful for testing file I/O without touching the real project structure.
    """
    return {
        'data_raw': temp_dir / 'data' / 'raw',
        'data_processed': temp_dir / 'data' / 'processed',
        'artifacts_reports': temp_dir / 'artifacts' / 'reports',
        'artifacts_figures': temp_dir / 'artifacts' / 'figures',
        'state': temp_dir / 'state',
    }
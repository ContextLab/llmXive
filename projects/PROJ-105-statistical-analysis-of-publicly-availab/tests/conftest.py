"""
Pytest configuration and base test fixtures for the flight delay analysis pipeline.

This module provides:
- Fixtures for temporary data directories
- Fixtures for sample data generation (used only in unit tests, not for final analysis)
- Integration with project configuration and utilities
"""

import os
import sys
import tempfile
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional

import pytest
import pandas as pd
import numpy as np

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import RANDOM_SEED
from code.utils import setup_logging, check_memory_limit


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-scoped fixture to set up the test environment.
    Configures logging and validates memory limits for the test run.
    """
    # Set random seed for reproducibility in tests
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)

    # Setup logging for tests (redirect to stderr to avoid file clutter)
    logger = setup_logging()
    logger.info("Test environment initialized")

    # Check memory limit (using a lower threshold for tests if needed)
    try:
        check_memory_limit(limit_gb=1.0)  # Lower limit for test safety
    except MemoryError as e:
        pytest.skip(f"Memory limit exceeded: {e}")

    yield

    logger.info("Test environment teardown complete")


@pytest.fixture
def temp_data_dir():
    """
    Creates a temporary directory for test data that is cleaned up after the test.
    Yields the path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "test_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        yield data_dir


@pytest.fixture
def sample_flight_data(temp_data_dir) -> Path:
    """
    Creates a small, deterministic sample of flight delay data for unit testing.
    This is NOT real data; it is a synthetic dataset designed to test
    preprocessing logic (filtering, anomaly detection, etc.).

    The data includes:
    - Normal delays (0-60 mins)
    - Anomalies (>1440 mins)
    - Data errors (>10000 mins)
    - Negative delays (to be filtered)
    - Missing values

    Returns:
        Path: Path to the generated CSV file.
    """
    n_records = 100
    data = []

    for i in range(n_records):
        record = {
            "Year": 2023,
            "Month": (i % 12) + 1,
            "DayofMonth": (i % 28) + 1,
            "DayOfWeek": (i % 7) + 1,
            "Carrier": "AA" if i % 2 == 0 else "DL",
            "FlightNum": 100 + i,
            "Origin": "JFK",
            "Dest": "LAX",
            "DepDelay": max(0, np.random.normal(10, 15)) if i % 5 != 0 else np.nan,
            "ArrDelay": max(0, np.random.normal(10, 15)) if i % 5 != 1 else np.nan,
            "Distance": np.random.randint(1000, 3000),
        }

        # Inject specific test cases
        if i == 5:
            record["DepDelay"] = -10  # Negative delay
            record["ArrDelay"] = -5
        elif i == 10:
            record["DepDelay"] = 1500  # Anomaly (>1440)
            record["ArrDelay"] = 1600
        elif i == 15:
            record["DepDelay"] = 12000  # Data error (>10000)
            record["ArrDelay"] = 11000
        elif i == 20:
            record["DepDelay"] = np.nan
            record["ArrDelay"] = np.nan

        data.append(record)

    df = pd.DataFrame(data)
    output_path = temp_data_dir / "sample_flights.csv"
    df.to_csv(output_path, index=False)
    return output_path


@pytest.fixture
def sample_tail_data(temp_data_dir) -> Path:
    """
    Creates a synthetic dataset with a known heavy-tailed distribution for
    testing model fitting and tail estimation logic.
    """
    n_records = 2000
    # Generate Pareto-distributed data (alpha=2.5, scale=10)
    data = np.random.pareto(a=2.5, size=n_records) * 10 + 10
    df = pd.DataFrame({"total_delay": data})

    output_path = temp_data_dir / "sample_tail_data.csv"
    df.to_csv(output_path, index=False)
    return output_path


@pytest.fixture
def mock_config(monkeypatch):
    """
    Monkeypatches config values for testing without affecting global state.
    Usage:
        def test_something(mock_config):
            # config values are overridden
    """
    original_bts_url = os.environ.get("BTS_URL", None)
    original_target_year = os.environ.get("TARGET_YEAR", None)

    monkeypatch.setenv("BTS_URL", "https://mock-bts-url.test/api")
    monkeypatch.setenv("TARGET_YEAR", "2023")

    yield

    # Restore original environment
    if original_bts_url is not None:
        monkeypatch.setenv("BTS_URL", original_bts_url)
    elif "BTS_URL" in os.environ:
        monkeypatch.delenv("BTS_URL")

    if original_target_year is not None:
        monkeypatch.setenv("TARGET_YEAR", original_target_year)
    elif "TARGET_YEAR" in os.environ:
        monkeypatch.delenv("TARGET_YEAR")
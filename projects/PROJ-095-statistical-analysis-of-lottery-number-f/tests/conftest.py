"""
Pytest configuration and fixtures for the Lottery Draw Integrity project.

This module provides:
1. Fixed random seeds for deterministic test execution.
2. Mock data generators for unit testing metrics and analysis.
3. Fixtures for temporary directories and sample datasets.
"""

import os
import json
import random
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Generator, Optional

import pytest
import numpy as np
import pandas as pd

# Set global random seeds for deterministic behavior in tests
# This ensures that any randomness in test data generation or algorithmic
# steps (like bootstrapping) is reproducible.
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Project Root Constants
# We assume the project structure is:
# root/
#   code/
#   data/
#   tests/
#   ...
# We add the 'code' directory to sys.path to allow imports during testing
# if running from the tests directory or via pytest.
ROOT_DIR = Path(__file__).parent.parent
CODE_DIR = ROOT_DIR / "code"
if str(CODE_DIR) not in os.sys.path:
    os.sys.path.insert(0, str(CODE_DIR))

# Fixtures
@pytest.fixture(scope="session", autouse=True)
def set_seed():
    """Ensure a fixed random seed for the entire test session."""
    random.seed(SEED)
    np.random.seed(SEED)

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test artifacts (e.g., CSVs, JSONs)."""
    tmp_path = Path(tempfile.mkdtemp())
    yield tmp_path
    shutil.rmtree(tmp_path)

@pytest.fixture
def sample_draw_numbers() -> List[List[int]]:
    """
    Returns a list of mock draw numbers (6 balls per draw).
    Includes edge cases: all birthdays, no birthdays, consecutive numbers.
    """
    return [
        [1, 2, 3, 4, 5, 6],       # All birthdays, consecutive
        [32, 33, 34, 35, 36, 37], # No birthdays, consecutive
        [1, 10, 15, 20, 25, 30],  # All birthdays, no consecutive
        [32, 35, 40, 42, 45, 49], # No birthdays, no consecutive
        [1, 2, 3, 40, 41, 42],    # Mixed: 3 birthdays consecutive, 3 non-birthdays consecutive
    ]

@pytest.fixture
def sample_metrics_json(sample_draw_numbers) -> Dict[str, Any]:
    """
    Generates a mock metrics.json structure based on sample_draw_numbers.
    Simulates the output of code/metrics.py for testing downstream analysis.
    """
    # Hardcoded expected values based on the logic in code/metrics.py
    # birthday_cluster_ratio = count(b <= 31) / 6
    # consecutive_pattern_count = count of pairs (n, n+1) in sorted draw
    
    metrics = []
    for i, draw in enumerate(sample_draw_numbers):
        draw_sorted = sorted(draw)
        birthday_count = sum(1 for n in draw_sorted if n <= 31)
        birthday_ratio = birthday_count / 6.0
        
        consecutive_count = 0
        for j in range(len(draw_sorted) - 1):
            if draw_sorted[j+1] == draw_sorted[j] + 1:
                consecutive_count += 1
        
        metrics.append({
            "draw_id": i + 1,
            "draw_date": f"2023-01-{i+1:02d}",
            "numbers": draw,
            "birthday_cluster_ratio": round(birthday_ratio, 4),
            "consecutive_pattern_count": consecutive_count,
            "jackpot_amount": 1000000 * (i + 1), # Simulated increasing jackpot
            "total_sales": 50000000 * (i + 1)
        })
    
    return metrics

@pytest.fixture
def temp_metrics_file(temp_dir, sample_metrics_json) -> Path:
    """
    Writes sample_metrics_json to a temporary file and returns the path.
    Output: data/processed/metrics.json equivalent.
    """
    file_path = temp_dir / "metrics.json"
    with open(file_path, "w") as f:
        json.dump(sample_metrics_json, f, indent=2)
    return file_path

@pytest.fixture
def mock_raw_csv(temp_dir) -> Path:
    """
    Creates a mock raw CSV file in temp_dir for ingestion testing.
    Includes headers: draw_date, numbers, total_sales, jackpot_amount
    """
    csv_path = temp_dir / "lottery_draws.csv"
    data = {
        "draw_date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "numbers": [
            "[1, 2, 3, 4, 5, 6]",
            "[32, 33, 34, 35, 36, 37]",
            "[1, 15, 20, 25, 30, 49]"
        ],
        "total_sales": [50000000, 52000000, None], # Include missing sales
        "jackpot_amount": [1000000, 1200000, 1500000]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_data_sources_config(temp_dir) -> Path:
    """
    Creates a mock config/data_sources.json for ingestion testing.
    """
    config_path = temp_dir / "data_sources.json"
    config = {
        "source_name": "Mock UK National Lottery",
        "url": "https://example.com/mock_data.csv"
    }
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path
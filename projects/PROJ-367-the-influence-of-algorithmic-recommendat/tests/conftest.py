"""
Pytest configuration and shared fixtures for the algorithmic recommendations project.

This file configures pytest behavior and provides shared fixtures used across
the test suite. It is located in the tests directory as per the project structure.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Generator, Any, Dict, List

import pytest
import pandas as pd
import numpy as np

# Add the project code directory to the Python path for imports
# This allows tests to import from code/ without installing the package
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Configure logging for tests
@pytest.fixture(autouse=True)
def setup_logging() -> None:
    """Configure logging for test runs."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

@pytest.fixture
def test_data_path() -> Path:
    """Return the path to the test data directory."""
    return project_root / "data" / "test"

@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """
    Provide a sample DataFrame with the required schema for testing.
    
    This fixture creates a realistic mock dataset with:
    - user_id: unique user identifiers
    - session_id: unique session identifiers
    - recommended_categories: list of recommended course categories
    - enrolled_categories: list of enrolled course categories
    - pre_study_history: historical enrollment data for baseline derivation
    """
    data = {
        "user_id": [1, 2, 3, 4, 5],
        "session_id": ["s1", "s2", "s3", "s4", "s5"],
        "recommended_categories": [
            ["math", "physics", "computer_science"],
            ["history", "literature", "art"],
            ["biology", "chemistry", "physics"],
            ["economics", "business", "math"],
            ["music", "art", "history"]
        ],
        "enrolled_categories": [
            ["math", "computer_science"],
            ["history"],
            ["biology", "chemistry"],
            ["economics", "math"],
            ["music"]
        ],
        "pre_study_history": [
            ["math", "physics"],
            ["literature", "art"],
            ["biology"],
            ["economics", "business"],
            ["music", "art"]
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_diversity_scores() -> pd.DataFrame:
    """
    Provide sample diversity scores for testing downstream analysis.
    
    This fixture creates a DataFrame with calculated diversity scores
    that can be used to test modeling and robustness functions.
    """
    data = {
        "user_id": [1, 2, 3, 4, 5],
        "session_id": ["s1", "s2", "s3", "s4", "s5"],
        "recommendation_diversity_score": [1.58, 1.58, 1.58, 1.58, 1.58],
        "learner_diversity_score": [1.0, 0.0, 1.0, 1.58, 0.0],
        "baseline_interest_vector": [
            [0.5, 0.5, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.5, 0.5, 0.0],
            [0.5, 0.0, 0.5, 0.0, 0.0],
            [0.0, 0.5, 0.0, 0.5, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0]
        ],
        "propensity_score": [0.8, 0.2, 0.6, 0.7, 0.3],
        "stabilized_weight": [1.2, 0.8, 1.1, 1.3, 0.9]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_config_dict() -> Dict[str, Any]:
    """
    Provide a mock configuration dictionary for testing.
    
    This fixture returns a dictionary that mimics the structure of
    ProjectConfig, useful for testing functions that expect config objects.
    """
    return {
        "seed": 42,
        "similarity_threshold": 0.5,
        "min_enrollments": 1,
        "max_iterations": 1000,
        "p_value_threshold": 0.05,
        "weight_stability_threshold": 10.0,
        "vif_threshold": 5.0,
        "output_dir": "data/processed",
        "log_level": "INFO"
    }

@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Provide an empty DataFrame with the correct schema for edge case testing."""
    return pd.DataFrame(columns=[
        "user_id",
        "session_id",
        "recommended_categories",
        "enrolled_categories",
        "pre_study_history"
    ])

@pytest.fixture
def dataframe_with_missing_values() -> pd.DataFrame:
    """
    Provide a DataFrame with missing values for testing error handling.
    
    This fixture creates a dataset with:
    - Empty enrolled_categories lists
    - Missing recommended_categories
    - Null values in other fields
    """
    data = {
        "user_id": [1, 2, 3, 4, 5],
        "session_id": ["s1", "s2", "s3", "s4", "s5"],
        "recommended_categories": [
            ["math", "physics"],
            None,
            ["biology"],
            ["economics", "business"],
            []
        ],
        "enrolled_categories": [
            [],
            ["history"],
            None,
            ["economics"],
            ["music"]
        ],
        "pre_study_history": [
            ["math"],
            ["literature"],
            ["biology"],
            None,
            ["music"]
        ]
    }
    return pd.DataFrame(data)

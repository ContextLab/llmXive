"""
PyTest configuration and shared fixtures for schema validation.
"""
import os
import sys
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Common paths
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """
    Creates a temporary directory for output files during testing.
    """
    return tmp_path

@pytest.fixture
def sample_salience_row() -> Dict[str, Any]:
    """
    Returns a dictionary representing a single row from the salience-enriched dataset.
    Used for schema validation contract tests.
    """
    return {
        "scenario_id": "MM_12345",
        "salience_score": 0.75,
        "salience_method": "itti_gvs",
        "image_url": "https://example.com/img.jpg",
        "outcome": "pedestrian_hit",
        "species": "human",
        "age": 30,
        "gender": "male",
        "social_status": "doctor",
        "agency": "pedestrian",
        "choice": "save_pedestrian",
        "lives_saved": 1,
        "lives_lost": 0,
        "text_fallback_used": False
    }

@pytest.fixture
def sample_preprocessed_data(tmp_path: Path) -> Path:
    """
    Creates a temporary CSV file with valid preprocessed data for testing.
    Returns the path to the file.
    """
    csv_path = tmp_path / "test_salience_enriched.csv"
    data = [
        ["scenario_id", "salience_score", "salience_method", "outcome", "species", "age", "gender", "social_status", "agency", "choice", "lives_saved", "lives_lost", "text_fallback_used"],
        ["MM_001", "0.82", "itti_gvs", "pedestrian_hit", "human", "25", "female", "doctor", "pedestrian", "save_pedestrian", "1", "0", "False"],
        ["MM_002", "0.15", "text_heuristic", "vehicle_hit", "human", "45", "male", "lawyer", "driver", "save_driver", "0", "1", "True"],
        ["MM_003", "0.55", "itti_gvs", "collision", "human", "60", "male", "judge", "pedestrian", "save_pedestrian", "1", "0", "False"]
    ]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\n".join([",".join(row) for row in data]))
    return csv_path

@pytest.fixture
def sample_model_params() -> Dict[str, Any]:
    """
    Returns a dictionary representing the expected structure of fitted model parameters.
    """
    return {
        "salience_weight": 0.5,
        "drift_rate": 0.1,
        "threshold": 0.05,
        "log_likelihood": -123.45,
        "aic": 250.9,
        "bic": 260.1,
        "converged": True,
        "iterations": 15
    }

@pytest.fixture
def sample_comparison_report() -> Dict[str, Any]:
    """
    Returns a dictionary representing the expected structure of a model comparison report.
    """
    return {
        "baseline_model": {
            "log_likelihood": -130.0,
            "aic": 265.0,
            "bic": 270.0
        },
        "salience_model": {
            "log_likelihood": -123.45,
            "aic": 250.9,
            "bic": 260.1
        },
        "improvement": {
            "log_likelihood_diff": 6.55,
            "aic_diff": -14.1,
            "bic_diff": -9.9,
            "p_value": 0.02,
            "bonferroni_corrected": False
        },
        "sensitivity_analysis": [
            {"threshold": 0.01, "log_likelihood": -123.5, "aic": 251.0},
            {"threshold": 0.05, "log_likelihood": -123.45, "aic": 250.9},
            {"threshold": 0.10, "log_likelihood": -123.6, "aic": 251.2}
        ]
    }

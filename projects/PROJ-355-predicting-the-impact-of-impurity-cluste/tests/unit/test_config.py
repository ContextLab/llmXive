"""
Unit tests for code/config.py (T005).
"""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.config import (
    get_project_root, 
    get_data_paths, 
    get_config_summary,
    RANDOM_SEED,
    VALIDATED_SOURCE_WHITELIST,
    HYPERPARAMETERS
)

def test_project_root_exists():
    root = get_project_root()
    assert root.exists()
    assert isinstance(root, Path)

def test_data_paths_exist():
    paths = get_data_paths()
    assert "raw" in paths
    assert "processed" in paths
    assert "results" in paths
    assert isinstance(paths["raw"], Path)

def test_random_seed_defined():
    assert RANDOM_SEED == 42

def test_whitelist_defined():
    assert isinstance(VALIDATED_SOURCE_WHITELIST, list)
    assert len(VALIDATED_SOURCE_WHITELIST) > 0
    assert "https://materialsproject.org" in VALIDATED_SOURCE_WHITELIST

def test_hyperparameters_defined():
    assert isinstance(HYPERPARAMETERS, dict)
    assert "k_folds" in HYPERPARAMETERS
    assert "perturbation_magnitude" in HYPERPARAMETERS
    assert "vif_threshold" in HYPERPARAMETERS

def test_config_summary():
    summary = get_config_summary()
    assert "random_seed" in summary
    assert "hyperparameters" in summary
    assert "whitelist" in summary
"""
Unit tests for code/config.py
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    RESULTS_DIR,
    RANDOM_SEED,
    LLM_BATCH_SIZE,
    MAX_TOTAL_BATCH_SIZE,
    DATASET_SAMPLE_SIZE,
    VIF_THRESHOLD,
    get_path,
    get_data_path,
    get_processed_path,
    get_results_path,
)

class TestConfigConstants:
    def test_random_seed_is_defined(self):
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED == 42

    def test_llm_batch_size_constraint(self):
        """LLM batch size must be <= 10"""
        assert LLM_BATCH_SIZE <= 10
        assert LLM_BATCH_SIZE > 0

    def test_max_total_batch_size_constraint(self):
        """Max total batch size must be >= LLM batch size"""
        assert MAX_TOTAL_BATCH_SIZE >= LLM_BATCH_SIZE
        assert MAX_TOTAL_BATCH_SIZE == 50

    def test_dataset_sample_size(self):
        assert DATASET_SAMPLE_SIZE == 800

    def test_vif_threshold(self):
        assert VIF_THRESHOLD == 5.0

class TestConfigPaths:
    def test_project_root_exists(self):
        assert isinstance(PROJECT_ROOT, Path)
        assert PROJECT_ROOT.exists()

    def test_data_dir_structure(self):
        assert isinstance(DATA_DIR, Path)
        assert DATA_DIR.exists()

    def test_raw_dir_exists(self):
        assert DATA_RAW_DIR.exists()
        assert "raw" in str(DATA_RAW_DIR)

    def test_processed_dir_exists(self):
        assert DATA_PROCESSED_DIR.exists()
        assert "processed" in str(DATA_PROCESSED_DIR)

    def test_results_dir_exists(self):
        assert RESULTS_DIR.exists()
        assert "results" in str(RESULTS_DIR)

class TestConfigHelpers:
    def test_get_path(self):
        result = get_path("data/raw")
        assert isinstance(result, Path)
        assert "data" in str(result)
        assert "raw" in str(result)

    def test_get_data_path(self):
        result = get_data_path("test.csv")
        assert isinstance(result, Path)
        assert "data" in str(result)
        assert result.name == "test.csv"

    def test_get_processed_path(self):
        result = get_processed_path("results.json")
        assert isinstance(result, Path)
        assert "processed" in str(result)
        assert result.name == "results.json"

    def test_get_results_path(self):
        result = get_results_path("report.md")
        assert isinstance(result, Path)
        assert "results" in str(result)
        assert result.name == "report.md"

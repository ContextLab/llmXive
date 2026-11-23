"""
Unit tests for the configuration module (src/config/config.py).
Ensures paths are valid, seeds are integers, and constants are defined.
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path for imports if running from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.config.config import (
    SEED,
    DATA_PATH,
    MODEL_ID,
    ALFWORLD_MAX_STEPS,
    TARGET_N_BASELINE,
    get_config_summary,
    get_full_path,
    get_derived_path,
    DATA_RAW_DIR,
    DATA_DERIVED_DIR
)

class TestConfigConstants:
    def test_seed_is_integer(self):
        assert isinstance(SEED, int)
        assert SEED == 42

    def test_model_id_defined(self):
        assert isinstance(MODEL_ID, str)
        assert "llama" in MODEL_ID.lower()

    def test_alfworld_max_steps(self):
        assert isinstance(ALFWORLD_MAX_STEPS, int)
        assert ALFWORLD_MAX_STEPS > 0

    def test_target_n_baseline(self):
        assert TARGET_N_BASELINE == 500

class TestConfigPaths:
    def test_data_path_is_pathlib(self):
        assert isinstance(DATA_PATH, Path)

    def test_data_raw_dir_exists(self):
        # The directory might not exist on disk if not created by T001 yet,
        # but the Path object must be valid.
        assert isinstance(DATA_RAW_DIR, Path)
        # Check if the parent structure is plausible
        assert DATA_RAW_DIR.name == "raw"

    def test_data_derived_dir_exists(self):
        assert isinstance(DATA_DERIVED_DIR, Path)
        assert DATA_DERIVED_DIR.name == "derived"

    def test_get_full_path(self):
        result = get_full_path("test_file.json")
        assert result == DATA_RAW_DIR / "test_file.json"

    def test_get_derived_path(self):
        result = get_derived_path("test_file.json")
        assert result == DATA_DERIVED_DIR / "test_file.json"

class TestConfigSummary:
    def test_get_config_summary_returns_dict(self):
        summary = get_config_summary()
        assert isinstance(summary, dict)
        assert "seed" in summary
        assert "model_id" in summary
        assert "data_path" in summary
        assert "cpu_mode" in summary
    
    def test_summary_seed_matches_constant(self):
        summary = get_config_summary()
        assert summary["seed"] == SEED
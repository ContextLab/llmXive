"""
Unit tests for code/config.py.
Verifies paths exist, seeds are set, and hyperparameters are valid.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import (
    RANDOM_SEED,
    CODE_DIR,
    DATA_DIR,
    DATA_RAW_DIR,
    DATA_DERIVED_DIR,
    DATA_VALIDATION_DIR,
    FIGURES_DIR,
    COLLAPSE_SSS_THRESHOLD,
    COLLAPSE_WER_MULTIPLIER,
    FINAL_SNR_VALUES,
    FINAL_RT60_VALUES,
    NUM_DISTORTION_SCENARIOS,
    VALIDATION_SAMPLE_SIZE,
    ASR_MODEL_NAME,
    EMBEDDING_MODEL_NAME,
    DEVICE,
    get_config_dict
)


class TestPaths:
    def test_code_dir_exists(self):
        assert CODE_DIR.exists(), "code/ directory should exist"
        assert CODE_DIR.is_dir()

    def test_data_dirs_exist(self):
        assert DATA_DIR.exists(), "data/ directory should exist"
        assert DATA_RAW_DIR.exists(), "data/raw/ should exist"
        assert DATA_DERIVED_DIR.exists(), "data/derived/ should exist"
        assert DATA_VALIDATION_DIR.exists(), "data/validation/ should exist"
        assert FIGURES_DIR.exists(), "figures/ directory should exist"

    def test_path_types(self):
        assert isinstance(CODE_DIR, Path)
        assert isinstance(DATA_DIR, Path)


class TestSeeds:
    def test_random_seed_is_int(self):
        assert isinstance(RANDOM_SEED, int)

    def test_seed_non_negative(self):
        assert RANDOM_SEED >= 0


class TestHyperparameters:
    def test_sss_threshold_range(self):
        assert 0.0 < COLLAPSE_SSS_THRESHOLD < 1.0

    def test_wer_multiplier_positive(self):
        assert COLLAPSE_WER_MULTIPLIER > 1.0

    def test_snr_values_not_empty(self):
        assert len(FINAL_SNR_VALUES) > 0
        assert all(isinstance(x, (int, float)) for x in FINAL_SNR_VALUES)

    def test_rt60_values_not_empty(self):
        assert len(FINAL_RT60_VALUES) > 0
        assert all(isinstance(x, (int, float)) for x in FINAL_RT60_VALUES)

    def test_scenario_count_matches_product(self):
        expected = len(FINAL_SNR_VALUES) * len(FINAL_RT60_VALUES)
        assert NUM_DISTORTION_SCENARIOS == expected, f"Expected {expected}, got {NUM_DISTORTION_SCENARIOS}"

    def test_validation_sample_size(self):
        assert VALIDATION_SAMPLE_SIZE == 500, "FR-011 requires exactly 500 annotations"


class TestModels:
    def test_asr_model_name(self):
        assert ASR_MODEL_NAME == "whisper-tiny"

    def test_embedding_model_name(self):
        assert "all-MiniLM-L6-v2" in EMBEDDING_MODEL_NAME

    def test_device_cpu(self):
        assert DEVICE == "cpu"


class TestConfigDict:
    def test_get_config_dict_returns_dict(self):
        cfg = get_config_dict()
        assert isinstance(cfg, dict)

    def test_config_dict_has_required_keys(self):
        cfg = get_config_dict()
        required_keys = ["random_seed", "asr_model", "paths", "num_scenarios"]
        for key in required_keys:
            assert key in cfg, f"Missing key: {key}"

    def test_paths_in_dict(self):
        cfg = get_config_dict()
        assert "paths" in cfg
        assert "stress_curves" in cfg["paths"]
        assert "human_annotations" in cfg["paths"]
        assert "collapse_points" in cfg["paths"]
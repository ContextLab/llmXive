"""
Tests for the configuration module (code/config.py).
"""
import pytest
import os
from pathlib import Path
import sys

# Add the parent directory to the path to allow importing 'code'
# Assuming tests are run from the root or the code directory structure is relative.
# In a real run, this might be handled by pytest configuration or PYTHONPATH.
# Here we assume the test is run from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.config import (
    MODEL_CONFIGS,
    MODEL_IDS,
    SEED,
    MAX_TOKENS,
    TEMPERATURE,
    DATA_RAW_DIR,
    get_model_hf_id,
    get_model_params_m,
)


class TestModelConstants:
    """Test that model constants are correctly defined."""

    def test_model_ids_list(self):
        """Verify the list of model IDs contains the required models."""
        # The task requires GPT2-small, CodeBERT, StarCoder-1B
        # We check the keys in MODEL_CONFIGS as that is the authoritative source
        required_models = {"GPT2-small", "CodeBERT", "StarCoder-1B"}
        assert required_models.issubset(set(MODEL_CONFIGS.keys())), \
            f"Missing required models. Found: {set(MODEL_CONFIGS.keys())}"

    def test_model_hf_ids(self):
        """Verify HuggingFace IDs are correctly mapped."""
        assert get_model_hf_id("GPT2-small") == "gpt2"
        assert get_model_hf_id("CodeBERT") == "microsoft/codebert-base"
        assert get_model_hf_id("StarCoder-1B") == "bigcode/starcoderbase-1b"

    def test_model_param_counts(self):
        """Verify parameter counts are reasonable integers."""
        assert get_model_params_m("GPT2-small") > 0
        assert get_model_params_m("CodeBERT") > 0
        assert get_model_params_m("StarCoder-1B") > 0
        
        # Rough sanity checks
        assert get_model_params_m("GPT2-small") < 200  # ~117M
        assert get_model_params_m("StarCoder-1B") > 500 # ~1B

    def test_inference_settings(self):
        """Verify inference settings match requirements."""
        assert SEED == 42
        assert MAX_TOKENS == 128
        assert TEMPERATURE == 0.0

    def test_unknown_model_raises(self):
        """Verify that requesting an unknown model raises a KeyError."""
        with pytest.raises(KeyError):
            get_model_hf_id("NonExistentModel")
        
        with pytest.raises(KeyError):
            get_model_params_m("NonExistentModel")

class TestDirectoryStructure:
    """Test that required directories exist."""

    def test_data_raw_exists(self):
        """Verify data/raw directory exists."""
        assert DATA_RAW_DIR.exists(), f"data/raw directory does not exist: {DATA_RAW_DIR}"
        assert DATA_RAW_DIR.is_dir(), f"data/raw is not a directory: {DATA_RAW_DIR}"

    def test_data_processed_exists(self):
        """Verify data/processed directory exists (created by config init)."""
        # The config module creates this on import
        from code.config import DATA_PROCESSED_DIR
        assert DATA_PROCESSED_DIR.exists(), f"data/processed directory does not exist: {DATA_PROCESSED_DIR}"
        assert DATA_PROCESSED_DIR.is_dir(), f"data/processed is not a directory: {DATA_PROCESSED_DIR}"

    def test_figures_exists(self):
        """Verify figures directory exists."""
        from code.config import FIGURES_DIR
        assert FIGURES_DIR.exists(), f"figures directory does not exist: {FIGURES_DIR}"
        assert FIGURES_DIR.is_dir(), f"figures directory is not a directory: {FIGURES_DIR}"

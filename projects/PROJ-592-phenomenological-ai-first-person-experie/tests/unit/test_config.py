"""
Unit tests for the configuration module (T004).
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (
    MODEL_ID,
    MODEL_FILENAME,
    MODEL_PATH,
    SEED,
    STRATEGIES,
    SAMPLES_PER_PROMPT,
    NUM_PROMPTS,
    MARKERS,
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_QUALITATIVE_DIR,
)


class TestModelConfiguration:
    """Test model configuration settings."""

    def test_model_is_tinyllama(self):
        """Verify the model is TinyLlama, not a larger model."""
        assert "TinyLlama" in MODEL_ID
        assert "1.1B" in MODEL_ID

    def test_model_filename_is_q4_quantized(self):
        """Verify the model uses Q4 quantization for CPU efficiency."""
        assert "Q4" in MODEL_FILENAME
        assert "gguf" in MODEL_FILENAME.lower()

    def test_model_path_is_in_data_directory(self):
        """Verify model path is under data directory."""
        assert "data" in str(MODEL_PATH)

    def test_seed_is_defined(self):
        """Verify a seed is defined for reproducibility."""
        assert isinstance(SEED, int)
        assert SEED >= 0

    def test_seed_value(self):
        """Verify the seed value is a reasonable number."""
        assert SEED == 42


class TestGenerationParameters:
    """Test generation parameters."""

    def test_strategies_are_complete(self):
        """Verify all four prompting strategies are defined."""
        expected = {"direct", "hypothetical", "comparative", "roleplay"}
        assert set(STRATEGIES) == expected

    def test_strategy_count(self):
        """Verify the correct number of strategies."""
        assert len(STRATEGIES) == 4

    def test_samples_per_prompt_target(self):
        """Verify the target sample count per prompt."""
        assert SAMPLES_PER_PROMPT == 80

    def test_num_prompts(self):
        """Verify the number of base prompts."""
        assert NUM_PROMPTS == 20


class TestMarkerDictionaries:
    """Test phenomenological marker dictionaries (FR-008, FR-009)."""

    def test_markers_structure(self):
        """Verify markers dictionary has required categories."""
        assert "sensory" in MARKERS
        assert "temporal" in MARKERS
        assert "intentional" in MARKERS

    def test_sensory_markers_not_empty(self):
        """Verify sensory markers are populated."""
        assert len(MARKERS["sensory"]) > 0

    def test_temporal_markers_not_empty(self):
        """Verify temporal markers are populated."""
        assert len(MARKERS["temporal"]) > 0

    def test_intentional_markers_not_empty(self):
        """Verify intentional markers are populated."""
        assert len(MARKERS["intentional"]) > 0

    def test_sensory_markers_content(self):
        """Verify sensory markers contain expected keywords."""
        sensory = MARKERS["sensory"]
        assert any("see" in s for s in sensory)
        assert any("hear" in s for s in sensory)
        assert any("feel" in s for s in sensory)

    def test_temporal_markers_content(self):
        """Verify temporal markers contain expected keywords."""
        temporal = MARKERS["temporal"]
        assert any("now" in t for t in temporal)
        assert any("then" in t for t in temporal)
        assert any("before" in t for t in temporal)

    def test_intentional_markers_content(self):
        """Verify intentional markers contain expected keywords."""
        intentional = MARKERS["intentional"]
        assert any("think" in i for i in intentional)
        assert any("believe" in i for i in intentional)
        assert any("perceive" in i for i in intentional)


class TestDirectoryConfiguration:
    """Test directory path configuration."""

    def test_data_raw_dir_exists(self):
        """Verify data/raw directory is configured."""
        assert DATA_RAW_DIR is not None
        assert "raw" in str(DATA_RAW_DIR)

    def test_data_processed_dir_exists(self):
        """Verify data/processed directory is configured."""
        assert DATA_PROCESSED_DIR is not None
        assert "processed" in str(DATA_PROCESSED_DIR)

    def test_data_qualitative_dir_exists(self):
        """Verify data/qualitative directory is configured."""
        assert DATA_QUALITATIVE_DIR is not None
        assert "qualitative" in str(DATA_QUALITATIVE_DIR)

    def test_directories_are_under_data(self):
        """Verify all data directories are under the data root."""
        assert "data" in str(DATA_RAW_DIR)
        assert "data" in str(DATA_PROCESSED_DIR)
        assert "data" in str(DATA_QUALITATIVE_DIR)
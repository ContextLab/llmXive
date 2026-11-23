"""
Unit tests for the base model configuration constants and functions.
"""
import pytest
import sys
from pathlib import Path

# Add the code directory to the path for imports
# Assuming tests are run from the project root or code directory
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from models.config import (
    EMBED_DIM,
    NUM_HEADS,
    PARAMS,
    HEAD_DIM,
    VOCAB_SIZE,
    MAX_SEQ_LENGTH,
    MODEL_TYPE_AR,
    MODEL_TYPE_MDM,
    get_model_config
)

class TestModelConstants:
    """Tests for the raw constant definitions."""
    
    def test_embed_dim(self):
        assert EMBED_DIM == 768, "EMBED_DIM must be 768 per task requirements."
        
    def test_num_heads(self):
        assert NUM_HEADS == 12, "NUM_HEADS must be 12 per task requirements."
        
    def test_params_target(self):
        assert PARAMS == 100_000_000, "PARAMS must be 100M per task requirements."
        
    def test_head_dim_derivation(self):
        # 768 / 12 = 64
        assert HEAD_DIM == 64, "HEAD_DIM must be derived correctly from EMBED_DIM and NUM_HEADS."
        assert EMBED_DIM % NUM_HEADS == 0, "EMBED_DIM must be divisible by NUM_HEADS."
        
    def test_vocab_size(self):
        assert VOCAB_SIZE == 50257, "VOCAB_SIZE should match GPT-2 standard."
        
    def test_max_seq_length(self):
        assert MAX_SEQ_LENGTH == 1024, "MAX_SEQ_LENGTH should be 1024."
        
class TestGetModelConfig:
    """Tests for the get_model_config function."""
    
    def test_autoregressive_config_keys(self):
        config = get_model_config(MODEL_TYPE_AR)
        required_keys = ["type", "embed_dim", "num_heads", "head_dim", "vocab_size"]
        for key in required_keys:
            assert key in config, f"AR config missing required key: {key}"
            
    def test_autoregressive_values(self):
        config = get_model_config(MODEL_TYPE_AR)
        assert config["type"] == MODEL_TYPE_AR
        assert config["embed_dim"] == 768
        assert config["num_heads"] == 12
        
    def test_diffusion_config_keys(self):
        config = get_model_config(MODEL_TYPE_MDM)
        required_keys = ["type", "embed_dim", "num_heads", "num_timesteps", "beta_schedule"]
        for key in required_keys:
            assert key in config, f"MDM config missing required key: {key}"
            
    def test_diffusion_values(self):
        config = get_model_config(MODEL_TYPE_MDM)
        assert config["type"] == MODEL_TYPE_MDM
        assert config["embed_dim"] == 768
        assert config["num_heads"] == 12
        assert config["num_timesteps"] == 1000
        
    def test_invalid_model_type(self):
        with pytest.raises(ValueError, match="Unknown model type"):
            get_model_config("invalid_type")

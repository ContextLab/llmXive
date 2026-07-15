"""
Configuration management for the llmXive research pipeline.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Base project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"

# Default LLM Configuration
DEFAULT_MODEL_REPO = "TheBloke/Llama-2-7B-Chat-GGUF"
DEFAULT_MODEL_FILENAME = "llama-2-7b-chat.Q4_K_M.gguf"

# Inference settings
DEFAULT_N_CTX = 4096  # Context window size
DEFAULT_N_THREADS = 4  # CPU threads for inference
DEFAULT_N_BATCH = 512  # Batch size for prompt processing
DEFAULT_N_PREDICT = 1024  # Max tokens to generate

# Paths
def get_model_path(custom_path: Optional[str] = None) -> str:
    """
    Resolve the model path.
    If custom_path is provided, use it.
    Otherwise, check if the default model exists in the cache.
    If not, the inference engine will handle the download.
    """
    if custom_path:
        return custom_path
    
    # Default cache location (huggingface_hub default)
    # We return the filename; the loader will handle the full path resolution
    # or trigger the download if not found.
    return DEFAULT_MODEL_FILENAME

def get_huggingface_cache_dir() -> Path:
    """Get the HuggingFace cache directory."""
    return Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

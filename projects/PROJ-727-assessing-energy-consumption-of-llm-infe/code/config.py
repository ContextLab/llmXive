"""
Configuration constants for the LLM Energy Consumption Assessment pipeline.

This module defines all global constants used across the project, including
model identifiers, parameter counts, inference settings, and directory paths.
"""
import os
from pathlib import Path

# --- Project Root & Directory Structure ---
# Assuming the script is run from the project root or code/ directory.
# We resolve paths relative to the file location (code/) to ensure robustness.
_BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = _BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = _BASE_DIR / "figures"

# Ensure data/raw/ directory exists as per task requirement
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# --- Inference Settings ---
SEED = 42
MAX_TOKENS = 128
TEMPERATURE = 0.0
TOP_P = 1.0
DO_SAMPLE = False  # Greedy decoding due to temperature=0.0

# --- Model Definitions ---
# List of models to evaluate in order.
# Note: StarCoder-base is replaced by StarCoder-1B due to RAM constraints (FR-001).
MODEL_IDS = [
    "gpt2",
    "codellama/CodeLlama-7b-hf", # Using a standard CodeBERT-like or small Code model if specific one isn't available, but task says CodeBERT.
    # Correction: Task explicitly requests 'CodeBERT'.
    # 'CodeBERT' usually refers to 'microsoft/codebert-base'.
    # 'StarCoder-1B' refers to 'bigcode/starcoderbase-1b' or similar.
]

# Explicit mapping of friendly names to HuggingFace IDs and parameter counts (in millions)
# These are the canonical identifiers for the project.
MODEL_CONFIGS = {
    "GPT2-small": {
        "hf_id": "gpt2",
        "param_count_m": 117,  # ~124M parameters
    },
    "CodeBERT": {
        "hf_id": "microsoft/codebert-base",
        "param_count_m": 125,  # ~125M parameters
    },
    "StarCoder-1B": {
        "hf_id": "bigcode/starcoderbase-1b",
        "param_count_m": 1000, # ~1B parameters
    },
}

# --- Execution Constants ---
# Timeout for individual inference calls (seconds)
INFERENCE_TIMEOUT = 300
# Timeout for evaluation of a single problem (seconds)
EVALUATION_TIMEOUT = 10
# Max retries for model loading
MAX_LOAD_RETRIES = 3

# --- Output Schema Column Names ---
COL_MODEL_ID = "model_id"
COL_PROBLEM_ID = "problem_id"
COL_TOKENS_GENERATED = "tokens_generated"
COL_ENERGY_KWH = "energy_kwh"
COL_RUNTIME_SECONDS = "runtime_seconds"
COL_PASS_FAIL_STATUS = "pass_fail_status"

# File paths for data artifacts
RAW_DATA_FILE = DATA_RAW_DIR / "human_eval_data.jsonl"
RAW_RESULTS_FILE = DATA_PROCESSED_DIR / "energy_results_raw.csv"
AGGREGATED_RESULTS_FILE = DATA_PROCESSED_DIR / "energy_results_aggregated.csv"
STATS_REPORT_FILE = DATA_PROCESSED_DIR / "stats_report.csv"
SENSITIVITY_DELTA_FILE = DATA_PROCESSED_DIR / "sensitivity_delta.csv"
SCATTER_SLOPE_FILE = DATA_PROCESSED_DIR / "scatter_slope.txt"

# Figure paths
BAR_PLOT_FILE = FIGURES_DIR / "energy_bar.png"
SCATTER_PLOT_FILE = FIGURES_DIR / "tradeoff_scatter.png"

def get_model_hf_id(model_name: str) -> str:
    """
    Retrieve the HuggingFace model ID for a given friendly name.
    
    Args:
        model_name: One of "GPT2-small", "CodeBERT", "StarCoder-1B".
        
    Returns:
        The corresponding HuggingFace model ID string.
        
    Raises:
        KeyError: If the model name is not found in MODEL_CONFIGS.
    """
    if model_name not in MODEL_CONFIGS:
        raise KeyError(f"Unknown model name: {model_name}. Valid options: {list(MODEL_CONFIGS.keys())}")
    return MODEL_CONFIGS[model_name]["hf_id"]

def get_model_params_m(model_name: str) -> int:
    """
    Retrieve the parameter count (in millions) for a given model name.
    
    Args:
        model_name: One of "GPT2-small", "CodeBERT", "StarCoder-1B".
        
    Returns:
        Parameter count in millions.
    """
    if model_name not in MODEL_CONFIGS:
        raise KeyError(f"Unknown model name: {model_name}")
    return MODEL_CONFIGS[model_name]["param_count_m"]

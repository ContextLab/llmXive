"""
Configuration management for the llmXive Guava follow-up project.

Centralizes seeds, file paths, and hyperparameters to ensure reproducibility
and consistent environment setup across all pipeline stages.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import random
import numpy as np
import torch

# Project root relative to this file (utils/config.py is 2 levels deep)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_ROOT = PROJECT_ROOT / "code"
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA_ROOT = DATA_ROOT / "raw"
PROCESSED_DATA_ROOT = DATA_ROOT / "processed"
ARTIFACTS_ROOT = DATA_ROOT / "artifacts"

# Specific data sub-paths
GUAVA_RAW_PATH = RAW_DATA_ROOT / "guava"
SYMBOLIC_OUTPUT_PATH = PROCESSED_DATA_ROOT / "symbolic_guava"
PERCEPTION_LOG_PATH = ARTIFACTS_ROOT / "perception_log.json"
TRAINING_METRICS_PATH = ARTIFACTS_ROOT / "training_metrics.json"
EVALUATION_RESULTS_PATH = ARTIFACTS_ROOT / "evaluation_results.json"
SC004_VERIFICATION_PATH = ARTIFACTS_ROOT / "sc004_verification.json"
GPU_ESCAPE_LOG_PATH = ARTIFACTS_ROOT / "gpu_escape_log.json"

# Default Seeds
DEFAULT_SEED = 42
PYTORCH_SEED = DEFAULT_SEED
NUMPY_SEED = DEFAULT_SEED
RANDOM_SEED = DEFAULT_SEED

# Hyperparameters - Perception (US1)
YOLO_MODEL_NAME = "yolo_nas_s"  # Or 'yolov8n' depending on ONNX export
YOLO_INPUT_SIZE = (640, 640)
CONFIDENCE_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
MAX_DETECTIONS = 100
LATENCY_THRESHOLD_MS = 150.0  # FR-002, FR-008

# Hyperparameters - Training (US2)
MODEL_NAME_OR_PATH = "microsoft/Phi-3-mini-4k-instruct"
LORA_R = 16
LORA_ALPHA = 32
LORA_DROPOUT = 0.05
TRAIN_BATCH_SIZE = 4
EVAL_BATCH_SIZE = 8
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
MAX_SEQ_LENGTH = 2048
CPU_TRAINING_TIME_LIMIT_HOURS = 4.0
LOSS_DECREASE_TARGET_PERCENT = 15.0

# Hyperparameters - Evaluation (US3)
PERMUTATION_TEST_ITERATIONS = 10000
SEMANTIC_FAILURE_RATIO_THRESHOLD = 0.40
MAX_STEPS_PER_TASK = 100

# Device Configuration
FORCE_CPU = True  # Enforce CPU-only unless GPU escape hatch is triggered

def set_global_seed(seed: Optional[int] = None) -> None:
    """
    Set global random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Args:
        seed: The seed value. Defaults to DEFAULT_SEED if None.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    if torch.cuda.is_available() and not FORCE_CPU:
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    os.environ["PYTHONHASHSEED"] = str(seed)

def ensure_directories() -> None:
    """
    Create all required data directories if they do not exist.
    This should be called at the start of any pipeline execution.
    """
    dirs = [
        RAW_DATA_ROOT,
        PROCESSED_DATA_ROOT,
        ARTIFACTS_ROOT,
        GUAVA_RAW_PATH,
        SYMBOLIC_OUTPUT_PATH,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a dictionary of the current configuration state for logging.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "seed": DEFAULT_SEED,
        "device": "cpu" if FORCE_CPU else ("cuda" if torch.cuda.is_available() else "cpu"),
        "perception": {
            "model": YOLO_MODEL_NAME,
            "input_size": YOLO_INPUT_SIZE,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "latency_threshold_ms": LATENCY_THRESHOLD_MS,
        },
        "training": {
            "model": MODEL_NAME_OR_PATH,
            "lora_r": LORA_R,
            "lora_alpha": LORA_ALPHA,
            "batch_size": TRAIN_BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "time_limit_hours": CPU_TRAINING_TIME_LIMIT_HOURS,
        },
        "evaluation": {
            "permutation_iterations": PERMUTATION_TEST_ITERATIONS,
            "semantic_ratio_threshold": SEMANTIC_FAILURE_RATIO_THRESHOLD,
        }
    }
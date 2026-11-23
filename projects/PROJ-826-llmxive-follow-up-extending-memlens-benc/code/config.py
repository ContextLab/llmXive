"""
Configuration module for the MemLens benchmark extension.
"""
import os

# Model Configuration
MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/Phi-3-mini-4k-instruct")
QUANTIZATION = os.getenv("QUANTIZATION", "4bit")  # Options: '4bit', '8bit', 'none'

# Path Configuration
DATA_DIR = os.getenv("DATA_DIR", "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
STATE_DIR = os.getenv("STATE_DIR", "state/projects/PROJ-826-llmxive-follow-up-extending-memlens-benc")

# Inference Configuration
INFERENCE_OUTPUT_PATH = os.path.join(PROCESSED_DATA_DIR, "inference_results.json")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))

# Resource Limits
MAX_RAM_GB = float(os.getenv("MAX_RAM_GB", "7.0"))
MAX_RUNTIME_HOURS = float(os.getenv("MAX_RUNTIME_HOURS", "6.0"))

# Logging
LOG_DIR = os.path.join(PROCESSED_DATA_DIR, "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

"""
Configuration management for llmXive pipeline.
Defines schema, constants, and state tracking for budget and resource limits.
"""
import os
import sys
import json
import time
import resource
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineConfig:
    def __init__(self):
        self.MAX_RUNTIME_HOURS = 6
        self.MAX_MEMORY_GB = 7
        self.BUDGET = 100
        self.RANDOM_SEED = 42
        self.DATA_DIR = "data/processed"
        self.RESULTS_DIR = "data/results"
        self.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        self.SIMILARITY_THRESHOLD = 0.95
    
    def get(self, key: str, default=None):
        return getattr(self, key, default)

_config = None

def get_config() -> PipelineConfig:
    global _config
    if _config is None:
        _config = PipelineConfig()
    return _config

def update_config(key: str, value: Any):
    cfg = get_config()
    setattr(cfg, key, value)

def format_bytes(b: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.2f} {unit}"
        b /= 1024.0
    return f"{b:.2f} PB"

def check_system_limits():
    # Check memory
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_mem_mb = usage.ru_maxrss
        logger.info(f"Max memory usage: {max_mem_mb} MB")
    except Exception as e:
        logger.warning(f"Could not check system limits: {e}")

def main():
    pass

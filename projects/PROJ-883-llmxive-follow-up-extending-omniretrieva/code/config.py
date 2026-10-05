"""
Configuration module for the llmXive pipeline.

Defines seeds, paths, CPU throttling configuration, and real dataset URLs.
"""

import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Seeds
RANDOM_SEED = 42

# CPU Throttling Constants
EXIT_CODE_THROTTLING_FAILURE = 1

# Dataset URLs (Real Sources)
DATASET_URLS = {
    "ms_marco": "https://huggingface.co/datasets/ms_marco/resolve/main/data/train.parquet",
    "spider": "https://raw.githubusercontent.com/taoyan/Spider/main/spider.json",
    "dbpedia": "https://dbpedia.org/sparql/sparql-endpoint" # Placeholder for actual endpoint or subset
}

# Configuration Dictionary
CONFIG = {
    "num_queries": 100,
    "timeout_seconds": 60,
    "cpu_cores_limit": 2,
    "memory_limit_mb": 2048,
    "dataset_urls": DATASET_URLS,
    "output_paths": {
        "raw_logs": PROJECT_ROOT / "data" / "processed" / "execution_logs.csv",
        "anova_results": PROJECT_ROOT / "data" / "results" / "anova_results.json",
        "sensitivity_analysis": PROJECT_ROOT / "data" / "results" / "sensitivity_analysis.json"
    }
}

def get_config():
    return CONFIG

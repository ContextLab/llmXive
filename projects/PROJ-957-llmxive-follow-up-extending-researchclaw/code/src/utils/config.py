"""
Configuration module for the llmXive automated science pipeline.

This module defines experiment parameters, timeout limits, and constants
required for the ResearchClawBench analysis, specifically including
parameters for the TOST equivalence test on "Scientific Core" scores.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Constants for ResearchClawBench and TOST Equivalence Test (FR-005)
# The dataset ID for the ResearchClawBench benchmark.
# This is the canonical identifier used by the `datasets` library.
RESEARCHCLAWBENCH_DATASET_ID = "llmXive/ResearchClawBench"

# Margin for the Two One-Sided Tests (TOST) equivalence test.
# Used to determine if the difference in "Scientific Core" scores
# between Zero-Shot and Scaffolded conditions is statistically
# equivalent within this margin.
SCIENTIFIC_CORE_MARGIN = 5

# Maximum number of concurrent agent runs.
# Enforced by src/agents/concurrency.py to prevent resource exhaustion.
MAX_CONCURRENCY = 7

# Execution Limits
# Total wall-clock time budget for the entire experiment (in seconds).
# 24 hours = 86400 seconds.
EXPERIMENT_WALL_CLOCK_BUDGET_SECONDS = 86400

# Maximum duration allowed for a single agent run (in seconds).
# If exceeded, the run is marked as "Timeout" and excluded from stats.
SINGLE_RUN_TIMEOUT_SECONDS = 3600

# Statistical Power Threshold
# Minimum acceptable statistical power for the TOST test.
# If power < this value, a warning is logged, but the test proceeds.
MIN_STATISTICAL_POWER = 0.4

# Path Configuration
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
ASSETS_DIR = PROJECT_ROOT / "assets"
ASSETS_TEMPLATES_DIR = ASSETS_DIR / "templates"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SPECS_DIR = PROJECT_ROOT / "specs"

# File Paths
CHECKSUM_FILE = DATA_RAW_DIR / "checksum.txt"
TEMPLATE_MAP_FILE = ASSETS_TEMPLATES_DIR / "template_map.json"
CONSTRAINT_KEYWORDS_FILE = ASSETS_TEMPLATES_DIR / "constraint_keywords.yaml"
RUBRIC_SCHEMA_FILE = CONTRACTS_DIR / "rubric_schema.json"
AGENTS_CONFIG_FILE = PROJECT_ROOT / "agents_config.yaml"

# Output Paths
PAIRED_SCORES_FILE = RESULTS_DIR / "paired_scores.json"
GATE_LOG_FILE = RESULTS_DIR / "verified_accuracy_gate.log"
GATE_DONE_FILE = RESULTS_DIR / "verified_accuracy_gate.done"
AUDIT_IDS_FILE = RESULTS_DIR / "audit_ids.csv"
FAILURE_MODE_AUDIT_FILE = RESULTS_DIR / "failure_mode_audit.csv"
COMPLETION_REPORT_FILE = RESULTS_DIR / "completion_rate_report.json"
ANALYSIS_REPORT_FILE = RESULTS_DIR / "analysis_report.json"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-957-llmxive-follow-up-extending-researchclaw.yaml"

def ensure_directories() -> None:
    """
    Ensures all required project directories exist.
    Creates them if they do not exist.
    """
    directories = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        ASSETS_TEMPLATES_DIR,
        CONTRACTS_DIR,
        SPECS_DIR,
        PROJECT_ROOT / "state" / "projects",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration constants.
    Useful for logging experiment parameters at the start of a run.
    """
    return {
        "dataset_id": RESEARCHCLAWBENCH_DATASET_ID,
        "scientific_core_margin": SCIENTIFIC_CORE_MARGIN,
        "max_concurrency": MAX_CONCURRENCY,
        "experiment_budget_seconds": EXPERIMENT_WALL_CLOCK_BUDGET_SECONDS,
        "single_run_timeout_seconds": SINGLE_RUN_TIMEOUT_SECONDS,
        "min_statistical_power": MIN_STATISTICAL_POWER,
    }

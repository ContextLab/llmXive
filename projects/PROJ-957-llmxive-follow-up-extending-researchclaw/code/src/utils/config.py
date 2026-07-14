"""
Configuration module for llmXive ResearchClawBench follow-up experiment.

This module defines experiment parameters, timeout limits, and constants
required for the TOST equivalence test on "Scientific Core" scores (FR-005).
"""
import os
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
ASSETS_DIR = PROJECT_ROOT / "assets"
SPECS_DIR = PROJECT_ROOT / "specs"

# Dataset Configuration
# Using the canonical Hugging Face dataset ID for ResearchClawBench
RESEARCHCLAWBENCH_DATASET_ID = "researchclaw/researchclaw-bench-v1"

# Statistical Test Parameters (FR-005)
# Margin for TOST equivalence test on "Scientific Core" scores
SCIENTIFIC_CORE_MARGIN = 5

# Concurrency Control
# Maximum number of concurrent agent runs (FR-003, SC-004)
MAX_CONCURRENCY = 7

# Time Budgets (in seconds)
# Total wall-clock budget for the experiment (24 hours)
EXPERIMENT_WALL_CLOCK_BUDGET = 24 * 60 * 60
# Timeout per single agent run (20 minutes)
RUN_TIMEOUT = 20 * 60

# Paths for specific artifacts
CHECKSUM_FILE_PATH = DATA_DIR / "raw" / "checksum.txt"
PROTOCOL_MISMATCH_SUBSET_PATH = DATA_DIR / "processed" / "protocol_mismatch_subset.json"
TEMPLATE_MAP_PATH = ASSETS_DIR / "templates" / "template_map.json"
RUBRIC_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "rubric_schema.json"
CONSTRAINT_KEYWORDS_PATH = ASSETS_DIR / "templates" / "constraint_keywords.yaml"

# Gate Log Files
VERIFIED_ACCURACY_GATE_LOG = RESULTS_DIR / "verified_accuracy_gate.log"
VERIFIED_ACCURACY_GATE_DONE = RESULTS_DIR / "verified_accuracy_gate.done"
AUDIT_IDS_CSV = RESULTS_DIR / "audit_ids.csv"
FAILURE_MODE_AUDIT_CSV = RESULTS_DIR / "failure_mode_audit.csv"
PAIRED_SCORES_JSON = RESULTS_DIR / "paired_scores.json"
COMPLETION_RATE_REPORT_JSON = RESULTS_DIR / "completion_rate_report.json"
ANALYSIS_REPORT_JSON = RESULTS_DIR / "analysis_report.json"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-957-llmxive-follow-up-extending-researchclaw.yaml"

def ensure_directories():
    """Create necessary directories if they do not exist."""
    dirs = [
        DATA_DIR,
        RESULTS_DIR,
        ASSETS_DIR,
        ASSETS_DIR / "templates",
        PROJECT_ROOT / "contracts",
        PROJECT_ROOT / "state" / "projects",
        DATA_DIR / "raw",
        DATA_DIR / "processed",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on module load
ensure_directories()
"""
Configuration module for the llmXive code security evaluation pipeline.

This module defines pinned random seeds, path constants, and model hyperparameters
to ensure reproducibility and consistent execution across the research pipeline.
"""

import os
from pathlib import Path

# --- Project Root & Path Constants ---
# Determine project root relative to this file (code/config.py)
_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Path = _ROOT

# Directory paths
DATA_DIR: Path = PROJECT_ROOT / "data"
CODE_DIR: Path = PROJECT_ROOT / "code"
TESTS_DIR: Path = PROJECT_ROOT / "tests"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
SPEC_DIR: Path = PROJECT_ROOT / "specs"
FIGURES_DIR: Path = DATA_DIR / "figures"
RESULTS_DIR: Path = DATA_DIR / "results"
GENERATED_DIR: Path = DATA_DIR / "generated"
FINDINGS_DIR: Path = DATA_DIR / "findings"
CALIBRATION_DIR: Path = DATA_DIR / "calibration"
PROMPTS_DIR: Path = DATA_DIR / "prompts"
MAPPINGS_DIR: Path = DATA_DIR / "mappings"

# File paths
STATE_FILE: Path = PROJECT_ROOT / "state.yaml"
REQUIREMENTS_FILE: Path = PROJECT_ROOT / "requirements.txt"
LOG_FILE: Path = DATA_DIR / "pipeline.log"
FAILURE_LOG: Path = DATA_DIR / "failures.log"

# Output file paths (explicitly defined for script targets)
RAW_MANIFEST_PATH: Path = PROMPTS_DIR / "raw_manifest.json"
HANDCRAFTED_PROMPTS_PATH: Path = PROMPTS_DIR / "handcrafted.json"
FINAL_MANIFEST_PATH: Path = PROMPTS_DIR / "manifest.json"
NIST_SEVERITY_MAP_PATH: Path = MAPPINGS_DIR / "nist_severity_map.yaml"
SNIPPETS_CSV_PATH: Path = GENERATED_DIR / "snippets.csv"
RAW_FINDINGS_CSV_PATH: Path = FINDINGS_DIR / "raw_findings.csv"
DESCRIPTIVE_STATS_CSV_PATH: Path = RESULTS_DIR / "descriptive_stats.csv"
STATISTICAL_SUMMARY_CSV_PATH: Path = RESULTS_DIR / "statistical_summary.csv"
SENSITIVITY_ANALYSIS_CSV_PATH: Path = RESULTS_DIR / "sensitivity_analysis.csv"
RUN_SUMMARY_CSV_PATH: Path = RESULTS_DIR / "run_summary.csv"
FPR_RESULTS_CSV_PATH: Path = CALIBRATION_DIR / "fpr_results.csv"

# --- Reproducibility: Random Seeds ---
# Pinning seeds for numpy, torch, and python's random to ensure reproducible results
# across runs, given the stochastic nature of LLM sampling and data shuffling.
RANDOM_SEED: int = 42
NUMPY_SEED: int = 42
TORCH_SEED: int = 42
PYTHON_SEED: int = 42

# --- Model Hyperparameters ---
# Defined per task T003 requirements: max_tokens=256, batch_size=1
# These are conservative defaults for CPU-only execution to stay within memory/time limits.

# Generation parameters
MAX_NEW_TOKENS: int = 256
BATCH_SIZE: int = 1
DO_SAMPLE: bool = True
TEMPERATURE: float = 0.7
TOP_P: float = 0.9
TOP_K: int = 50
REPETITION_PENALTY: float = 1.1
MAX_LENGTH: int = 512  # Total sequence length (prompt + generated)

# Model loading parameters (4-bit quantization for CPU)
QUANTIZATION_BITS: int = 4
DEVICE_MAP: str = "auto"
LOW_CPU_MEM_USAGE: bool = True
TRUST_REMOTE_CODE: bool = False

# Target models for the study (StarCoder-Base, CodeGen, GPT-NeoX)
MODEL_IDS: list[str] = [
    "bigcode/starcoderbase-7b",
    "Salesforce/codegen-2B-mono",
    "EleutherAI/gpt-neox-20b"  # Note: Using a smaller variant if 20b is too large for CPU, or specific 1.3b if available.
                               # The task description mentions GPT-NeoX 1.3B. If the specific ID differs, adjust here.
                               # Common 1.3B ID: "EleutherAI/gpt-neo-1.3B" (GPT-Neo, not NeoX) or specific NeoX variants.
                               # Using the standard GPT-NeoX 20B as the base reference, but the pipeline will attempt
                               # to load the specific 1.3B variant if specified in downstream configs.
]

# Specific model mapping for the study scope (T013)
# StarCoder-Base 7B
MODEL_STARCODER: str = "bigcode/starcoderbase-7b"
# CodeGen 2B
MODEL_CODEGEN: str = "Salesforce/codegen-2B-mono"
# GPT-NeoX (Task mentions 1.3B, but standard is 20B. Using a placeholder for the specific 1.3B if it exists,
# otherwise the pipeline must handle the 20B or a smaller compatible variant.
# Based on "GPT-NeoX 1.3B" description, we assume a specific smaller variant or the user intends GPT-Neo.
# We define the ID string here. If the exact 1.3B NeoX ID is not public, the loader must handle fallback.
# For now, using a standard small model ID as a placeholder for the '1.3B' requirement if a specific NeoX 1.3B isn't standard.
# Correction: GPT-NeoX is the family. GPT-Neo is the 1.3B model. The task says "GPT-NeoX 1.3B".
# We will use the ID "EleutherAI/gpt-neo-1.3B" as the closest match to "GPT-NeoX 1.3B" if the user meant GPT-Neo,
# or we assume a specific fine-tune. Let's use the standard GPT-NeoX 20B ID but the config allows override.
# To be safe and adhere to the "1.3B" constraint in the prompt, we will use the GPT-Neo 1.3B ID as the likely intended target.
MODEL_GPTNEOX: str = "EleutherAI/gpt-neo-1.3B"

# --- Timeout & Resource Constraints ---
# From T008: 120s timeout for generation
GENERATION_TIMEOUT_SECONDS: int = 120
SCANNER_TIMEOUT_SECONDS: int = 60

# Resource limits (for safety checks)
MAX_MEMORY_GB: int = 7  # GitHub Actions constraint
MAX_RUNTIME_HOURS: int = 6

# --- Statistical Analysis Parameters ---
ALPHA: float = 0.05
BONFERRONI_ALPHA: float = 0.0167  # 0.05 / 3 comparisons
ZINB_ZERO_THRESHOLD: float = 0.20  # 20% zero-vulnerability threshold for ZINB

# --- Dataset Scope (Amended in T000a) ---
TOTAL_PROMPTS: int = 30
CODEXGLUE_PROMPTS: int = 10
HANDCRAFTED_PROMPTS: int = 20
TOTAL_SNIPPETS: int = 90  # 30 prompts * 3 models

# --- Logging Configuration ---
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
Configuration module for the llmXive CiteVQA benchmark pipeline.
Defines project paths, random seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- Project Paths ---
# All paths are relative to the project root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
RESULTS_DIR: Path = DATA_DIR / "results"
LOGS_DIR: Path = DATA_DIR / "logs"
FIGURES_DIR: Path = DATA_DIR / "figures"
SPECS_DIR: Path = PROJECT_ROOT / "specs"

# Ensure directories exist
def _ensure_dirs() -> None:
    for dir_path in [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR, LOGS_DIR, FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

_ensure_dirs()

# --- Random Seeds ---
# Fixed seeds for reproducibility
SEED: int = 42
PYTHON_SEED: int = SEED
NUMPY_SEED: int = SEED
TORCH_SEED: int = SEED

# --- Hyperparameters ---
# Retrieval
RETRIEVER_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_CHUNKS: int = 5
MAX_QUERY_LENGTH: int = 256
MAX_CHUNK_LENGTH: int = 512

# Reasoning (Text-Only)
REASONER_MODEL_NAME: str = "microsoft/Phi-3-mini-4k-instruct"
REASONER_MAX_NEW_TOKENS: int = 256
REASONER_TEMPERATURE: float = 0.0  # Deterministic for evaluation
REASONER_DO_SAMPLE: bool = False

# Reasoning (Visual-Only Control)
VISUAL_MODEL_NAME: str = "microsoft/phi-3-vision-128k-instruct"
VISUAL_MAX_NEW_TOKENS: int = 256

# Metrics
SEMANTIC_SIMILARITY_THRESHOLD: float = 0.85
IOU_THRESHOLD: float = 0.5
CORRECTNESS_METRIC: str = "answer_correctness"  # 'exact_match' or 'semantic_similarity'

# Statistical Analysis
SIGNIFICANCE_LEVEL: float = 0.05
BOOTSTRAP_ITERATIONS: int = 1000

# Resource Constraints (CPU-Only)
MAX_MEMORY_GB: float = 7.0
MAX_RUNTIME_HOURS: float = 6.0
DEVICE: str = "cpu"
TORCH_DTYPE: str = "float32"  # Could be float16 if supported on CPU, but float32 is safer

# --- Paths for External Data/Config ---
VERIFIED_SOURCES_PATH: Path = DATA_DIR / "verified_sources.json"
BASELINE_SAA_RAW_PATH: Path = DATA_DIR / "baseline_saa_raw.json"
BASELINE_SAA_PATH: Path = DATA_DIR / "baseline_saa.json"

# --- Output Paths ---
TEXT_PIPELINE_RESULTS_PATH: Path = RESULTS_DIR / "text_pipeline_results.json"
STATISTICAL_TEST_RESULTS_PATH: Path = RESULTS_DIR / "statistical_test.json"
SAA_SUMMARY_PATH: Path = RESULTS_DIR / "saa_summary.json"
HALLUCINATION_RATE_PATH: Path = RESULTS_DIR / "hallucination_rate.json"
MODALITY_COMPARISON_PATH: Path = RESULTS_DIR / "modality_comparison.md"
RUNTIME_ESTIMATE_PATH: Path = RESULTS_DIR / "runtime_estimate.json"
MEMORY_PROFILE_LOG_PATH: Path = LOGS_DIR / "memory_profile.log"
SAA_ANALYSIS_PLOT_PATH: Path = FIGURES_DIR / "saa_analysis.png"

# --- Configuration Dictionary ---
# Helper to get a flat dict of all config values for serialization/logging
def get_config_dict() -> Dict[str, Any]:
    """Returns a dictionary of all configuration values."""
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "seed": SEED,
        "retriever_model": RETRIEVER_MODEL_NAME,
        "top_k": TOP_K_CHUNKS,
        "reasoner_model": REASONER_MODEL_NAME,
        "reasoner_max_tokens": REASONER_MAX_NEW_TOKENS,
        "semantic_threshold": SEMANTIC_SIMILARITY_THRESHOLD,
        "iou_threshold": IOU_THRESHOLD,
        "device": DEVICE,
        "max_memory_gb": MAX_MEMORY_GB,
        "max_runtime_hours": MAX_RUNTIME_HOURS,
    }
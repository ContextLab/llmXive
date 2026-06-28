"""
Configuration Module for Code Duplication Impact Research Pipeline

This module centralizes ALL configuration parameters for reproducibility (SC-005).
Every parameter used across the pipeline is defined here with explicit documentation.

Reproducibility Checklist (SC-005):
- Random seeds: All random number generators are seeded identically
- Thresholds: Clone detection thresholds (0.7, 0.8, 0.9) are explicitly documented
- Model parameters: All model loading and inference parameters are specified
- Data parameters: All data loading and processing parameters are defined
- Path configuration: All file paths are centralized and documented
- Logging: All logging configuration is specified
"""

# =============================================================================
# RANDOM SEEDS FOR REPRODUCIBILITY
# =============================================================================
# All random number generators must be seeded with these values to ensure
# reproducible results across runs. This satisfies SC-005 reproducibility requirement.

# Primary random seed - used across all random operations
RANDOM_SEED: int = 42

# Numpy random seed
NUMPY_SEED: int = 42

# PyTorch random seed
TORCH_SEED: int = 42

# Python hash seed for dictionary ordering reproducibility
PYTHONHASHSEED: int = 42

# =============================================================================
# CLONE DETECTION THRESHOLDS (SC-005 Explicit Documentation)
# =============================================================================
# These thresholds define the minimum similarity score for considering code
# segments as clones. Multiple thresholds are used for sensitivity analysis
# (US3, T040). The values 0.7, 0.8, and 0.9 are explicitly documented per SC-005.

# Clone detection thresholds for sensitivity analysis
# T040 requires these three values: 0.7, 0.8, 0.9
CLONE_THRESHOLDS: list[float] = [0.7, 0.8, 0.9]

# Default threshold for primary analysis
DEFAULT_CLONE_THRESHOLD: float = 0.7

# Minimum clone size (number of AST nodes) to consider as a valid clone
MIN_CLONE_SIZE: int = 5

# Maximum clone size (number of AST nodes) to consider
MAX_CLONE_SIZE: int = 500

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================
# All model loading and inference parameters are centralized here.

# Model name for perplexity computation
MODEL_NAME: str = "Salesforce/codegen-350M-mono"

# Model name for bug detection
BUG_DETECTION_MODEL_NAME: str = "Salesforce/codegen-350M-mono"

# Quantization level for memory efficiency (8-bit per SC-002)
QUANTIZATION_BITS: int = 8

# Maximum sequence length for model inference
MAX_SEQUENCE_LENGTH: int = 1024

# Batch size for perplexity computation
PERPLEXITY_BATCH_SIZE: int = 8

# Temperature for text generation (bug detection)
GENERATION_TEMPERATURE: float = 0.0

# Maximum new tokens for generation
MAX_NEW_TOKENS: int = 256

# =============================================================================
# DATA LOADING CONFIGURATION
# =============================================================================
# All data loading parameters are centralized for reproducibility.

# HuggingFace dataset name for code corpus
DATASET_NAME: str = "codeparrot/github-code"

# Subset of dataset to download (500MB per SC-001)
DATASET_SUBSET_SIZE_MB: int = 500

# Streaming mode for large dataset loading
STREAMING_ENABLED: bool = True

# Maximum number of samples to load for testing
TEST_SAMPLE_COUNT: int = 10

# Minimum valid code segments required (SC-003)
MIN_VALID_SEGMENTS: int = 1000

# File extensions to process
SUPPORTED_EXTENSIONS: list[str] = [".py"]

# =============================================================================
# MEMORY CONFIGURATION (SC-002)
# =============================================================================
# Memory limits are enforced per SC-002 requirement.

# Maximum memory limit in megabytes (7GB per SC-002)
MEMORY_LIMIT_MB: int = 7168

# Memory monitoring interval in seconds
MEMORY_MONITOR_INTERVAL: int = 1

# Memory warning threshold (percentage of limit)
MEMORY_WARNING_THRESHOLD: float = 0.8

# =============================================================================
# FILE PATHS CONFIGURATION
# =============================================================================
# All file paths are centralized for maintainability and reproducibility.

# Project root directory (relative to repository root)
PROJECT_ROOT: str = "projects/PROJ-261-evaluating-the-impact-of-code-duplication"

# Data directories
DATA_DIR: str = f"{PROJECT_ROOT}/data"
DATA_RAW_DIR: str = f"{DATA_DIR}/raw"
DATA_PROCESSED_DIR: str = f"{DATA_DIR}/processed"
DATA_ANALYSIS_DIR: str = f"{DATA_DIR}/analysis"
DATA_FIGURES_DIR: str = f"{DATA_ANALYSIS_DIR}/figures"

# Output file paths
CLONE_METRICS_CSV: str = f"{DATA_PROCESSED_DIR}/clone_metrics.csv"
PERPLEXITY_SCORES_CSV: str = f"{DATA_PROCESSED_DIR}/perplexity_scores.csv"
CORRELATION_RESULTS_CSV: str = f"{DATA_ANALYSIS_DIR}/correlation_results.csv"
BUG_DETECTION_RESULTS_CSV: str = f"{DATA_PROCESSED_DIR}/bug_detection_results.csv"
PARSE_FAILURES_CSV: str = f"{DATA_DIR}/parse_failures.csv"
PII_FINDINGS_CSV: str = f"{DATA_ANALYSIS_DIR}/pii_findings.csv"

# Checksum manifest path
CHECKSUM_MANIFEST_PATH: str = f"{DATA_DIR}/checksum_manifest.json"

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
# All logging parameters are centralized for consistent behavior.

# Log level
LOG_LEVEL: str = "INFO"

# Log directory
LOG_DIR: str = f"{DATA_DIR}/logs"

# Log file name
LOG_FILE_NAME: str = "pipeline.log"

# Whether to include timestamps in logs
LOG_INCLUDE_TIMESTAMP: bool = True

# =============================================================================
# HUMAN EVAL CONFIGURATION
# =============================================================================
# Configuration for HumanEval bug detection evaluation.

# HumanEval dataset subset size (50 problems per T031)
HUMANEVAL_SUBSET_SIZE: int = 50

# Number of samples per problem for pass@1 calculation
HUMANEVAL_SAMPLES_PER_PROBLEM: int = 1

# =============================================================================
# CORRELATION ANALYSIS CONFIGURATION
# =============================================================================
# Configuration for statistical correlation analysis.

# Correlation method (Spearman rank correlation)
CORRELATION_METHOD: str = "spearman"

# Significance threshold for p-values
SIGNIFICANCE_THRESHOLD: float = 0.05

# =============================================================================
# VISUALIZATION CONFIGURATION
# =============================================================================
# Configuration for plot generation (US3, T041, T042).

# Figure format for output
FIGURE_FORMAT: str = "png"

# Figure DPI for resolution
FIGURE_DPI: int = 300

# Figure width in inches
FIGURE_WIDTH: int = 10

# Figure height in inches
FIGURE_HEIGHT: int = 8

# Whether to generate PDF format in addition to PNG
GENERATE_PDF: bool = True

# Color map for scatter plots
PLOT_COLORMAP: str = "viridis"

# =============================================================================
# CHECKSUM MANIFEST CONFIGURATION
# =============================================================================
# Configuration for artifact checksum tracking (SC-006).

# Checksum algorithm
CHECKSUM_ALGORITHM: str = "sha256"

# Whether to verify checksums on load
VERIFY_CHECKSUMS: bool = True

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================
# Configuration for performance monitoring (SC-001, SC-002, SC-003).

# Maximum allowed runtime in seconds (24 hours per SC-001)
MAX_RUNTIME_SECONDS: int = 86400

# Performance check interval in seconds
PERFORMANCE_CHECK_INTERVAL: int = 60

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================
# Configuration for PII scanning (Constitution Principle III).

# Whether to enable PII scanning
PII_SCAN_ENABLED: bool = True

# PII patterns to detect
PII_PATTERNS: list[str] = [
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone
    r"\b(?:\d{4}[-.\s]?){3}\d{4}\b",  # Credit card
]

# =============================================================================
# FUNCTIONAL CONFIGURATION ACCESSORS
# =============================================================================
# Helper functions for accessing configuration values.

def get_clone_thresholds() -> list[float]:
    """Return all clone detection thresholds for sensitivity analysis."""
    return CLONE_THRESHOLDS.copy()

def get_random_seed() -> int:
    """Return the primary random seed for reproducibility."""
    return RANDOM_SEED

def get_memory_limit_mb() -> int:
    """Return the memory limit in megabytes (SC-002)."""
    return MEMORY_LIMIT_MB

def get_max_runtime_seconds() -> int:
    """Return the maximum allowed runtime in seconds (SC-001)."""
    return MAX_RUNTIME_SECONDS

def get_min_valid_segments() -> int:
    """Return the minimum valid code segments required (SC-003)."""
    return MIN_VALID_SEGMENTS

def get_correlation_method() -> str:
    """Return the correlation method for analysis."""
    return CORRELATION_METHOD

def get_significance_threshold() -> float:
    """Return the significance threshold for p-values."""
    return SIGNIFICANCE_THRESHOLD

def get_figure_format() -> str:
    """Return the figure format for visualization output."""
    return FIGURE_FORMAT

def get_figure_dpi() -> int:
    """Return the figure DPI for visualization output."""
    return FIGURE_DPI

def get_checksum_algorithm() -> str:
    """Return the checksum algorithm for artifact tracking."""
    return CHECKSUM_ALGORITHM

def get_dataset_name() -> str:
    """Return the HuggingFace dataset name."""
    return DATASET_NAME

def get_model_name() -> str:
    """Return the model name for perplexity computation."""
    return MODEL_NAME

def get_quantization_bits() -> int:
    """Return the quantization bits for model loading."""
    return QUANTIZATION_BITS

def get_streaming_enabled() -> bool:
    """Return whether streaming mode is enabled for dataset loading."""
    return STREAMING_ENABLED

def get_pii_scan_enabled() -> bool:
    """Return whether PII scanning is enabled."""
    return PII_SCAN_ENABLED

def get_all_config() -> dict:
    """Return all configuration parameters as a dictionary for documentation."""
    return {
        "random_seeds": {
            "random_seed": RANDOM_SEED,
            "numpy_seed": NUMPY_SEED,
            "torch_seed": TORCH_SEED,
            "python_hash_seed": PYTHONHASHSEED,
        },
        "clone_detection": {
            "thresholds": CLONE_THRESHOLDS,
            "default_threshold": DEFAULT_CLONE_THRESHOLD,
            "min_clone_size": MIN_CLONE_SIZE,
            "max_clone_size": MAX_CLONE_SIZE,
        },
        "model": {
            "model_name": MODEL_NAME,
            "quantization_bits": QUANTIZATION_BITS,
            "max_sequence_length": MAX_SEQUENCE_LENGTH,
            "perplexity_batch_size": PERPLEXITY_BATCH_SIZE,
            "generation_temperature": GENERATION_TEMPERATURE,
            "max_new_tokens": MAX_NEW_TOKENS,
        },
        "data_loading": {
            "dataset_name": DATASET_NAME,
            "subset_size_mb": DATASET_SUBSET_SIZE_MB,
            "streaming_enabled": STREAMING_ENABLED,
            "test_sample_count": TEST_SAMPLE_COUNT,
            "min_valid_segments": MIN_VALID_SEGMENTS,
            "supported_extensions": SUPPORTED_EXTENSIONS,
        },
        "memory": {
            "memory_limit_mb": MEMORY_LIMIT_MB,
            "monitor_interval": MEMORY_MONITOR_INTERVAL,
            "warning_threshold": MEMORY_WARNING_THRESHOLD,
        },
        "human_eval": {
            "subset_size": HUMANEVAL_SUBSET_SIZE,
            "samples_per_problem": HUMANEVAL_SAMPLES_PER_PROBLEM,
        },
        "correlation": {
            "method": CORRELATION_METHOD,
            "significance_threshold": SIGNIFICANCE_THRESHOLD,
        },
        "visualization": {
            "figure_format": FIGURE_FORMAT,
            "figure_dpi": FIGURE_DPI,
            "figure_width": FIGURE_WIDTH,
            "figure_height": FIGURE_HEIGHT,
            "generate_pdf": GENERATE_PDF,
            "colormap": PLOT_COLORMAP,
        },
        "checksum": {
            "algorithm": CHECKSUM_ALGORITHM,
            "verify_on_load": VERIFY_CHECKSUMS,
        },
        "performance": {
            "max_runtime_seconds": MAX_RUNTIME_SECONDS,
            "check_interval": PERFORMANCE_CHECK_INTERVAL,
        },
        "pii_scanning": {
            "enabled": PII_SCAN_ENABLED,
            "patterns": PII_PATTERNS,
        },
        "logging": {
            "level": LOG_LEVEL,
            "include_timestamp": LOG_INCLUDE_TIMESTAMP,
        },
    }
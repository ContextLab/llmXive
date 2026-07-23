"""
Configuration module for the Chemo Biomarker Discovery pipeline.

Defines paths, random seeds, FDR thresholds, CPU/memory limits, and
gene filtering constants as per the project requirements.
"""
import os
from pathlib import Path
from typing import Final, Dict, Any

# Project Root
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Directory Paths
DATA_RAW_DIR: Final[Path] = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = _PROJECT_ROOT / "data" / "processed"
RESULTS_DIR: Final[Path] = _PROJECT_ROOT / "results"
RESULTS_META_DIR: Final[Path] = RESULTS_DIR / "meta_analysis"
STATE_DIR: Final[Path] = _PROJECT_ROOT / "state"
SPECS_DIR: Final[Path] = _PROJECT_ROOT / "specs" / "001-chemo-biomarker-discovery"
CONTRACTS_DIR: Final[Path] = SPECS_DIR / "contracts"
FIGURES_DIR: Final[Path] = RESULTS_DIR / "figures"

# Random Seeds for Reproducibility
RANDOM_SEED: Final[int] = 42
NUMPY_SEED: Final[int] = 42
PYTORCH_SEED: Final[int] = 42

# Statistical Thresholds
FDR_THRESHOLD: Final[float] = 0.05
LOG2FC_THRESHOLD: Final[float] = 1.0
PVALUE_CUTOFF: Final[float] = 0.01  # For Bonferroni adjusted p-values

# Gene Filtering Constants
MAX_VARIANCE_GENES: Final[int] = 5000  # Top variable genes to retain if needed
MIN_CPM_THRESHOLD: Final[float] = 1.0
MIN_SAMPLES_WITH_CPM: Final[float] = 0.20  # Keep if CPM > 1 in at least 20% of samples
GENE_HGNC_COVERAGE_THRESHOLD: Final[float] = 0.95  # 95%

# Resource Limits
MAX_MEMORY_GB: Final[float] = 14.0
MAX_RUNTIME_HOURS: Final[float] = 5.0
CPU_CORES: Final[int] = 4  # Conservative default for runners

# Data Acquisition Constants
TCGA_MIN_TYPES: Final[int] = 3
GEO_DATASETS: Final[list] = ["GSE25055", "GSE42752"]
HUGGINGFACE_DATASET_ID: Final[str] = "llmXive/chemo-biomarker-dataset"

# Model Hyperparameters (Defaults)
ELASTICNET_L1_RATIO: Final[float] = 0.5
ELASTICNET_C_RANGE: Final[tuple] = (1e-2, 1e2)
CV_FOLDS_INNER: Final[int] = 3
CV_FOLDS_OUTER: Final[int] = 5

# File Names
FEASIBILITY_GATE_FILE: Final[str] = "feasibility_gate.json"
SUMMARY_FILE: Final[str] = "summary.md"
GENE_PANEL_FILE: Final[str] = "gene_panel.json"
CHECKSUMS_FILE: Final[str] = "checksums.json"
ARTIFACT_HASHES_FILE: Final[str] = "artifact_hashes.yaml"
RUNTIME_METRICS_FILE: Final[str] = "runtime_metrics.json"

def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        RESULTS_META_DIR,
        STATE_DIR,
        CONTRACTS_DIR,
        FIGURES_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a dictionary of key configuration values for logging."""
    return {
        "random_seed": RANDOM_SEED,
        "fdr_threshold": FDR_THRESHOLD,
        "max_variance_genes": MAX_VARIANCE_GENES,
        "max_memory_gb": MAX_MEMORY_GB,
        "max_runtime_hours": MAX_RUNTIME_HOURS,
        "tcga_min_types": TCGA_MIN_TYPES,
        "geo_datasets": GEO_DATASETS,
    }

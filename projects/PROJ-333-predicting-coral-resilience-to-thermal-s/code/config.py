"""
Configuration module for the Coral Resilience GWAS pipeline.

This module centralizes all project paths, analysis thresholds, and random seeds
to ensure reproducibility and consistent behavior across the pipeline.

Thresholds are derived from the project specifications:
- MAF > 0.05
- Missingness < 10%
"""

import os
from pathlib import Path

# --- Project Paths ---
# Determine the project root based on the current working directory or script location
# Assuming this script runs from the project root or code/ directory
_current_dir = Path(__file__).parent
_project_root = _current_dir.parent if _current_dir.name == "code" else _current_dir

ROOT_DIR: Path = _project_root
DATA_DIR: Path = ROOT_DIR / "data"
RESULTS_DIR: Path = ROOT_DIR / "results"
CODE_DIR: Path = ROOT_DIR / "code"
TESTS_DIR: Path = ROOT_DIR / "tests"
FIGURES_DIR: Path = RESULTS_DIR / "figures"
REPORTS_DIR: Path = RESULTS_DIR / "reports"

# Specific data subdirectories
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
PLINK_DIR: Path = PROCESSED_DATA_DIR / "plink"
NCBI_DOWNLOAD_DIR: Path = RAW_DATA_DIR / "ncbi"

# --- Analysis Thresholds ---
# Minor Allele Frequency (MAF) threshold: > 0.05
MAF_THRESHOLD: float = 0.05

# Missingness threshold: < 10% (0.10)
MISSINGNESS_THRESHOLD: float = 0.10

# Phenotype requirements
REQUIRED_PHENOTYPE_COLUMNS: list[str] = ["sample_id", "avg_temp_survival"]
BINARY_LABEL_COLUMN: str = "survival_status"  # Optional, if binary labels exist

# PLINK specific filters
PLINK_HWE_THRESHOLD: float = 1e-6  # Hardiness-Weinberg Equilibrium threshold
PLINK_MIN_GENO: float = 0.10  # Maximum missing genotype rate per variant

# --- Random Seeds ---
# Fixed seeds for reproducibility across PCA, sampling, and any stochastic processes
RANDOM_SEED: int = 42
NP_RANDOM_SEED: int = 42
PLINK_SEED: int = 42

# --- Memory Constraints ---
# Maximum RAM usage target in GB (SC-001)
MAX_RAM_GB: float = 7.0

# --- API Endpoints / Sources ---
# NCBI SRA FTP base URL (placeholder for dynamic study ID injection)
NCBI_SRA_BASE_URL: str = "ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/"

# --- Helper Functions ---
def ensure_directories() -> None:
    """Create all necessary project directories if they do not exist."""
    directories = [
        DATA_DIR,
        RESULTS_DIR,
        CODE_DIR,
        TESTS_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        PLINK_DIR,
        NCBI_DOWNLOAD_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_plink_command() -> str:
    """Return the plink2 command. Assumes plink2 is in PATH."""
    return "plink2"

def get_thresholds() -> dict:
    """Return a dictionary of current analysis thresholds."""
    return {
        "maf": MAF_THRESHOLD,
        "missingness": MISSINGNESS_THRESHOLD,
        "hwe": PLINK_HWE_THRESHOLD,
        "min_geno": PLINK_MIN_GENO,
    }

# Initialize directories on import if running as main or explicitly called
# Note: In a pipeline, this might be called explicitly by the orchestrator
if __name__ == "__main__":
    ensure_directories()
    print(f"Project Root: {ROOT_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Thresholds: {get_thresholds()}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("Directories created successfully.")
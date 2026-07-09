"""
Configuration module for the Solar Irradiance Reconstruction project.

Defines project paths, random seeds, and domain-specific constants
required by FR-002 (gap logic) and FR-009 (thresholds).
"""

import os
from pathlib import Path
from typing import Final

# ============================================================================
# Project Root & Directory Paths
# ============================================================================

# Determine project root (parent of the 'code' directory)
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Standardized directory paths
DATA_RAW_DIR: Final[Path] = _PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Final[Path] = _PROJECT_ROOT / "data" / "processed"
CODE_MODELS_DIR: Final[Path] = _PROJECT_ROOT / "code" / "models"
CODE_MODELS_ARTIFACTS_DIR: Final[Path] = CODE_MODELS_DIR / "artifacts"
CODE_ANALYSIS_DIR: Final[Path] = _PROJECT_ROOT / "code" / "analysis"
TESTS_DIR: Final[Path] = _PROJECT_ROOT / "tests"
FIGURES_DIR: Final[Path] = _PROJECT_ROOT / "figures"

# Ensure directories exist (lazy initialization pattern)
def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    for dir_path in [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        CODE_MODELS_DIR,
        CODE_MODELS_ARTIFACTS_DIR,
        CODE_ANALYSIS_DIR,
        TESTS_DIR,
        FIGURES_DIR,
    ]:
        dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Random Seeds & Reproducibility
# ============================================================================

# Global random seed for reproducibility (FR-008 compliance)
RANDOM_SEED: Final[int] = 42

# ============================================================================
# Domain Constants: FR-002 (Gap Logic) & FR-009 (Thresholds)
# ============================================================================

# FR-002: Gap Filling Logic
# Threshold for switching from interpolation to proxy method (in years)
GAP_THRESHOLD_YEARS: Final[float] = 1.0

# Proxy value for GSN during gaps >= 1 year
# Per FR-002: Use GSN=0 proxy, NOT TSI units
GSN_PROXY_VALUE: Final[float] = 0.0

# FR-009: Inconsistency Tolerance Thresholds for Sensitivity Analysis
# Sweep values for absolute differences in TSI reconstruction stability
SENSITIVITY_SWEEP_VALUES: Final[list[float]] = [0.01, 0.05, 0.1]

# ============================================================================
# Data Sources (Real URLs)
# ============================================================================

# SILSO (Royal Observatory of Belgium) - Sunspot Number Data
SILSO_GSN_URL: Final[str] = (
    "https://www.sidc.be/users/eivonne/sol/indices/silso_daily_sn_total.csv"
)

# SORCE/TIM - Total Solar Irradiance Data (Proxy URL for demonstration of real source)
# In a real execution, this would point to the specific NASA PDS or SORCE archive endpoint.
# Using a direct FTP/HTTP link to the processed daily data if available, or a known stable mirror.
SORCE_TSI_URL: Final[str] = (
    "https://lasp.colorado.edu/sorce/data/tim_daily_data.csv"
)

# ============================================================================
# Model Hyperparameters (Defaults)
# ============================================================================

# Random Forest Configuration
RF_MAX_DEPTH: Final[int] = 10
RF_N_ESTIMATORS: Final[int] = 100

# Gaussian Process Kernel Type
GP_KERNEL_TYPE: Final[str] = "RBF"

# Bootstrap Configuration (FR-005)
BOOTSTRAP_ITERATIONS: Final[int] = 1000

# ============================================================================
# Output File Names
# ============================================================================

PREPROCESSED_DATA_FILENAME: Final[str] = "preprocessed_data.parquet"
BEST_MODEL_FILENAME: Final[str] = "best_model.joblib"
FALLBACK_MODEL_FILENAME: Final[str] = "fallback_model.joblib"
CV_REPORT_FILENAME: Final[str] = "cv_report.json"
CYCLE_COEFFICIENTS_FILENAME: Final[str] = "cycle_specific_coefficients.json"
SENSITIVITY_REPORT_FILENAME: Final[str] = "sensitivity_report.json"
RECONSTRUCTION_FILENAME: Final[str] = "reconstruction_1610_2002.parquet"
VARIANCE_ANALYSIS_FILENAME: Final[str] = "variance_analysis.json"
FINAL_REPORT_FILENAME: Final[str] = "final_report.md"

# Full paths to outputs
PREPROCESSED_DATA_PATH: Final[Path] = DATA_PROCESSED_DIR / PREPROCESSED_DATA_FILENAME
BEST_MODEL_PATH: Final[Path] = CODE_MODELS_ARTIFACTS_DIR / BEST_MODEL_FILENAME
FALLBACK_MODEL_PATH: Final[Path] = CODE_MODELS_ARTIFACTS_DIR / FALLBACK_MODEL_FILENAME
CV_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / CV_REPORT_FILENAME
CYCLE_COEFFICIENTS_PATH: Final[Path] = DATA_PROCESSED_DIR / CYCLE_COEFFICIENTS_FILENAME
SENSITIVITY_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / SENSITIVITY_REPORT_FILENAME
RECONSTRUCTION_PATH: Final[Path] = DATA_PROCESSED_DIR / RECONSTRUCTION_FILENAME
VARIANCE_ANALYSIS_PATH: Final[Path] = DATA_PROCESSED_DIR / VARIANCE_ANALYSIS_FILENAME
FINAL_REPORT_PATH: Final[Path] = DATA_PROCESSED_DIR / FINAL_REPORT_FILENAME
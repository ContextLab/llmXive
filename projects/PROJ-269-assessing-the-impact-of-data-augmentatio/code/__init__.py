# llmXive Project: Assessing the Impact of Data Augmentation
# This package contains the core simulation and analysis logic.

from .simulation import run_monte_carlo_simulation
from .augment import (
    apply_gaussian_noise,
    apply_smote,
    apply_random_oversampling,
    detect_zero_variance_samples
)
from .analyze import (
    calculate_error_rates,
    calculate_bootstrap_ci,
    run_ks_test,
    generate_report
)
from .subsample import create_stratified_subsample
from .download_data import download_uci_datasets

__version__ = "0.1.0"
__all__ = [
    "run_monte_carlo_simulation",
    "apply_gaussian_noise",
    "apply_smote",
    "apply_random_oversampling",
    "detect_zero_variance_samples",
    "calculate_error_rates",
    "calculate_bootstrap_ci",
    "run_ks_test",
    "generate_report",
    "create_stratified_subsample",
    "download_uci_datasets"
]

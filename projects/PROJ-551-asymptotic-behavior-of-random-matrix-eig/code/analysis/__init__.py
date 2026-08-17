"""Analysis module for eigenvalue solvers, outlier detection, and sweep utilities."""
from .eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from .outlier_detect import OutlierResult, calculate_bbp_threshold, detect_outliers, run_outlier_analysis
from .checksum_raw import compute_file_sha256, find_raw_matrices, checksum_raw_matrices, main as checksum_main
from .matrix_hygiene import save_matrix_to_npy, save_sparse_matrix_to_npz, run_hygiene_capture, main as hygiene_main
from .raw_matrix_capture import save_raw_wigner_matrix, main as raw_capture_main
from .sweep_hygiene import generate_sweep_configs, run_single_sweep_instance, main as sweep_hygiene_main
from .threshold_sweep import generate_sweep_grid, run_single_sweep_instance, main as threshold_sweep_main
from .threshold_fit import sigmoid_function, load_sweep_results, fit_critical_threshold, run_curve_fitting, main as threshold_fit_main
from .threshold_comparison import load_fitted_thresholds, compare_thresholds, generate_comparison_report, main as comparison_main
from .sweep_matrix_generator import generate_sweep_configs as sweep_gen_configs, save_raw_sweep_matrix, run_sweep_generation, main as sweep_gen_main

__all__ = [
    "compute_top_eigenvalues",
    "validate_eigenvalues",
    "OutlierResult",
    "calculate_bbp_threshold",
    "detect_outliers",
    "run_outlier_analysis",
    "compute_file_sha256",
    "find_raw_matrices",
    "checksum_raw_matrices",
    "checksum_main",
    "save_matrix_to_npy",
    "save_sparse_matrix_to_npz",
    "run_hygiene_capture",
    "hygiene_main",
    "save_raw_wigner_matrix",
    "raw_capture_main",
    "generate_sweep_configs",
    "run_single_sweep_instance",
    "sweep_hygiene_main",
    "generate_sweep_grid",
    "threshold_sweep_main",
    "sigmoid_function",
    "load_sweep_results",
    "fit_critical_threshold",
    "run_curve_fitting",
    "threshold_fit_main",
    "load_fitted_thresholds",
    "compare_thresholds",
    "generate_comparison_report",
    "comparison_main",
    "save_raw_sweep_matrix",
    "run_sweep_generation",
    "sweep_gen_main"
]
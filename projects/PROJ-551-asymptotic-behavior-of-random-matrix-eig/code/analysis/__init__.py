"""
Analysis module initialization.
"""
from .eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from .outlier_detect import detect_outliers, calculate_bbp_threshold, OutlierResult
from .matrix_hygiene import save_matrix_to_npy, save_sparse_matrix_to_npz, run_hygiene_capture
from .sweep_hygiene import generate_sweep_configs, run_single_sweep_instance as sweep_hygiene_runner
from .threshold_sweep import generate_sweep_grid, run_single_sweep_instance, main

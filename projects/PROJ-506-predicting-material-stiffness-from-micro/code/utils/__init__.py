# utils package
"""
Utility package for core algorithms, metrics, and project management.
Includes FFT homogenization, performance metrics, state management, and verification tools.
"""
from .fft_homogenization import compute_effective_stiffness, compute_stiffness_from_image
from .metrics import mean_absolute_error, mean_squared_error, r2_score
from .state_manager import load_state_file, compute_file_hash, update_project_state
from .verify_constitution import verify_constitution, main as verify_const_main
from .verify_spec import verify_spec, main as verify_spec_main
from .verify_spec_anova import verify_anova_mention, main as verify_anova_main
from .verify_structure import check_structure, print_tree_structure, main as verify_struct_main
from .setup_linting import check_command_available, create_pyproject_config, validate_config_files, main as lint_main

__all__ = [
    "compute_effective_stiffness",
    "compute_stiffness_from_image",
    "mean_absolute_error",
    "mean_squared_error",
    "r2_score",
    "load_state_file",
    "compute_file_hash",
    "update_project_state",
    "verify_constitution",
    "verify_spec",
    "verify_anova_mention",
    "check_structure",
    "print_tree_structure",
    "check_command_available",
    "create_pyproject_config",
    "validate_config_files",
]

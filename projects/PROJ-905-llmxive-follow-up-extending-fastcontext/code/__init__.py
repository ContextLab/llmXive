"""
llmXive FastContext-Lite Project.

This package contains modules for analyzing repository structure regularity
and running efficient context exploration pipelines.
"""

__version__ = "0.1.0"

# Import public APIs for convenience
from .config import get_path, ensure_directories, get_config_dict
from .data_loader import download_dataset, compute_file_sha256, verify_checksum
from .annotation_extractor import extract_ground_truth_annotations
from .static_analysis import (
    calculate_dir_score,
    calculate_test_score,
    calculate_import_score,
    calculate_regularity_score,
    analyze_repository
)
from .stratification import split_repos, load_scores_from_csv, save_sets_to_csv

__all__ = [
    "get_path",
    "ensure_directories",
    "get_config_dict",
    "download_dataset",
    "compute_file_sha256",
    "verify_checksum",
    "extract_ground_truth_annotations",
    "calculate_dir_score",
    "calculate_test_score",
    "calculate_import_score",
    "calculate_regularity_score",
    "analyze_repository",
    "split_repos",
    "load_scores_from_csv",
    "save_sets_to_csv",
]

"""
llmXive HEA Predictive Power Pipeline - Code Package.

This package contains the core implementation for evaluating
the predictive power of machine learning for identifying
novel high-entropy alloy compositions.
"""

from .config import ensure_dirs, setup_logging
from .setup_dirs import create_directory, create_init_file, create_config_files
from .compute_checksum import compute_file_checksum, get_dataset_checksum_from_hf, update_config_checksum, main as checksum_main
from .download_hmao import get_dataset_checksum, compute_file_checksum as download_compute_checksum, main as download_main
from .data_ingestion import (
    load_hmao_dataset,
    validate_dataset_checksum,
    filter_min_elements,
    process_and_save_heas_train,
    generate_all_5_element_combinations,
    load_hmao_index_for_novelty_check,
    sample_holdout_known,
    sample_true_novel,
    strict_composition_compare,
    build_deduplicated_composition_index,
    main as ingestion_main
)

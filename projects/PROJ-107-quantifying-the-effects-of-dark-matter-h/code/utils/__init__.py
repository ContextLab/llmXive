"""
Utilities package for the llmXive pipeline.
"""
from utils.config import (
    load_config,
    get_data_raw_path,
    get_data_processed_path,
    get_figures_path,
    get_millennium_path,
    get_project_root,
    get_output_path,
    get_raw_data_path
)
from utils.io import (
    iter_hdf5_groups,
    iter_csv_chunks,
    save_dataframe_chunked,
    load_config_safe,
    validate_hdf5_structure,
    get_file_size_mb,
    process_halo_chunk
)
from utils.logging import (
    get_pipeline_logger,
    log_pipeline_start,
    log_pipeline_end,
    log_error,
    log_metric,
    get_log_file_path
)

__all__ = [
    # Config
    'load_config',
    'get_data_raw_path',
    'get_data_processed_path',
    'get_figures_path',
    'get_millennium_path',
    'get_project_root',
    'get_output_path',
    'get_raw_data_path',
    # IO
    'iter_hdf5_groups',
    'iter_csv_chunks',
    'save_dataframe_chunked',
    'load_config_safe',
    'validate_hdf5_structure',
    'get_file_size_mb',
    'process_halo_chunk',
    # Logging
    'get_pipeline_logger',
    'log_pipeline_start',
    'log_pipeline_end',
    'log_error',
    'log_metric',
    'get_log_file_path'
]

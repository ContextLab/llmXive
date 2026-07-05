"""
Data ingestion, cleaning, and preprocessing module.
"""
from .download import (
    download_lsms,
    download_nasa_power,
    download_faostat,
    download_lsms_batch,
    download_nasa_power_batch,
    download_faostat_batch,
)
from .clean import (
    clean_and_merge,
    apply_imputation_weights,
    validate_imputation_quality,
    get_imputation_report,
    calculate_design_weights,
    stratified_sample,
    apply_sampling_weights,
    validate_sample_quality,
    save_sampled_data,
    run_sampling_pipeline,
)

"""
Services package for the llmXive automated science pipeline.

This package contains the core data processing and analysis services:
- data_ingestion: Download and validate datasets
- anxiety_scoring: Compute anxiety scores from text
- proxy_extractor: Extract control proxies from metadata
- merge_and_save: Merge results for final analysis (T032)
"""
from code.services.data_ingestion import (
    download_and_validate_dataset,
    validate_existing_dataset,
    run_data_ingestion_pipeline
)
from code.services.anxiety_scoring import (
    filter_text_quality,
    load_anxiety_model,
    compute_anxiety_scores,
    run_full_scoring_pipeline
)
from code.services.proxy_extractor import (
    calculate_filter_applied_contribution,
    calculate_timestamp_regularity,
    calculate_control_proxy,
    run_proxy_extraction_pipeline,
    run_full_proxy_pipeline
)
from code.services.merge_and_save import (
    load_scoring_results,
    load_proxy_results,
    merge_datasets,
    save_final_analysis,
    run_merge_and_save_pipeline
)
from code.services.coverage_validation import (
    validate_coverage,
    run_coverage_validation
)
from code.services.scoring_saver import (
    save_scoring_results,
    run_scoring_saver_pipeline
)
from code.services.proxy_saver import (
    save_proxy_results,
    run_proxy_saver_pipeline,
    main as proxy_saver_main
)

__all__ = [
    # Data ingestion
    "download_and_validate_dataset",
    "validate_existing_dataset",
    "run_data_ingestion_pipeline",
    # Anxiety scoring
    "filter_text_quality",
    "load_anxiety_model",
    "compute_anxiety_scores",
    "run_full_scoring_pipeline",
    # Proxy extraction
    "calculate_filter_applied_contribution",
    "calculate_timestamp_regularity",
    "calculate_control_proxy",
    "run_proxy_extraction_pipeline",
    "run_full_proxy_pipeline",
    # Merge and save (T032)
    "load_scoring_results",
    "load_proxy_results",
    "merge_datasets",
    "save_final_analysis",
    "run_merge_and_save_pipeline",
    # Coverage validation
    "validate_coverage",
    "run_coverage_validation",
    # Saver utilities
    "save_scoring_results",
    "run_scoring_saver_pipeline",
    "save_proxy_results",
    "run_proxy_saver_pipeline",
    "proxy_saver_main"
]

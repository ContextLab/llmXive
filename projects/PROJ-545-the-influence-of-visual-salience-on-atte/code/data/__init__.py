"""
Data ingestion, preprocessing, and salience computation.
"""

from .download import (
    download_from_url,
    verify_checksum,
    subset_csv,
    download_moral_machine_data,
    main as download_main,
)
from .salience import (
    compute_itti_gvs_salience,
    compute_text_heuristic_salience,
    load_image_from_path,
    load_image_from_url,
    compute_salience_score,
    process_salience_batch,
    main as salience_main,
)
from .preprocess import (
    load_salience_scores,
    load_raw_moral_machine_data,
    handle_missing_images,
    extract_proxy_controls,
    merge_and_finalize,
    validate_output,
    main as preprocess_main,
)

__all__ = [
    # Download
    "download_from_url",
    "verify_checksum",
    "subset_csv",
    "download_moral_machine_data",
    "download_main",
    # Salience
    "compute_itti_gvs_salience",
    "compute_text_heuristic_salience",
    "load_image_from_path",
    "load_image_from_url",
    "compute_salience_score",
    "process_salience_batch",
    "salience_main",
    # Preprocess
    "load_salience_scores",
    "load_raw_moral_machine_data",
    "handle_missing_images",
    "extract_proxy_controls",
    "merge_and_finalize",
    "validate_output",
    "preprocess_main",
]

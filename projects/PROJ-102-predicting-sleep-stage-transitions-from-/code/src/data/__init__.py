"""
Data processing module for Sleep-EDF SC data pipeline.
Handles downloading, preprocessing, and segmentation of sleep data.
"""
from .download import (
    compute_sha256,
    download_file,
    verify_checksum,
    download_subject,
    download_subset,
    handle_missing_subjects,
    main
)
from .preprocess import (
    linear_interpolate_missing,
    bandpass_filter,
    notch_filter,
    preprocess_signal,
    segment_into_epochs,
    extract_transition_windows,
    extract_pre_transition_windows,
    preprocess_subject,
    main
)

"""
Ingestion module for solar wind and geomagnetic data.

This module handles the downloading, parsing, and initial processing of
raw data from ACE/WIND and NOAA sources, as well as synthetic data generation
for pipeline validation when real data is unavailable.
"""

from .align import (
    load_source_data,
    apply_epsilon_floor,
    handle_instrument_transitions,
    detect_and_handle_gaps,
    resample_to_hourly_median,
    validate_temporal_alignment,
    align_data,
    main as align_main,
    check_memory_usage
)

from .download_ace import (
    fetch_ace_data,
    load_synthetic_ace,
    run_ingestion as run_ace_ingestion,
    main as ace_main
)

from .download_noaa import (
    fetch_noaa_kp,
    fetch_noaa_dst,
    load_synthetic_noaa,
    run_ingestion as run_noaa_ingestion,
    main as noaa_main
)

# Note: generate_synthetic_data is intentionally excluded from __init__.py
# as it is a standalone script for synthetic data generation (T021)

__all__ = [
    # Align functions
    'load_source_data',
    'apply_epsilon_floor',
    'handle_instrument_transitions',
    'detect_and_handle_gaps',
    'resample_to_hourly_median',
    'validate_temporal_alignment',
    'align_data',
    'align_main',
    'check_memory_usage',
    
    # ACE ingestion
    'fetch_ace_data',
    'load_synthetic_ace',
    'run_ace_ingestion',
    'ace_main',
    
    # NOAA ingestion
    'fetch_noaa_kp',
    'fetch_noaa_dst',
    'load_synthetic_noaa',
    'run_noaa_ingestion',
    'noaa_main'
]
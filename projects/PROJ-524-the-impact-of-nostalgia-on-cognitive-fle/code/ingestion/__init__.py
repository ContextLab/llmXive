"""
Ingestion Module Package.

This package separates data fetching and validation logic for modularity.

Public API:
- DataFetchError
- DataGapError
- fetch_data (from fetcher)
- validate_and_filter_dataset (from validator)
- save_exclusion_log (from validator)
- load_dataset (helper to orchestrate fetch + validate)
"""
from .fetcher import (
    DataFetchError,
    DataGapError,
    fetch_data,
    fetch_from_openml,
    fetch_from_huggingface,
    fetch_from_url,
    fetch_metadata_from_source,
    fetch_metadata_from_url,
    load_local_file
)

from .validator import (
    validate_schema,
    validate_and_filter_dataset,
    save_exclusion_log,
    clean_data,
    calculate_validity_metrics,
    save_validity_metrics
)

# Re-export for backward compatibility with code/ingestion.py imports
__all__ = [
    'DataFetchError',
    'DataGapError',
    'fetch_data',
    'fetch_from_openml',
    'fetch_from_huggingface',
    'fetch_from_url',
    'fetch_metadata_from_source',
    'fetch_metadata_from_url',
    'load_local_file',
    'validate_schema',
    'validate_and_filter_dataset',
    'save_exclusion_log',
    'clean_data',
    'calculate_validity_metrics',
    'save_validity_metrics'
]

# Optional: Main orchestration function to replace old load_dataset logic
def load_dataset(keywords=None, dataset_id=None, url=None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Orchestrate fetching and validation.
    
    Args:
        keywords: Search keywords.
        dataset_id: Specific dataset ID.
        url: Specific URL.
        
    Returns:
        Tuple of (cleaned_df, metadata)
    """
    import pandas as pd
    from .fetcher import fetch_data, DataGapError
    from .validator import validate_and_filter_dataset, clean_data
    
    df_raw, metadata = fetch_data(keywords=keywords, dataset_id=dataset_id, url=url)
    df_clean, metadata = validate_and_filter_dataset(df_raw, metadata)
    df_clean = clean_data(df_clean)
    return df_clean, metadata

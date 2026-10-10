import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd

from utils import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Exception raised when data fetching fails."""
    pass

class DataGapError(Exception):
    """Exception raised when a required data gap is detected."""
    pass

class RealDataFetchFailed(Exception):
    """Exception raised when real data fetch fails and simulation is required."""
    pass

def fetch_from_openml(dataset_id: int) -> pd.DataFrame:
    """
    Fetches data from OpenML.

    Args:
        dataset_id: The OpenML dataset ID.

    Returns:
        DataFrame with the fetched data.

    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        import openml
        dataset = openml.datasets.get_dataset(dataset_id)
        df, _, _, _ = dataset.get_data()
        log_info(f"Successfully fetched dataset {dataset_id} from OpenML.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from OpenML: {e}")
        raise DataFetchError(f"OpenML fetch failed: {e}")

def fetch_from_huggingface(repo: str, name: str = "wcst", split: str = "train", streaming: bool = False) -> pd.DataFrame:
    """
    Fetches data from HuggingFace Datasets.

    Args:
        repo: The dataset repository identifier.
        name: The dataset configuration name (default "wcst").
        split: The split to load (default "train").
        streaming: Whether to stream the dataset.

    Returns:
        DataFrame with the fetched data.

    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        from datasets import load_dataset
        ds = load_dataset(repo, name=name, split=split, streaming=streaming)
        # If streaming, we need to materialize
        if streaming:
            df = pd.DataFrame(ds)
        else:
            df = ds.to_pandas()
        log_info(f"Successfully fetched dataset {repo} (config={name}) from HuggingFace.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from HuggingFace: {e}")
        raise DataFetchError(f"HuggingFace fetch failed: {e}")

def fetch_from_url(url: str) -> pd.DataFrame:
    """
    Fetches data from a URL (CSV).

    Args:
        url: The URL to the CSV file.

    Returns:
        DataFrame with the fetched data.

    Raises:
        DataFetchError: If the fetch fails.
    """
    try:
        df = pd.read_csv(url)
        log_info(f"Successfully fetched data from {url}.")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch from URL: {e}")
        raise DataFetchError(f"URL fetch failed: {e}")

def fetch_data() -> Tuple[Optional[pd.DataFrame], str, bool]:
    """
    Attempts to fetch real WCST data from public sources.

    Strategy (deterministic order):
    1. Search OpenML for datasets whose name or description contain any of the keywords
       ["WCST","card-sorting","executive function"]; select the dataset with the largest
       row count, breaking ties by the lowest OpenML ID.
    2. If no suitable OpenML dataset is found, attempt to load a HuggingFace dataset
       using a repository identifier (placeholder) with name="wcst".
    3. If that also fails, attempt a direct URL fetch (placeholder URL).

    On success returns (DataFrame, source_identifier, simulation_mode=False).
    On total failure raises RealDataFetchFailed.

    Returns:
        Tuple[DataFrame or None, source identifier string, simulation_mode flag]
    """
    # 1. OpenML search
    try:
        import openml
        log_info("Searching OpenML for WCST-related datasets...")
        df_list = openml.datasets.list_datasets(output_format='dataframe')
        keywords = ["wcst", "card-sorting", "executive function"]
        mask = df_list['name'].str.lower().fillna('').apply(
            lambda x: any(k in x for k in keywords)
        ) | df_list['description'].str.lower().fillna('').apply(
            lambda x: any(k in x for k in keywords)
        )
        candidates = df_list[mask]
        if not candidates.empty:
            # Choose dataset with max instances, then min did
            max_instances = candidates['NumberOfInstances'].max()
            candidates_max = candidates[candidates['NumberOfInstances'] == max_instances]
            selected = candidates_max.loc[candidates_max['did'].idxmin()]
            dataset_id = int(selected['did'])
            log_info(f"Selected OpenML dataset ID {dataset_id} ({selected['name']}) with {max_instances} rows.")
            df = fetch_from_openml(dataset_id)
            source = f"openml:{dataset_id}"
            return df, source, False
        else:
            log_info("No OpenML datasets matched the keywords.")
    except Exception as e:
        log_warning(f"OpenML search/fetch failed: {e}")

    # 2. HuggingFace attempt (placeholder repo - will likely fail)
    try:
        repo = "some_user/wcst_dataset"  # Placeholder; replace with real repo if known
        log_info(f"Attempting HuggingFace fetch from repo '{repo}'...")
        df = fetch_from_huggingface(repo, name="wcst", split="train", streaming=False)
        source = f"huggingface:{repo}"
        return df, source, False
    except Exception as e:
        log_warning(f"HuggingFace fetch failed: {e}")

    # 3. Direct URL attempt (placeholder URL)
    try:
        url = "https://example.com/wcst_data.csv"
        log_info(f"Attempting direct URL fetch from {url}...")
        df = fetch_from_url(url)
        source = f"url:{url}"
        return df, source, False
    except Exception as e:
        log_warning(f"URL fetch failed: {e}")

    # All attempts failed
    log_error("All real data sources failed to fetch.")
    raise RealDataFetchFailed("Could not fetch real WCST data from any source.")

def save_metadata(metadata: Dict[str, Any], filepath: str) -> None:
    """
    Saves metadata to a JSON file.

    Args:
        metadata: Metadata dictionary.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    log_info(f"Metadata saved to {filepath}")

def save_exclusion_log(exclusion_counts: Dict[str, int], filepath: str) -> None:
    """
    Saves exclusion log to a JSON file.

    Args:
        exclusion_counts: Dictionary of exclusion counts.
        filepath: Path to save the file.
    """
    with open(filepath, 'w') as f:
        json.dump(exclusion_counts, f, indent=2)
    log_info(f"Exclusion log saved to {filepath}")

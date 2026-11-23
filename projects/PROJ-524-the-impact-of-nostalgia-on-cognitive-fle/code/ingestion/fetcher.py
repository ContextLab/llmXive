"""
Ingestion fetcher module.

This module provides functions to fetch a real Wisconsin Card Sorting Test (WCST)
dataset from public sources. The primary entry point is ``fetch_data`` which
implements the deterministic search strategy required by task T101.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd

# External libraries – they are added to ``requirements.txt`` below.
import openml
from datasets import load_dataset, Dataset

logger = logging.getLogger(__name__)

class RealDataFetchFailed(RuntimeError):
    """Raised when all attempts to fetch a real dataset fail."""
    pass

class DataFetchError(RuntimeError):
    """General error during data fetching."""
    pass

class DataGapError(RuntimeError):
    """Raised when a fetched dataset is unexpectedly empty."""
    pass

def fetch_from_openml(dataset_id: int) -> pd.DataFrame:
    """
    Fetch a dataset from OpenML given its numeric ID.

    Parameters
    ----------
    dataset_id: int
        The OpenML dataset identifier.

    Returns
    -------
    pd.DataFrame
        The dataset as a DataFrame.

    Raises
    ------
    DataFetchError
        If the OpenML request fails.
    DataGapError
        If the returned data is empty.
    """
    try:
        logger.info(f"Attempting to download OpenML dataset ID {dataset_id}")
        oml_dataset = openml.datasets.get_dataset(dataset_id)
        df, *_ = oml_dataset.get_data()
        if df is None or df.empty:
            raise DataGapError(f"OpenML dataset {dataset_id} returned no rows.")
        return df
    except Exception as exc:
        raise DataFetchError(f"Failed to fetch OpenML dataset {dataset_id}: {exc}") from exc

def fetch_from_huggingface(repo: str, name: str = "wcst", split: str = "train", streaming: bool = False) -> pd.DataFrame:
    """
    Fetch a dataset from the HuggingFace Hub.

    Parameters
    ----------
    repo: str
        The repository identifier (e.g., ``\"username/repo_name\"``).
    name: str, optional
        The configuration name within the repo. Default is ``\"wcst\"``.
    split: str, optional
        Which split to load. Default is ``\"train\"``.
    streaming: bool, optional
        Whether to stream the dataset. Default is ``False``.

    Returns
    -------
    pd.DataFrame
        The dataset as a DataFrame.

    Raises
    ------
    DataFetchError
        If the HuggingFace request fails.
    DataGapError
        If the returned data is empty.
    """
    try:
        logger.info(f"Attempting to download HuggingFace dataset {repo} (name={name}, split={split})")
        hf_dataset: Dataset = load_dataset(repo, name=name, split=split, streaming=streaming)
        # ``hf_dataset`` may be a DatasetDict or a Dataset; we coerce to pandas.
        df = pd.DataFrame(hf_dataset)
        if df.empty:
            raise DataGapError(f"HuggingFace dataset {repo} returned no rows.")
        return df
    except Exception as exc:
        raise DataFetchError(f"Failed to fetch HuggingFace dataset {repo}: {exc}") from exc

def fetch_from_url(url: str) -> pd.DataFrame:
    """
    Fetch a CSV file from a direct URL.

    Parameters
    ----------
    url: str
        The HTTP(S) URL pointing to a CSV file.

    Returns
    -------
    pd.DataFrame
        The dataset as a DataFrame.

    Raises
    ------
    DataFetchError
        If the request fails or the CSV cannot be parsed.
    DataGapError
        If the downloaded CSV is empty.
    """
    import requests
    import io

    try:
        logger.info(f"Attempting to download CSV from URL: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        if df.empty:
            raise DataGapError(f"CSV at {url} contained no rows.")
        return df
    except Exception as exc:
        raise DataFetchError(f"Failed to download CSV from {url}: {exc}") from exc

def _search_openml_by_keywords(keywords: list[str]) -> Optional[Tuple[int, pd.DataFrame]]:
    """
    Search OpenML for datasets whose name or description contains any of the supplied keywords.
    Returns the ID and DataFrame of the best candidate (largest row count, lowest ID on ties) or ``None``.
    """
    try:
        logger.info("Listing OpenML datasets for keyword search")
        catalog = openml.datasets.list_datasets(output_format="dataframe")
    except Exception as exc:
        logger.warning(f"OpenML catalog retrieval failed: {exc}")
        return None

    # Normalise keywords for case‑insensitive matching
    kw_pattern = "|".join([kw.replace("-", " ").replace("‑", " ") for kw in keywords])
    mask = (
        catalog["name"].fillna("").str.contains(kw_pattern, case=False, regex=True)
        | catalog["description"].fillna("").str.contains(kw_pattern, case=False, regex=True)
    )
    candidates = catalog[mask]

    if candidates.empty:
        logger.info("No OpenML datasets matched the keyword filter.")
        return None

    # Choose dataset with most instances; break ties by smallest ID
    candidates["n_instances"] = pd.to_numeric(candidates["NumberOfInstances"], errors="coerce").fillna(0)
    best = candidates.sort_values(
        ["n_instances", "did"], ascending=[False, True]
    ).iloc[0]

    dataset_id = int(best["did"])
    try:
        df = fetch_from_openml(dataset_id)
        return dataset_id, df
    except (DataFetchError, DataGapError) as exc:
        logger.warning(f"Failed to download OpenML candidate ID {dataset_id}: {exc}")
        return None

def fetch_data() -> Tuple[Optional[pd.DataFrame], str, bool]:
    """
    Attempt to fetch a real WCST dataset following the deterministic strategy
    described in task T101.

    Returns
    -------
    tuple
        (DataFrame or ``None``, source identifier string, ``simulation_mode`` flag)

    Raises
    ------
    RealDataFetchFailed
        If none of the data sources provide a usable dataset.
    """
    keywords = ["WCST", "card‑sorting", "executive function"]

    # 1️⃣ OpenML search
    openml_result = _search_openml_by_keywords(keywords)
    if openml_result is not None:
        dataset_id, df = openml_result
        source = f"OpenML:{dataset_id}"
        logger.info(f"Selected OpenML dataset {dataset_id} with {len(df)} rows")
        return df, source, False

    # 2️⃣ HuggingFace attempt – a concrete repository must be known.
    # The specification does not provide a concrete repo; we try a few well‑known
    # candidates that host WCST‑style data. If all fail we move on.
    hf_candidates = [
        "mlcommons/wcst",            # hypothetical
        "openml/wcst",               # another guess
    ]
    for repo in hf_candidates:
        try:
            df = fetch_from_huggingface(repo, name="wcst", split="train", streaming=False)
            source = f"HuggingFace:{repo}"
            logger.info(f"Fetched HuggingFace dataset from {repo} with {len(df)} rows")
            return df, source, False
        except (DataFetchError, DataGapError) as exc:
            logger.warning(f"HuggingFace fetch failed for {repo}: {exc}")

    # 3️⃣ Direct URL fallback – no verified URL is supplied in the current
    # project configuration, so we raise the final error.
    raise RealDataFetchFailed("All attempts to fetch a real WCST dataset failed.")

def save_metadata(metadata: Dict[str, Any], filepath: str) -> None:
    """
    Write a metadata dictionary to ``filepath`` as pretty‑printed JSON.

    Parameters
    ----------
    metadata: dict
        The metadata to persist.
    filepath: str
        Destination path (will be created if necessary).
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"Metadata saved to {filepath}")

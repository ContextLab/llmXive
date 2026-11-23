import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import hashlib
import json
import requests
import datasets
from datasets import load_dataset

class DataFetchError(Exception):
    """Raised when a real data fetch fails."""
    pass

def compute_dataset_checksum(data: List[Dict[str, Any]]) -> str:
    """Compute a deterministic checksum of the dataset content."""
    hasher = hashlib.sha256()
    # Sort keys and items to ensure determinism
    sorted_data = sorted(
        [json.dumps(record, sort_keys=True) for record in data]
    )
    content = "\n".join(sorted_data).encode("utf-8")
    hasher.update(content)
    return hasher.hexdigest()

def fetch_with_retry(
    url: str,
    max_retries: int = 3,
    timeout: int = 30,
) -> requests.Response:
    """Fetch a URL with exponential backoff retry logic."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            last_exc = e
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                print(f"Retrying {url} in {wait_time}s due to {e}...")
                import time
                time.sleep(wait_time)
        raise DataFetchError(f"Failed to fetch {url} after {max_retries} retries: {last_exc}")

def download_file_to_cache(
    url: str,
    cache_dir: Path,
    filename: str,
) -> Path:
    """Download a file to a cache directory."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / filename

    if cache_path.exists():
        print(f"Using cached file: {cache_path}")
        return cache_path

    print(f"Downloading {url} to {cache_path}...")
    response = fetch_with_retry(url)
    with open(cache_path, "wb") as f:
        f.write(response.content)

    return cache_path

def validate_dataset_structure(
    data: List[Dict[str, Any]],
    required_fields: List[str],
) -> bool:
    """Validate that all records have the required fields."""
    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record:
                raise ValueError(f"Record {i} missing required field: {field}")
    return True

def load_real_dataset(
    dataset_name: str = "databricks/databricks-dolly-15k",
    split: str = "train",
    streaming: bool = False,
) -> List[Dict[str, Any]]:
    """
    Load real data from the Hugging Face datasets library.
    Uses the verified source: 'databricks/databricks-dolly-15k'.

    This function MUST fail loudly if the dataset cannot be fetched.
    NO synthetic fallback is allowed.
    """
    try:
        print(f"Loading real dataset: {dataset_name} (split={split})...")
        if streaming:
            ds = load_dataset(dataset_name, split=split, streaming=True)
            # Convert streaming dataset to list for processing (if memory allows)
            # or process in chunks. For this task, we assume we can stream into a list
            # or process iteratively.
            # To ensure we have a list for the context simulation logic, we convert.
            # If the dataset is huge, this might be an issue, but Dolly-15k is small enough.
            data_list = list(ds)
        else:
            ds = load_dataset(dataset_name, split=split)
            data_list = list(ds)

        # Map fields to expected names if necessary
        # The verified source has 'instruction' and 'response'
        mapped_data = []
        for record in data_list:
            mapped_record = {
                "prompt_text": record.get("instruction", ""),
                "rationale_text": record.get("response", ""),
                "original_record": record
            }
            mapped_data.append(mapped_record)

        if not mapped_data:
            raise DataFetchError("Dataset loaded but returned 0 records.")

        return mapped_data

    except Exception as e:
        raise DataFetchError(f"Failed to load real dataset from {dataset_name}: {e}") from e

"""
Real-data fetching utilities for llmXive.

This module provides strict loaders that fetch REAL data from verified sources
(Hugging Face datasets or direct URLs). No synthetic fallbacks are permitted.
If a real fetch fails, the loader raises an exception immediately.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required for real-data fetching. "
        "Install it via: pip install datasets"
    )

import requests

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_RAW_DIR = _PROJECT_ROOT / "data" / "raw"
_DATA_PROCESSED_DIR = _PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
_DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
_DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_cot_traces() -> List[Dict[str, Any]]:
    """
    Load Chain-of-Thought (CoT) traces from the verified real source.

    Source: Hugging Face dataset 'Qwen/Qwen-AgentWorld' or a specific
    subset if the full dataset is too large. We attempt to load the
    'cot_traces' split if available, or the default split.

    Returns:
        List[Dict[str, Any]]: List of trace dictionaries.

    Raises:
        RuntimeError: If the real data source cannot be fetched or parsed.
        FileNotFoundError: If a local cached file is expected but missing
                           and the remote fetch fails.
    """
    # Try to load from local cache first (if previously downloaded)
    local_cache_path = _DATA_RAW_DIR / "cot_traces.json"
    if local_cache_path.exists():
        try:
            with open(local_cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Corrupted local cache at {local_cache_path}: {e}")

    # Fetch from Hugging Face
    # Note: Using 'Qwen/Qwen-AgentWorld' as the base dataset.
    # We attempt to load the 'train' split or the default.
    # If the dataset structure differs, this will raise an error, which is desired.
    try:
        ds = load_dataset("Qwen/Qwen-AgentWorld", split="train", trust_remote_code=True)
    except Exception as e:
        # Fallback to default split if 'train' fails
        try:
            ds = load_dataset("Qwen/Qwen-AgentWorld", trust_remote_code=True)
            if isinstance(ds, dict):
                # Try to find a split that looks like traces
                for split_name in ds:
                    if "trace" in split_name.lower() or "cot" in split_name.lower():
                        ds = ds[split_name]
                        break
                else:
                    # Just take the first split
                    ds = next(iter(ds.values()))
        except Exception as fallback_err:
            raise RuntimeError(
                f"Failed to load real CoT traces from Hugging Face 'Qwen/Qwen-AgentWorld': {fallback_err}"
            ) from fallback_err

    # Convert to list of dicts
    # Assuming the dataset has columns like 'prompt', 'completion', 'reasoning', etc.
    # We adapt based on actual schema.
    traces = []
    for item in ds:
        # Standardize to a common schema if necessary
        trace_entry = {
            "id": item.get("id", str(len(traces))),
            "prompt": item.get("prompt", ""),
            "completion": item.get("completion", ""),
            "reasoning": item.get("reasoning", item.get("cot", "")),
            "metadata": item.get("metadata", {}),
        }
        traces.append(trace_entry)

    if not traces:
        raise RuntimeError("Loaded dataset is empty. Cannot proceed without real data.")

    # Save to local cache for future runs
    with open(local_cache_path, "w", encoding="utf-8") as f:
        json.dump(traces, f, indent=2, ensure_ascii=False)

    return traces

def load_oracle_source_code() -> Dict[str, Any]:
    """
    Load the Qwen-AgentWorld source code or relevant interaction logic.

    Since the source code is typically a git repository, this function
    attempts to load a pre-downloaded snapshot from `data/raw/source_code.json`
    if available. If not, it raises an error indicating the need to
    manually download the source or use a specific dataset mirror.

    Returns:
        Dict[str, Any]: Parsed source code or interaction logic.

    Raises:
        RuntimeError: If the real source code is not found locally and cannot be fetched.
    """
    local_path = _DATA_RAW_DIR / "source_code.json"
    if local_path.exists():
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise RuntimeError(f"Corrupted local source code cache: {e}")

    # Attempt to fetch from a verified URL or dataset
    # Note: Direct git cloning is not done here to keep it simple.
    # We assume a dataset or URL exists for the source code.
    # If no such dataset exists, we raise a clear error.
    raise RuntimeError(
        "Real source code for Qwen-AgentWorld is not available locally. "
        "Please download the repository, extract the relevant interaction logic, "
        "and save it as JSON to 'data/raw/source_code.json' or implement a "
        "specific fetcher for the verified source URL."
    )

def load_dataset_from_url(url: str, filename: str) -> str:
    """
    Download a dataset file from a verified URL to the data/raw directory.

    Args:
        url (str): The verified URL to download from.
        filename (str): The name to save the file as.

    Returns:
        str: The absolute path to the downloaded file.

    Raises:
        RuntimeError: If the download fails.
    """
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    filepath = _DATA_RAW_DIR / filename
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(response.content)
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download real data from {url}: {e}")

    return str(filepath)
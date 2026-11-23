import json
import logging
import os
import gc
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Tuple

import requests
from huggingface_hub import HfApi, RepositoryNotFoundError

from src.utils.logging import get_logger, log_event, log_error

logger = get_logger(__name__)

# Required metadata variables for analysis branching
REQUIRED_VARS_ERROR_SIGNAL = ['stimulus_type', 'response_correctness']
REQUIRED_VARS_STIMULUS_DRIVEN = ['stimulus_type']

# ----------------------------------------------------------------------
# Dataset discovery helpers (FR-001)
# ----------------------------------------------------------------------
def _prepare_query(query_terms: List[str]) -> str:
    """
    Join a list of query terms into a single search string suitable for
    the HuggingFace and OpenNeuro APIs.

    Args:
        query_terms: List of terms (e.g., ["tactile", "somatosensory", "odd-ball"])

    Returns:
        A space‑separated query string.
    """
    return " ".join(term.strip() for term in query_terms if term.strip())

def fetch_huggingface_datasets(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Search the HuggingFace Hub for datasets whose metadata contains any of the
    supplied query terms.

    This uses the official ``huggingface_hub`` API (which is a dependency of the
    ``datasets`` package) to perform a live search against the public hub.
    The function raises an exception if the hub cannot be reached – the
    pipeline is expected to handle such failures gracefully at a higher
    level (see T004).

    Args:
        query_terms: List of keywords to search for (e.g., ["tactile",
                     "somatosensory", "odd-ball"]).

    Returns:
        A list of dictionaries, each representing a dataset with the keys:
        ``repo_id`` (the HuggingFace repository identifier),
        ``tags`` (list of tags attached to the dataset),
        ``description`` (short description if available).
    """
    query = _prepare_query(query_terms)
    logger.info(f"Fetching datasets from HuggingFace with query: '{query}'")
    api = HfApi()

    try:
        # ``list_datasets`` returns a list of ``DatasetInfo`` objects.
        hf_datasets = api.list_datasets(search=query, sort="downloads")
    except Exception as exc:
        log_error(logger, f"HuggingFace API request failed: {exc}")
        raise

    results: List[Dict[str, Any]] = []
    for ds in hf_datasets:
        # ``DatasetInfo`` objects expose ``id``, ``tags`` and ``cardData``.
        description = ""
        if hasattr(ds, "cardData") and isinstance(ds.cardData, dict):
            description = ds.cardData.get("description", "")
        results.append({
            "repo_id": ds.id,
            "tags": ds.tags,
            "description": description,
        })
    logger.info(f"HuggingFace returned {len(results)} dataset(s).")
    return results

def fetch_openneuro_datasets(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Search the OpenNeuro public API for datasets matching the supplied query
    terms. The OpenNeuro API endpoint ``/api/v1/datasets`` supports a ``search``
    query‑parameter that performs a simple text search over dataset titles and
    descriptions.

    Args:
        query_terms: List of keywords (e.g., ["tactile", "somatosensory",
                     "odd-ball"]).

    Returns:
        A list of dictionaries with keys ``dataset_id`` and ``title``.
    """
    query = _prepare_query(query_terms)
    logger.info(f"Fetching datasets from OpenNeuro with query: '{query}'")
    endpoint = "https://openneuro.org/api/v1/datasets"
    try:
        response = requests.get(endpoint, params={"search": query}, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        log_error(logger, f"OpenNeuro API request failed: {exc}")
        raise

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        log_error(logger, f"Failed to decode OpenNeuro JSON response: {exc}")
        raise

    results: List[Dict[str, Any]] = []
    for entry in data:
        # The OpenNeuro API returns items with at least ``id`` and ``name``.
        dataset_id = entry.get("id") or entry.get("dataset_id")
        title = entry.get("name") or entry.get("title")
        results.append({
            "dataset_id": dataset_id,
            "title": title,
        })
    logger.info(f"OpenNeuro returned {len(results)} dataset(s).")
    return results

def search_datasets(query_terms: List[str]) -> List[Dict[str, Any]]:
    """
    Convenience wrapper that queries both HuggingFace and OpenNeuro, merges the
    results and returns a unified list.

    The function does **not** deduplicate across the two sources – the caller
    can handle that if needed.

    Args:
        query_terms: List of search keywords.

    Returns:
        Combined list of dataset metadata dictionaries from both repositories.
    """
    hf_results = fetch_huggingface_datasets(query_terms)
    on_results = fetch_openneuro_datasets(query_terms)
    # Normalise keys so the combined list has a consistent schema.
    unified: List[Dict[str, Any]] = []
    for r in hf_results:
        unified.append({
            "source": "huggingface",
            "id": r["repo_id"],
            "tags": r["tags"],
            "description": r["description"],
        })
    for r in on_results:
        unified.append({
            "source": "openneuro",
            "id": r["dataset_id"],
            "title": r["title"],
        })
    return unified

# ----------------------------------------------------------------------
# Existing validation utilities (unchanged)
# ----------------------------------------------------------------------
def validate_metadata_variables(metadata: Dict[str, Any], required_vars: List[str]) -> bool:
    """
    Checks if all required variables are present in the dataset metadata.

    Args:
        metadata: The dataset metadata dictionary.
        required_vars: List of variable names that must exist.

    Returns:
        True if all required variables are present, False otherwise.
    """
    if not metadata:
        logger.error("Metadata is empty or None.")
        return False

    missing = []
    for var in required_vars:
        if var not in metadata:
            missing.append(var)

    if missing:
        logger.warning(f"Missing required variables: {missing}")
        return False

    return True

def check_and_report_variables(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks for the presence of 'stimulus_type' and 'response_correctness'
    in the metadata and reports the findings.

    Args:
        metadata: The dataset metadata dictionary.

    Returns:
        A dictionary containing the check results and available variables.
    """
    result = {
        'stimulus_type_present': False,
        'response_correctness_present': False,
        'analysis_mode': None,
        'available_variables': list(metadata.keys()) if metadata else []
    }

    if not metadata:
        log_error(logger, "Metadata is empty or None. Cannot check variables.")
        return result

    # Check for stimulus_type
    if 'stimulus_type' in metadata:
        result['stimulus_type_present'] = True
        logger.info("Variable 'stimulus_type' found in metadata.")
    else:
        logger.warning("Variable 'stimulus_type' NOT found in metadata.")

    # Check for response_correctness
    if 'response_correctness' in metadata:
        result['response_correctness_present'] = True
        logger.info("Variable 'response_correctness' found in metadata.")
    else:
        logger.warning("Variable 'response_correctness' NOT found in metadata.")

    # Determine analysis mode based on FR-011, FR-012
    if result['response_correctness_present']:
        result['analysis_mode'] = 'error_signal'
        log_event(logger, "Analysis mode determined: error_signal (response_correctness present)")
    elif result['stimulus_type_present']:
        result['analysis_mode'] = 'stimulus_driven'
        log_event(logger, "Analysis mode determined: stimulus_driven (only stimulus_type present)", level="WARNING")
    else:
        result['analysis_mode'] = None
        log_error(logger, "Analysis mode cannot be determined: neither stimulus_type nor response_correctness found.")

    return result

def generate_validation_report(metadata: Dict[str, Any], output_path: Path) -> Dict[str, Any]:
    """
    Generates a validation report JSON file based on the variable check.

    Args:
        metadata: The dataset metadata dictionary.
        output_path: Path where the validation report JSON will be saved.

    Returns:
        The validation report dictionary.
    """
    check_result = check_and_report_variables(metadata)

    report = {
        'metadata_keys_found': check_result['available_variables'],
        'stimulus_type_present': check_result['stimulus_type_present'],
        'response_correctness_present': check_result['response_correctness_present'],
        'analysis_mode': check_result['analysis_mode'],
        'status': 'valid' if check_result['analysis_mode'] else 'invalid'
    }

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report generated at: {output_path}")
    except Exception as e:
        log_error(logger, f"Failed to write validation report: {e}")
        raise

    return report

def get_current_memory_usage_gb() -> float:
    """Returns current memory usage in GB."""
    try:
        import resource
        mem_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB.
        import sys
        if sys.platform != 'darwin':
            mem_bytes = mem_bytes * 1024
        return mem_bytes / (1024 ** 3)
    except Exception:
        return 0.0

def stream_dataset_chunks(dataset_id: str, chunk_size: int = 1000) -> Iterator[Dict[str, Any]]:
    """
    Streams dataset chunks from a real source (e.g., HuggingFace).
    Raises an error if the real source is not reachable.
    """
    # Example implementation using the ``datasets`` library with streaming.
    from datasets import load_dataset

    try:
        ds = load_dataset(dataset_id, streaming=True)
    except Exception as exc:
        log_error(logger, f"Failed to open streaming dataset '{dataset_id}': {exc}")
        raise

    buffer: List[Dict[str, Any]] = []
    for i, example in enumerate(ds):
        buffer.append(example)
        if (i + 1) % chunk_size == 0:
            yield {"chunk_index": i // chunk_size, "records": buffer}
            buffer = []
    # Yield any remaining records
    if buffer:
        yield {"chunk_index": i // chunk_size + 1, "records": buffer}

def download_and_process_streaming(dataset_id: str, output_dir: Path) -> None:
    """
    Downloads and processes a dataset in a streaming fashion.
    The function writes processed chunks to ``output_dir`` as JSON Lines files.
    It raises on any network or I/O error – callers should handle these
    exceptions to implement graceful degradation (T004).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for chunk in stream_dataset_chunks(dataset_id):
        chunk_idx = chunk["chunk_index"]
        out_path = output_dir / f"{dataset_id.replace('/', '_')}_chunk_{chunk_idx}.jsonl"
        try:
            with out_path.open("w", encoding="utf-8") as f:
                for record in chunk["records"]:
                    f.write(json.dumps(record) + "\n")
            logger.info(f"Wrote chunk {chunk_idx} to {out_path}")
        except Exception as exc:
            log_error(logger, f"Failed to write chunk {chunk_idx}: {exc}")
            raise

def main():
    """
    Main entry point for the ingest module, typically used for direct testing
    or as a script to run the validation logic.
    """
    logger.info("Starting ingest module main.")
    # Example usage for T001 – discover datasets containing the target terms.
    query_terms = ["tactile", "somatosensory", "odd-ball"]
    try:
        discovered = search_datasets(query_terms)
        logger.info(f"Discovered {len(discovered)} dataset(s) matching query.")
        # For demonstration, we write a short JSON report with the IDs.
        report_path = Path("data/discovered_datasets.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(discovered, f, indent=2)
        logger.info(f"Discovery report written to {report_path}")
    except Exception as exc:
        logger.error(f"Dataset discovery failed: {exc}")

    logger.info("Ingest module main completed.")

if __name__ == "__main__":
    main()

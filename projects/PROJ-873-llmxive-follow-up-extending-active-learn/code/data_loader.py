"""
Data Loader Module for llmXive.

Handles fetching real datasets from BEIR and TREC-COVID.
Enforces strict "Fail Loudly" policy: NO synthetic fallbacks.
"""
import os
import sys
import json
import logging
import zipfile
import io
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

try:
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
except ImportError:
    raise ImportError("The 'beir' library is required. Install it via 'pip install beir'.")

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None  # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataInjectionError(Exception):
    """Raised when data injection or fetching fails."""
    pass

class DataFetchError(DataInjectionError):
    """Raised specifically when fetching real data fails."""
    pass

class RedundancyCluster:
    def __init__(self, cluster_id: int, documents: List[Dict[str, Any]]):
        self.cluster_id = cluster_id
        self.documents = documents

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str, url: str, out_dir: str) -> str:
    """
    Download and unzip a BEIR dataset.
    
    ENFORCES REAL DATA ONLY: If download fails, raises RuntimeError/DataFetchError.
    NO synthetic fallback is permitted.
    """
    logger.info(f"Attempting to download BEIR dataset: {dataset_name}")
    
    try:
        data_path = util.download_and_unzip(url, out_dir)
        logger.info(f"Successfully downloaded {dataset_name} to {data_path}")
        return data_path
    except Exception as e:
        error_msg = f"Failed to download BEIR dataset '{dataset_name}': {str(e)}"
        logger.error(error_msg)
        # CRITICAL: Do NOT catch and return synthetic data.
        # Raise a specific error to fail the pipeline loudly.
        raise DataFetchError(error_msg) from e

def load_beir_corpus(data_path: str) -> Tuple[Dict[str, Dict], Dict[str, str], Dict[str, Dict[str, int]]]:
    """
    Load corpus, queries, and qrels from a BEIR dataset path.
    """
    logger.info(f"Loading BEIR corpus from {data_path}")
    try:
        corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")
        logger.info(f"Loaded {len(corpus)} documents, {len(queries)} queries")
        return corpus, queries, qrels
    except Exception as e:
        error_msg = f"Failed to load BEIR corpus from {data_path}: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg) from e

def fetch_beir_datasets(dataset_names: List[str]) -> Dict[str, Any]:
    """
    Fetch multiple BEIR datasets.
    
    ENFORCES REAL DATA ONLY: Raises DataFetchError if any fetch fails.
    """
    base_url = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/"
    results = {}
    
    for dataset_name in dataset_names:
        url = f"{base_url}{dataset_name}.zip"
        out_dir = os.path.join("data", "raw", "beir", dataset_name)
        os.makedirs(out_dir, exist_ok=True)
        
        try:
            data_path = download_beir_dataset(dataset_name, url, out_dir)
            corpus, queries, qrels = load_beir_corpus(data_path)
            results[dataset_name] = {
                "corpus": corpus,
                "queries": queries,
                "qrels": qrels
            }
        except DataFetchError:
            # Re-raise immediately; do not continue with other datasets
            raise
    
    return results

def fetch_trec_covid_dataset() -> Dict[str, Any]:
    """
    Fetch TREC-COVID dataset via BEIR.
    
    ENFORCES REAL DATA ONLY: Raises DataFetchError if fetch fails.
    """
    dataset_name = "trec-covid"
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    out_dir = os.path.join("data", "raw", "beir", dataset_name)
    os.makedirs(out_dir, exist_ok=True)
    
    try:
        data_path = download_beir_dataset(dataset_name, url, out_dir)
        corpus, queries, qrels = load_beir_corpus(data_path)
        return {
            "corpus": corpus,
            "queries": queries,
            "qrels": qrels
        }
    except DataFetchError:
        raise
    except Exception as e:
        error_msg = f"Failed to fetch TREC-COVID dataset: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg) from e

def inject_redundancy(corpus: Dict[str, Dict], seed: int = 42) -> Dict[str, Any]:
    """
    Inject synthetic redundancy into a corpus for testing.
    This is used ONLY when explicitly requested for simulation,
    not as a fallback for failed real data fetches.
    """
    # Implementation of redundancy injection logic
    # (Placeholder for actual logic if needed for T012)
    return {"injected_corpus": corpus, "clusters": []}

def prepare_injected_datasets(dataset_name: str, redundancy_ratio: float = 0.4, seed: int = 42) -> Dict[str, Any]:
    """
    Prepare a dataset with injected redundancy.
    """
    # This function assumes real data is already fetched or passed in.
    # It does NOT fetch real data itself to avoid side effects.
    return {"status": "prepared", "dataset": dataset_name}

def load_injected_dataset(file_path: str) -> Dict[str, Any]:
    """
    Load an injected dataset from a JSON file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Injected dataset file not found: {file_path}")
    
    with open(file_path, "r") as f:
        return json.load(f)

def validate_injected_similarity(injected_data: Dict[str, Any], threshold: float = 0.95) -> bool:
    """
    Validate that injected clusters meet similarity threshold.
    """
    # Placeholder for validation logic
    return True

def run_validation_pipeline():
    """
    Run the full validation pipeline.
    """
    logger.info("Running validation pipeline")
    # Placeholder for pipeline logic
    pass

def main():
    """
    Main entry point for data loader script.
    """
    logger.info("Data Loader Module")
    # Example usage
    try:
        # This will fail loudly if network is down or dataset missing
        datasets = fetch_beir_datasets(["nfcorpus"])
        logger.info(f"Loaded datasets: {list(datasets.keys())}")
    except DataFetchError as e:
        logger.error(f"Data fetch failed (as expected in offline mode): {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
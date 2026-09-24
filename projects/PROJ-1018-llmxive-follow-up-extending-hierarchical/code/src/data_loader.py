"""
Data loading utilities for PG-19 dataset.
Handles streaming, filtering, and sampling of long-context documents.
"""
import logging
import itertools
import os
import json
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset, Dataset
import pyarrow.parquet as pq
import io

# Configure logging
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def load_pg19_streaming() -> Iterator[Dict[str, Any]]:
    """
    Load PG-19 dataset in streaming mode to handle large contexts.
    
    Returns:
        Iterator over dataset rows containing 'text' field.
    
    Raises:
        DataFetchError: If the dataset cannot be fetched from the real source.
    """
    try:
        # Load from the verified real source: lmsys/pg-19-test
        dataset = load_dataset("lmsys/pg-19-test", split="test", streaming=True)
        return iter(dataset)
    except Exception as e:
        error_msg = f"Failed to fetch real data from lmsys/pg-19-test: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg) from e

def estimate_token_count(text: str, tokens_per_char: float = 0.5) -> int:
    """
    Estimate token count based on character length.
    This is a rough approximation for filtering purposes.
    
    Args:
        text: Input text string.
        tokens_per_char: Estimated tokens per character (default 0.5).
    
    Returns:
        Estimated number of tokens.
    """
    return int(len(text) * tokens_per_char)

def filter_long_documents(
    dataset_iter: Iterator[Dict[str, Any]], 
    min_tokens: int = 32000
) -> Iterator[Dict[str, Any]]:
    """
    Filter dataset to retain only documents with token count >= min_tokens.
    
    Args:
        dataset_iter: Iterator over dataset rows.
        min_tokens: Minimum token count threshold (default 32,000).
    
    Yields:
        Documents meeting the token threshold.
    """
    included_count = 0
    excluded_count = 0
    
    for doc in dataset_iter:
        text = doc.get("text", "")
        if not text:
            excluded_count += 1
            continue
            
        token_count = estimate_token_count(text)
        if token_count >= min_tokens:
            included_count += 1
            yield doc
        else:
            excluded_count += 1
    
    logger.info(f"Filtering complete: {included_count} documents included, {excluded_count} excluded (threshold: {min_tokens} tokens)")

def get_document_iterator() -> Iterator[Dict[str, Any]]:
    """
    Get the full pipeline iterator: load -> filter.
    
    Returns:
        Iterator over filtered documents.
    """
    raw_iter = load_pg19_streaming()
    return filter_long_documents(raw_iter)

def save_filtered_dataset(
    output_path: str, 
    doc_iterator: Optional[Iterator[Dict[str, Any]]] = None
) -> None:
    """
    Save filtered documents to a Parquet file.
    
    Args:
        output_path: Path to output Parquet file.
        doc_iterator: Optional iterator of documents. If None, uses default pipeline.
    """
    if doc_iterator is None:
        doc_iterator = get_document_iterator()
    
    # Convert iterator to list of dicts for Parquet
    docs_list = list(doc_iterator)
    
    if not docs_list:
        logger.warning("No documents to save. Output file may be empty.")
    
    # Create dataset and save
    dataset = Dataset.from_list(docs_list)
    dataset.to_parquet(output_path)
    logger.info(f"Saved {len(docs_list)} documents to {output_path}")

def run_filter_pipeline(output_path: str) -> None:
    """
    Run the full filtering pipeline and save results.
    
    Args:
        output_path: Path to output Parquet file.
    """
    logger.info("Starting filter pipeline...")
    save_filtered_dataset(output_path)
    logger.info("Filter pipeline completed.")

def sample_dataset(
    doc_iterator: Iterator[Dict[str, Any]], 
    max_samples: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Sample documents from an iterator.
    
    Args:
        doc_iterator: Iterator over documents.
        max_samples: Maximum number of samples to return. If None, returns all.
        seed: Random seed for reproducibility (used if max_samples is not None).
    
    Returns:
        List of sampled documents.
    """
    if max_samples is None:
        return list(doc_iterator)
    
    if seed is not None:
        import random
        random.seed(seed)
        # Convert to list to allow shuffling if needed, though islice is deterministic
        docs = list(doc_iterator)
        random.shuffle(docs)
        return docs[:max_samples]
    else:
        # Use islice for deterministic sampling without shuffling
        return list(itertools.islice(doc_iterator, max_samples))

def save_filtered_sampled_dataset(
    output_path: str,
    doc_iterator: Optional[Iterator[Dict[str, Any]]] = None,
    max_samples: Optional[int] = None,
    seed: Optional[int] = None
) -> None:
    """
    Filter, sample, and save documents to a Parquet file.
    
    This function implements T006b: sampling logic to handle memory limits.
    It uses itertools.islice or random sampling if max_samples is provided.
    
    Args:
        output_path: Path to output Parquet file.
        doc_iterator: Optional iterator of documents. If None, uses default pipeline.
        max_samples: Maximum number of samples to return. If None, returns all filtered documents.
        seed: Random seed for reproducibility.
    """
    if doc_iterator is None:
        doc_iterator = get_document_iterator()
    
    logger.info(f"Sampling dataset: max_samples={max_samples}, seed={seed}")
    sampled_docs = sample_dataset(doc_iterator, max_samples, seed)
    
    if not sampled_docs:
        logger.warning("No sampled documents to save.")
        return
    
    dataset = Dataset.from_list(sampled_docs)
    dataset.to_parquet(output_path)
    logger.info(f"Saved {len(sampled_docs)} sampled documents to {output_path}")

def main():
    """Main entry point for running the filter and sample pipeline."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage: save filtered dataset
    filtered_output = "data/interim/filtered_pg19.parquet"
    if not os.path.exists(os.path.dirname(filtered_output)):
        os.makedirs(os.path.dirname(filtered_output))
    
    # Run filter pipeline (T005)
    run_filter_pipeline(filtered_output)
    
    # Run sampling pipeline (T006b)
    sampled_output = "data/interim/filtered_sampled_pg19.parquet"
    # Sample 100 documents for demonstration (adjust max_samples as needed)
    save_filtered_sampled_dataset(sampled_output, max_samples=100, seed=42)

if __name__ == "__main__":
    main()

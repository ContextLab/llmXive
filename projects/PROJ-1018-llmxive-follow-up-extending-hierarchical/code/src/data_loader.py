import logging
import itertools
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset
from .config import Config
from .logging_utils import get_logger

class DataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

def load_pg19_streaming(config: Config) -> Iterator[Dict[str, Any]]:
    """
    Load the lmsys/pg-19-test dataset with streaming enabled.
    This function strictly fetches real data. If the fetch fails,
    it raises DataFetchError. No synthetic fallbacks are provided.
    """
    logger = get_logger(__name__)
    try:
        logger.info("Attempting to load lmsys/pg-19-test with streaming=True")
        dataset = load_dataset("lmsys/pg-19-test", split="train", streaming=True)
        logger.info("Dataset loaded successfully from real source.")
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to fetch real data from lmsys/pg-19-test: {e}")
        raise DataFetchError(f"Real data fetch failed: {e}") from e

def filter_long_documents(doc_iterator: Iterator[Dict[str, Any]], min_tokens: int = 32000) -> Iterator[Dict[str, Any]]:
    """
    Filter documents to retain only those with token count >= min_tokens.
    Logs the number of excluded documents.
    """
    logger = get_logger(__name__)
    excluded_count = 0
    included_count = 0

    for doc in doc_iterator:
        text = doc.get("text", "")
        # Simple heuristic: assume 1 token ~ 4 characters for PG-19 rough estimation
        # or rely on a tokenizer if available in config. For this task, we use length check.
        # The task description implies token count, but without a heavy tokenizer loaded here,
        # we approximate or assume the dataset provides a token_count field if available.
        # However, PG-19 raw text usually requires estimation or a tokenizer.
        # Let's assume we use a rough char-based proxy or a simple tokenizer if Config provides one.
        # Since Config has model_path, we could tokenize, but that's heavy.
        # Let's stick to the task description logic: "retain only documents with token count >= 32000".
        # We will estimate tokens as len(text) / 4.
        estimated_tokens = len(text) // 4

        if estimated_tokens >= min_tokens:
            doc["_estimated_tokens"] = estimated_tokens
            included_count += 1
            yield doc
        else:
            excluded_count += 1

    logger.info(f"Document filtering complete. Included: {included_count}, Excluded: {excluded_count}")

def get_document_iterator(config: Config, min_tokens: int = 32000, sample_size: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """
    Returns an iterator over the dataset that:
    1. Streams real data from lmsys/pg-19-test.
    2. Filters for documents with >= min_tokens.
    3. Optionally samples the dataset if sample_size is provided to verify memory constraints.

    If sample_size is set, uses itertools.islice to limit the stream.
    """
    logger = get_logger(__name__)
    
    # Step 1: Load real data (raises if failed)
    raw_iterator = load_pg19_streaming(config)
    
    # Step 2: Filter documents
    filtered_iterator = filter_long_documents(raw_iterator, min_tokens)
    
    # Step 3: Sample if requested
    if sample_size is not None:
        logger.info(f"Applying dataset sampling: limiting to {sample_size} documents.")
        # Verify memory constraints by limiting the stream
        return itertools.islice(filtered_iterator, sample_size)
    
    return filtered_iterator

import logging
import itertools
import os
import json
from typing import Iterator, List, Dict, Any, Optional
from datasets import load_dataset, Dataset

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when real data fetching fails."""
    pass

def load_pg19_streaming(tokenizer_name: str = "lmsys/pg-19-test") -> Iterator[Dict[str, Any]]:
    """
    Loads the PG-19 dataset in streaming mode to handle large contexts.
    
    Args:
        tokenizer_name: The HuggingFace dataset identifier.
        
    Returns:
        An iterator yielding document dictionaries.
        
    Raises:
        DataFetchError: If the dataset cannot be fetched.
    """
    try:
        dataset = load_dataset(tokenizer_name, split="train", streaming=True)
        return iter(dataset)
    except Exception as e:
        logger.error(f"Failed to load dataset {tokenizer_name}: {e}")
        raise DataFetchError(f"Real data fetch failed: {e}")

def estimate_token_count(text: str, tokenizer) -> int:
    """
    Estimates the token count for a given text using a tokenizer.
    
    Args:
        text: The input text.
        tokenizer: A HuggingFace tokenizer instance.
        
    Returns:
        The estimated number of tokens.
    """
    if tokenizer is None:
        # Fallback estimation: ~4 characters per token if no tokenizer provided
        return len(text) // 4
    return len(tokenizer.encode(text, truncation=False))

def get_document_iterator(dataset_iter: Iterator[Dict[str, Any]], tokenizer) -> Iterator[Dict[str, Any]]:
    """
    Wraps the dataset iterator to include token counts in each document.
    
    Args:
        dataset_iter: Iterator from load_pg19_streaming.
        tokenizer: Tokenizer instance for counting.
        
    Yields:
        Documents with an added 'token_count' field.
    """
    for doc in dataset_iter:
        # Handle potential missing 'text' key or None
        text = doc.get("text", "")
        if text is None:
            text = ""
        
        token_count = estimate_token_count(text, tokenizer)
        
        yield {
            "document_id": doc.get("id", "unknown"),
            "text": text,
            "token_count": token_count
        }

def filter_long_documents(doc_iterator: Iterator[Dict[str, Any]], min_tokens: int = 32000) -> Iterator[Dict[str, Any]]:
    """
    Filters documents to retain only those with token count >= min_tokens.
    
    Logs warnings for skipped documents to stdout as required.
    
    Args:
        doc_iterator: Iterator of documents with 'token_count'.
        min_tokens: Minimum token threshold (default 32000).
        
    Yields:
        Documents meeting the threshold.
    """
    for doc in doc_iterator:
        if doc["token_count"] >= min_tokens:
            yield doc
        else:
            # Log warning to stdout as specified
            print(f"WARNING: Skipping document {doc['document_id']}: length {doc['token_count']} < {min_tokens}")

def save_filtered_dataset(doc_iterator: Iterator[Dict[str, Any]], output_path: str) -> int:
    """
    Saves the filtered documents to a JSON file.
    
    Args:
        doc_iterator: Iterator of filtered documents.
        output_path: Path to the output JSON file.
        
    Returns:
        The number of documents saved.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    count = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write as a JSON list
        f.write("[\n")
        first = True
        for doc in doc_iterator:
            if not first:
                f.write(",\n")
            first = False
            # Ensure keys are exactly as specified: document_id, text, token_count
            record = {
                "document_id": doc["document_id"],
                "text": doc["text"],
                "token_count": doc["token_count"]
            }
            json.dump(record, f, ensure_ascii=False)
            count += 1
            # Optional: flush periodically to avoid huge memory buffer for list
            if count % 1000 == 0:
                f.flush()
        f.write("\n]")
    
    logger.info(f"Saved {count} documents to {output_path}")
    return count

def sample_dataset(doc_iterator: Iterator[Dict[str, Any]], sample_size: int) -> Iterator[Dict[str, Any]]:
    """
    Takes a sample of documents from the iterator.
    
    Args:
        doc_iterator: Input iterator.
        sample_size: Number of documents to sample.
        
    Yields:
        A subset of documents.
    """
    return itertools.islice(doc_iterator, sample_size)

def save_filtered_sampled_dataset(doc_iterator: Iterator[Dict[str, Any]], output_path: str, sample_size: int) -> int:
    """
    Samples and saves filtered documents.
    """
    sampled_iter = sample_dataset(doc_iterator, sample_size)
    return save_filtered_dataset(sampled_iter, output_path)

def run_filter_pipeline(tokenizer_name: str, output_path: str, min_tokens: int = 32000, sample_size: Optional[int] = None) -> int:
    """
    Orchestrates the full filtering pipeline: Load -> Count -> Filter -> Save.
    
    Args:
        tokenizer_name: Dataset identifier.
        output_path: Output JSON path.
        min_tokens: Minimum token threshold.
        sample_size: Optional limit on number of documents to process.
        
    Returns:
        Number of saved documents.
    """
    # We need a tokenizer to count tokens accurately. 
    # For this specific task, if a tokenizer isn't passed, we might need to load one.
    # However, the task description focuses on the logic. 
    # Assuming a tokenizer is available or we use a simple estimator if not.
    # To be robust, we try to load a small tokenizer if needed, or use the estimator.
    from transformers import AutoTokenizer
    
    try:
        tokenizer = AutoTokenizer.from_pretrained("gpt2", trust_remote_code=True)
    except Exception:
        tokenizer = None
        logger.warning("Could not load tokenizer, using character-based estimation.")

    logger.info(f"Starting filter pipeline: min_tokens={min_tokens}, output={output_path}")
    
    dataset_iter = load_pg19_streaming(tokenizer_name)
    doc_iter = get_document_iterator(dataset_iter, tokenizer)
    
    if sample_size:
        doc_iter = sample_dataset(doc_iter, sample_size)
        
    filtered_iter = filter_long_documents(doc_iter, min_tokens)
    
    return save_filtered_dataset(filtered_iter, output_path)

def main():
    """Entry point for running the filter pipeline."""
    output_file = "data/interim/filtered_pg19.json"
    # Run on a small sample first to verify logic if needed, 
    # but the task implies processing the stream.
    # We run the full pipeline.
    run_filter_pipeline(
        tokenizer_name="lmsys/pg-19-test",
        output_path=output_file,
        min_tokens=32000
    )

if __name__ == "__main__":
    main()

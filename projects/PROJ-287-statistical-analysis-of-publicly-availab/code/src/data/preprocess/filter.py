import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.data.preprocess.tokenizer import TokenizationResult, load_preprocessed_data
from src.utils.logging import get_logger
from src.utils.config import ensure_directories

# Configure logger for this module
logger = get_logger(__name__)


def filter_by_token_count(
    tokenized_results: List[TokenizationResult],
    min_tokens: int = 20
) -> Tuple[List[TokenizationResult], int]:
    """
    Filter a list of tokenized results, excluding records with fewer than min_tokens.
    
    Args:
        tokenized_results: List of TokenizationResult objects from the tokenizer.
        min_tokens: Minimum number of tokens required to keep a record (default 20).
        
    Returns:
        A tuple containing:
            - List of TokenizationResult objects that passed the filter.
            - Count of records excluded due to low token count.
    """
    if not tokenized_results:
        logger.warning("No tokenized results provided for filtering.")
        return [], 0

    filtered_results = []
    excluded_count = 0

    for result in tokenized_results:
        token_count = len(result.tokens)
        if token_count >= min_tokens:
            filtered_results.append(result)
        else:
            excluded_count += 1
            logger.debug(
                f"Excluded record {result.id} (or similar identifier): "
                f"token count {token_count} < {min_tokens}"
            )

    logger.info(
        f"Filtering complete: kept {len(filtered_results)} records, "
        f"excluded {excluded_count} records (< {min_tokens} tokens)."
    )
    
    return filtered_results, excluded_count


def process_and_filter(
    input_path: str,
    output_path: str,
    min_tokens: int = 20
) -> Dict[str, Any]:
    """
    Load preprocessed data, filter by token count, and save the results.
    
    This function acts as the main entry point for the filtering stage of the pipeline.
    It ensures the output directory exists, loads data from the specified input path,
    applies the token count filter, and saves the filtered results to the output path.
    
    Args:
        input_path: Path to the input JSONL file containing tokenized results.
        output_path: Path where the filtered JSONL file will be saved.
        min_tokens: Minimum token threshold for inclusion (default 20).
        
    Returns:
        Dictionary containing processing statistics:
            - total_input: Number of records in input.
            - kept: Number of records kept.
            - excluded: Number of records excluded.
            - output_path: Path to the saved file.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Ensure output directory exists
    ensure_directories([output_file.parent])
    
    logger.info(f"Loading tokenized data from {input_file}")
    tokenized_results = load_preprocessed_data(input_file)
    
    logger.info(f"Loaded {len(tokenized_results)} records. Applying token filter (>= {min_tokens})...")
    filtered_results, excluded_count = filter_by_token_count(tokenized_results, min_tokens)
    
    logger.info(f"Saving {len(filtered_results)} filtered records to {output_file}")
    
    # Reuse the save function from tokenizer module
    from src.data.preprocess.tokenizer import save_tokenized_results
    save_tokenized_results(filtered_results, output_file)
    
    stats = {
        "total_input": len(tokenized_results),
        "kept": len(filtered_results),
        "excluded": excluded_count,
        "output_path": str(output_file),
        "min_tokens": min_tokens
    }
    
    return stats


def main():
    """
    Command-line entry point for the filtering script.
    
    Expects environment variables or hardcoded defaults for input/output paths.
    For this implementation, we assume the pipeline orchestrator sets the paths,
    but we provide defaults for standalone testing if needed.
    """
    # Default paths relative to project root
    # In a real pipeline, these might be passed via arguments or env vars
    default_input = "data/raw/tokenized_abstracts.jsonl"
    default_output = "data/processed/filtered_abstracts.jsonl"
    
    # Check if input exists; if not, log a clear error
    if not os.path.exists(default_input):
        logger.error(f"Input file {default_input} does not exist. "
                     "Please ensure the tokenizer stage (T014) has run successfully.")
        return 1
    
    stats = process_and_filter(default_input, default_output)
    
    logger.info("Filtering pipeline completed successfully.")
    logger.info(f"Stats: {stats}")
    
    return 0


if __name__ == "__main__":
    exit(main())

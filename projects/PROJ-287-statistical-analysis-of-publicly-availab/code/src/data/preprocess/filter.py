"""
Filter module for preprocessing abstracts.
Excludes records with fewer than 20 tokens and logs exclusion counts.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from src.data.preprocess.tokenizer import TokenizationResult, load_preprocessed_data
from src.utils.logging import get_logger

# Minimum token count threshold as per requirements
MIN_TOKEN_THRESHOLD = 20

def filter_by_token_count(tokenization_results: List[TokenizationResult]) -> Tuple[List[TokenizationResult], int]:
    """
    Filter a list of tokenization results, keeping only those with >= MIN_TOKEN_THRESHOLD tokens.

    Args:
        tokenization_results: List of TokenizationResult objects from the tokenizer.

    Returns:
        Tuple containing:
            - List of filtered TokenizationResult objects (kept records)
            - Count of excluded records
    """
    filtered_results = []
    excluded_count = 0

    for result in tokenization_results:
        if result.token_count >= MIN_TOKEN_THRESHOLD:
            filtered_results.append(result)
        else:
            excluded_count += 1

    return filtered_results, excluded_count

def process_and_filter(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Load preprocessed data, filter by token count, and save the results.

    This function:
    1. Loads tokenized data from the input path (JSONL format).
    2. Filters out records with fewer than 20 tokens.
    3. Logs the number of excluded records.
    4. Saves the filtered results to the output path.

    Args:
        input_path: Path to the input JSONL file containing tokenized results.
        output_path: Path to the output JSONL file for filtered results.

    Returns:
        Dictionary containing processing statistics:
            - total_loaded: Total number of records loaded
            - total_kept: Number of records kept after filtering
            - total_excluded: Number of records excluded (< 20 tokens)
            - exclusion_rate: Percentage of excluded records
    """
    logger = get_logger(__name__)
    
    # Load preprocessed data
    logger.info(f"Loading tokenized data from {input_path}")
    tokenization_results = load_preprocessed_data(input_path)
    
    if not tokenization_results:
        logger.warning(f"No data found in {input_path}")
        return {
            "total_loaded": 0,
            "total_kept": 0,
            "total_excluded": 0,
            "exclusion_rate": 0.0
        }

    total_loaded = len(tokenization_results)
    
    # Filter by token count
    logger.info(f"Filtering records (threshold: {MIN_TOKEN_THRESHOLD} tokens)...")
    filtered_results, excluded_count = filter_by_token_count(tokenization_results)
    
    total_kept = len(filtered_results)
    total_excluded = excluded_count
    exclusion_rate = (total_excluded / total_loaded * 100) if total_loaded > 0 else 0.0

    # Log exclusion counts
    logger.info(f"Filtering complete:")
    logger.info(f"  - Total loaded: {total_loaded}")
    logger.info(f"  - Total kept: {total_kept}")
    logger.info(f"  - Total excluded (< {MIN_TOKEN_THRESHOLD} tokens): {total_excluded}")
    logger.info(f"  - Exclusion rate: {exclusion_rate:.2f}%")

    # Save filtered results
    logger.info(f"Saving filtered data to {output_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write filtered results to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in filtered_results:
            # Convert TokenizationResult to dictionary for JSON serialization
            record_dict = {
                "id": result.id,
                "source": result.source,
                "original_text": result.original_text,
                "tokens": result.tokens,
                "token_count": result.token_count,
                "window": result.window,
                "year": result.year
            }
            f.write(f"{record_dict}\n")

    return {
        "total_loaded": total_loaded,
        "total_kept": total_kept,
        "total_excluded": total_excluded,
        "exclusion_rate": exclusion_rate
    }

def main():
    """
    Main entry point for the filter module.
    Reads from data/raw/tokenized_abstracts.jsonl and writes to data/processed/filtered_abstracts.jsonl
    """
    logger = get_logger(__name__)
    logger.info("Starting filter module...")

    # Define input and output paths
    base_dir = Path(__file__).parent.parent.parent.parent
    input_path = base_dir / "data" / "raw" / "tokenized_abstracts.jsonl"
    output_path = base_dir / "data" / "processed" / "filtered_abstracts.jsonl"

    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the tokenizer module first to generate tokenized_abstracts.jsonl")
        return

    # Process and filter
    stats = process_and_filter(str(input_path), str(output_path))

    logger.info("Filter module completed successfully.")
    logger.info(f"Final statistics: {stats}")

if __name__ == "__main__":
    main()

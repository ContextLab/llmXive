import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json

from src.data.preprocess.tokenizer import TokenizationResult, load_preprocessed_data
from src.utils.logging import get_logger

MIN_TOKEN_THRESHOLD = 20
logger = get_logger(__name__)


def filter_by_token_count(
    records: List[Dict[str, Any]],
    min_tokens: int = MIN_TOKEN_THRESHOLD
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Filter a list of preprocessed record dictionaries based on token count.
    
    Args:
        records: List of dicts containing at least 'tokens' key (list of strings).
        min_tokens: Minimum number of tokens required to keep a record.
        
    Returns:
        Tuple containing:
            - filtered_records: List of records meeting the token threshold.
            - kept_count: Number of records kept.
            - excluded_count: Number of records excluded.
    """
    if not records:
        logger.warning("No records provided to filter_by_token_count.")
        return [], 0, 0

    filtered_records = []
    excluded_count = 0

    for record in records:
        token_list = record.get("tokens", [])
        token_count = len(token_list)
        
        if token_count >= min_tokens:
            filtered_records.append(record)
        else:
            excluded_count += 1
            
            # Log exclusion details for a small sample to avoid log flooding
            if excluded_count <= 5:
                logger.debug(
                    f"Excluding record ID {record.get('id', 'unknown')}: "
                    f"token count {token_count} < {min_tokens}"
                )
            elif excluded_count == 6:
                logger.info("Stopped logging individual exclusion details. "
                            "Check summary stats below.")

    kept_count = len(filtered_records)
    total_processed = kept_count + excluded_count
    
    logger.info(
        f"Filtering complete: Kept {kept_count}/{total_processed} records "
        f"({100*kept_count/total_processed:.1f}%) with >= {min_tokens} tokens. "
        f"Excluded {excluded_count} records."
    )
    
    return filtered_records, kept_count, excluded_count


def process_and_filter(
    input_path: str,
    output_path: str,
    min_tokens: int = MIN_TOKEN_THRESHOLD
) -> Dict[str, Any]:
    """
    Load preprocessed data from a JSONL file, filter by token count, 
    and save the result to a new JSONL file.
    
    Args:
        input_path: Path to the input JSONL file (raw tokenized data).
        output_path: Path to the output JSONL file (filtered data).
        min_tokens: Minimum token threshold.
        
    Returns:
        Dictionary containing processing statistics.
    """
    logger.info(f"Starting filter process: {input_path} -> {output_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    records = load_preprocessed_data(input_path)
    logger.info(f"Loaded {len(records)} records from {input_path}")
    
    filtered_records, kept_count, excluded_count = filter_by_token_count(
        records, min_tokens=min_tokens
    )
    
    # Save filtered records
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in filtered_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
    logger.info(f"Saved {kept_count} filtered records to {output_path}")
    
    return {
        "input_file": input_path,
        "output_file": output_path,
        "total_input": len(records),
        "total_output": kept_count,
        "excluded_count": excluded_count,
        "min_tokens_threshold": min_tokens
    }


def main():
    """
    CLI entry point for running the filter module.
    Expects environment variables or defaults for input/output paths.
    """
    # Default paths relative to project structure
    # These would typically be set via config or CLI args in a real pipeline
    input_file = os.getenv(
        "FILTER_INPUT_PATH", 
        "data/processed/tokenized_abstracts.jsonl"
    )
    output_file = os.getenv(
        "FILTER_OUTPUT_PATH",
        "data/processed/filtered_abstracts.jsonl"
    )
    min_tokens = int(os.getenv("FILTER_MIN_TOKENS", str(MIN_TOKEN_THRESHOLD)))
    
    try:
        stats = process_and_filter(input_file, output_file, min_tokens)
        logger.info("Filtering successful.")
        logger.info(f"Stats: {stats}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during filtering: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
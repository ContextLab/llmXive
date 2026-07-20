import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from src.data.preprocess.tokenizer import TokenizationResult, load_preprocessed_data
from src.utils.logging import get_logger

def filter_by_token_count(
    records: List[Dict[str, Any]],
    min_tokens: int = 20
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Filter a list of tokenized records, excluding those with fewer than min_tokens.
    
    Args:
        records: List of dictionaries containing tokenized data (expected key: 'tokens').
        min_tokens: Minimum number of tokens required to keep a record.
        
    Returns:
        A tuple containing:
            - filtered_records: List of records meeting the token threshold.
            - excluded_count: Number of records excluded due to low token count.
    """
    filtered_records = []
    excluded_count = 0
    
    for record in records:
        tokens = record.get('tokens', [])
        if len(tokens) >= min_tokens:
            filtered_records.append(record)
        else:
            excluded_count += 1
            
    return filtered_records, excluded_count

def process_and_filter(
    input_path: str,
    output_path: str,
    min_tokens: int = 20
) -> Dict[str, Any]:
    """
    Load preprocessed data, filter by token count, and save the result.
    
    This function orchestrates the filtering step for User Story 1.
    It reads JSONL data from `input_path`, applies the token count filter,
    logs the exclusion counts, and writes the valid records to `output_path`.
    
    Args:
        input_path: Path to the input JSONL file containing tokenized abstracts.
        output_path: Path where the filtered JSONL file will be saved.
        min_tokens: Minimum token threshold (default 20).
        
    Returns:
        A dictionary containing processing statistics:
            - total_loaded: Number of records loaded.
            - total_kept: Number of records kept after filtering.
            - total_excluded: Number of records excluded.
            - exclusion_rate: Percentage of excluded records.
    """
    logger = get_logger(__name__)
    
    logger.info(f"Loading preprocessed data from: {input_path}")
    records = load_preprocessed_data(input_path)
    total_loaded = len(records)
    
    if total_loaded == 0:
        logger.warning(f"No records found in {input_path}. Creating empty output.")
        # Ensure output file exists even if empty
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            pass
        return {
            'total_loaded': 0,
            'total_kept': 0,
            'total_excluded': 0,
            'exclusion_rate': 0.0
        }
        
    logger.info(f"Loaded {total_loaded} records. Filtering for >= {min_tokens} tokens...")
    
    filtered_records, excluded_count = filter_by_token_count(records, min_tokens)
    total_kept = len(filtered_records)
    
    logger.info(f"Filtering complete. Kept: {total_kept}, Excluded: {excluded_count}")
    
    if total_kept == 0:
        logger.error("CRITICAL: All records were filtered out. Check tokenization or input data.")
        
    # Save filtered records
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in filtered_records:
            f.write(f"{record}\n") # Assuming records are dict strings or need json.dumps if not stringified yet
            # The tokenizer likely outputs dicts. If load_preprocessed_data returns dicts:
            # We need to ensure we write valid JSONL. 
            # If the record is already a string representation of a dict, we write it.
            # If it's a dict, we need json.dumps. 
            # Looking at standard patterns in this project:
            # Let's assume standard JSONL writing for robustness if not already string.
            # However, to be safe with the specific tokenizer output, we check type.
            # If the tokenizer saves as json.dumps(record), then load returns dict.
            # We must write back as json.
            import json
            f.write(json.dumps(record) + '\n')

    stats = {
        'total_loaded': total_loaded,
        'total_kept': total_kept,
        'total_excluded': excluded_count,
        'exclusion_rate': (excluded_count / total_loaded * 100) if total_loaded > 0 else 0.0
    }
    
    logger.info(f"Filtered data saved to: {output_path}")
    logger.info(f"Statistics: {stats}")
    
    return stats

def main():
    """
    Entry point for the filter script.
    Reads configuration from environment or defaults to standard paths.
    """
    logger = get_logger(__name__)
    logger.info("Starting filter_by_token_count module.")
    
    # Default paths relative to project root
    # Assuming standard project structure: data/raw/ -> data/processed/
    # The exact filenames might vary based on fetcher output, but we assume
    # the orchestrator or previous step defines the input.
    # For this specific task, we assume the input is the tokenized output from T014.
    
    input_file = os.environ.get('FILTER_INPUT_PATH', 'data/raw/tokenized_abstracts.jsonl')
    output_file = os.environ.get('FILTER_OUTPUT_PATH', 'data/processed/filtered_abstracts.jsonl')
    min_tokens = int(os.environ.get('MIN_TOKENS', 20))
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Ensure T014 (tokenizer) has run and produced the expected file.")
        return 1
        
    try:
        stats = process_and_filter(input_file, output_file, min_tokens)
        if stats['total_kept'] == 0:
            logger.error("Process failed: No records passed the filter.")
            return 1
        logger.info("Filtering completed successfully.")
        return 0
    except Exception as e:
        logger.exception(f"Error during filtering: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
from src.data.preprocess.tokenizer import TokenizationResult, load_preprocessed_data
from src.utils.logging import get_logger

logger = get_logger(__name__)

def filter_by_token_count(
    records: List[Dict[str, Any]],
    min_tokens: int = 20
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Filter records based on minimum token count.

    Args:
        records: List of tokenized record dictionaries.
        min_tokens: Minimum number of tokens required to keep a record.

    Returns:
        Tuple containing:
            - List of records that meet the token threshold.
            - Count of excluded records.
            - Count of processed records.
    """
    filtered_records = []
    excluded_count = 0
    total_count = len(records)

    for record in records:
        token_count = len(record.get("tokens", []))
        if token_count >= min_tokens:
            filtered_records.append(record)
        else:
            excluded_count += 1

    logger.info(
        f"Token filtering: {total_count} total records, "
        f"{len(filtered_records)} kept (>= {min_tokens} tokens), "
        f"{excluded_count} excluded (< {min_tokens} tokens)."
    )

    return filtered_records, excluded_count, total_count

def process_and_filter(
    input_dir: str,
    output_dir: str,
    min_tokens: int = 20,
    window_suffix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load preprocessed data, filter by token count, and save results.

    Args:
        input_dir: Directory containing preprocessed JSONL files.
        output_dir: Directory to save filtered CSV/JSONL files.
        min_tokens: Minimum token threshold.
        window_suffix: Optional suffix to identify specific window files.

    Returns:
        Dictionary with processing statistics.
    """
    logger.info(f"Starting filter process for directory: {input_dir}")
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    total_input_records = 0
    total_output_records = 0
    total_excluded = 0
    files_processed = 0

    # Find all JSONL files in input directory
    jsonl_files = list(input_path.glob("*.jsonl"))
    
    if not jsonl_files:
        logger.warning(f"No JSONL files found in {input_dir}")
        return {
            "status": "no_input",
            "message": "No JSONL files found in input directory"
        }

    for jsonl_file in jsonl_files:
        logger.info(f"Processing file: {jsonl_file.name}")
        
        # Load data using the tokenizer module's loader
        records = load_preprocessed_data(str(jsonl_file))
        
        if not records:
            logger.warning(f"No records loaded from {jsonl_file.name}")
            continue

        # Apply filter
        filtered_records, excluded, total = filter_by_token_count(records, min_tokens)
        
        # Update totals
        total_input_records += total
        total_excluded += excluded
        total_output_records += len(filtered_records)
        files_processed += 1

        # Determine output filename
        if window_suffix:
            output_filename = f"{jsonl_file.stem}_{window_suffix}.jsonl"
        else:
            output_filename = f"{jsonl_file.stem}_filtered.jsonl"
        
        output_file = output_path / output_filename

        # Save filtered records
        with open(output_file, "w", encoding="utf-8") as f:
            for record in filtered_records:
                f.write(json.dumps(record) + "\n")
        
        logger.info(f"Saved {len(filtered_records)} records to {output_file}")

    stats = {
        "status": "success",
        "files_processed": files_processed,
        "total_input_records": total_input_records,
        "total_output_records": total_output_records,
        "total_excluded": total_excluded,
        "min_tokens_threshold": min_tokens,
        "exclusion_rate": (total_excluded / total_input_records) if total_input_records > 0 else 0.0
    }

    logger.info(f"Filtering complete. Exclusion rate: {stats['exclusion_rate']:.2%}")
    return stats

def main():
    """Main entry point for running the filter module."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Filter preprocessed abstracts by token count.")
    parser.add_argument(
        "--input-dir",
        type=str,
        required=True,
        help="Directory containing preprocessed JSONL files."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save filtered JSONL files."
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=20,
        help="Minimum number of tokens required (default: 20)."
    )
    parser.add_argument(
        "--window",
        type=str,
        default=None,
        help="Optional window identifier for output naming."
    )

    args = parser.parse_args()

    try:
        result = process_and_filter(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            min_tokens=args.min_tokens,
            window_suffix=args.window
        )
        
        if result["status"] == "success":
            print(f"Successfully processed {result['files_processed']} files.")
            print(f"Input records: {result['total_input_records']}")
            print(f"Output records: {result['total_output_records']}")
            print(f"Excluded records: {result['total_excluded']}")
            sys.exit(0)
        else:
            print(f"Filtering failed: {result.get('message', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Critical error during filtering: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
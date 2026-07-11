"""
Script to load the DAG SFT dataset and optionally save it to local storage.

Usage:
    python -m code.scripts.load_dataset --split train --save-to data/processed/dag_sft.parquet
"""

import argparse
import logging
import sys
from pathlib import Path
import json

# Ensure code/src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.data_loader import (
    load_dag_sft_dataset,
    get_dataset_info,
    iterate_dataset_examples,
    save_dataset_to_parquet
)

def main():
    parser = argparse.ArgumentParser(
        description="Load DAG SFT dataset from HuggingFace and optionally save to local storage."
    )
    parser.add_argument(
        "--split",
        type=str,
        default=None,
        help="Dataset split to load (e.g., 'train', 'test'). If None, loads all."
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Use streaming mode instead of downloading the full dataset."
    )
    parser.add_argument(
        "--max-preview",
        type=int,
        default=3,
        help="Number of examples to preview in the console."
    )
    parser.add_argument(
        "--save-to",
        type=str,
        default=None,
        help="Path to save the dataset as a Parquet file (e.g., data/processed/dag_sft.parquet)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Loading dataset '{'aaabiao/DAG_sft'}'...")
        dataset = load_dag_sft_dataset(
            split=args.split,
            streaming=args.streaming
        )
        
        info = get_dataset_info(dataset)
        logger.info(f"Dataset loaded. Info: {json.dumps(info, indent=2, default=str)}")
        
        # Preview examples
        logger.info(f"Previewing {args.max_preview} examples:")
        count = 0
        for example in iterate_dataset_examples(dataset, max_examples=args.max_preview):
            print(f"\n--- Example {count + 1} ---")
            # Truncate long strings for console readability
            safe_example = {
                k: (v[:100] + "..." if isinstance(v, str) and len(v) > 100 else v)
                for k, v in example.items()
            }
            print(json.dumps(safe_example, indent=2, default=str))
            count += 1
        
        # Save to Parquet if requested
        if args.save_to:
            output_path = Path(args.save_to)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to non-streaming if streaming was used
            if args.streaming:
                logger.warning("Converting streaming dataset to in-memory for Parquet save...")
                dataset = list(iterate_dataset_examples(dataset))
                from datasets import Dataset
                dataset = Dataset.from_list(dataset)
            
            save_path = save_dataset_to_parquet(dataset, str(output_path), overwrite=True)
            logger.info(f"Dataset successfully saved to {save_path}")
            
            # Verify integrity
            if not save_path.exists():
                raise FileNotFoundError(f"Save verification failed: {save_path} does not exist.")
                
        logger.info("Task completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to load or process dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

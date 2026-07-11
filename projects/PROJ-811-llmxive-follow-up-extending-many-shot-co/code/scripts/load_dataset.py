import argparse
import logging
import sys
from pathlib import Path
import json

# Adjust import path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.data_loader import (
    load_dag_sft_dataset,
    get_dataset_info,
    save_dataset_to_parquet
)
from code.src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Load and cache the DAG_SFT dataset.")
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Dataset split to load (e.g., train, test)"
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Load dataset in streaming mode (does not download fully)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to save the processed parquet file"
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Limit the number of examples to process (for testing)"
    )
    
    args = parser.parse_args()

    config = Config.get_config()
    
    try:
        logger.info(f"Loading dataset 'aaabiao/DAG_sft' (split={args.split})...")
        dataset = load_dag_sft_dataset(
            split=args.split,
            streaming=args.streaming,
            cache_dir=config.get("data.cache_dir")
        )

        if args.streaming:
            logger.warning("Streaming mode enabled. Cannot calculate total size or save to Parquet directly without materializing.")
            if args.max_examples:
                logger.info(f"Previewing first {args.max_examples} examples in streaming mode...")
                from code.src.data_loader import iterate_dataset_examples
                for i, example in enumerate(iterate_dataset_examples(dataset, max_examples=args.max_examples)):
                    if i == 0:
                        logger.info(f"Example structure: {list(example.keys())}")
                    # Just iterating to verify connectivity
            return

        # Materialize and save if not streaming
        info = get_dataset_info(dataset)
        logger.info(f"Dataset loaded. Info: {info}")

        output_path = Path(args.output_dir)
        output_file = save_dataset_to_parquet(
            dataset, 
            str(output_path), 
            split=args.split
        )

        logger.info(f"Dataset successfully saved to: {output_file}")
        
        # Verify
        if output_file.exists():
            logger.info(f"Verification: File exists at {output_file}, size: {output_file.stat().st_size} bytes")
        else:
            logger.error("Verification failed: Output file does not exist.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to load or process dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

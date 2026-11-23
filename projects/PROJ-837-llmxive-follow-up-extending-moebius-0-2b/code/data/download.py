"""
Wrapper script to download datasets as invoked by the run-book.
Delegates to the actual implementation in data.loader.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.loader import fetch_places365_subset
from utils.logger import get_logger

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Download datasets for the project.")
    parser.add_argument("--dataset", type=str, default="places365", help="Dataset name")
    parser.add_argument("--limit", type=int, default=100, help="Limit number of samples to download")
    args = parser.parse_args()

    if args.dataset == "places365":
        logger.info(f"Downloading Places365 subset (limit={args.limit})...")
        try:
            dataset = fetch_places365_subset(limit=args.limit)
            logger.info(f"Successfully downloaded {len(dataset)} samples.")
        except Exception as e:
            logger.error(f"Failed to download dataset: {e}")
            sys.exit(1)
    else:
        logger.error(f"Unknown dataset: {args.dataset}")
        sys.exit(1)

if __name__ == "__main__":
    main()

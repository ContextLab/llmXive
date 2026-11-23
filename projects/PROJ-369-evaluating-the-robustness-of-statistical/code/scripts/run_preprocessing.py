import os
import sys
import json
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).resolve().parent
src_path = code_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.data.preprocessing import preprocess_dataset
from src.utils.logging import setup_logger, log_info, log_error
from src.utils.config import get_path

def main():
    logger = setup_logger()
    log_info("Starting Preprocessing Stage...")

    try:
        # Define paths
        data_raw = get_path("data_raw")
        data_processed = get_path("data_processed")
        data_processed.mkdir(parents=True, exist_ok=True)

        # Process all datasets in data/raw
        # Assuming manifest exists or we iterate files
        manifest_path = data_raw / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        else:
            log_error("Manifest not found. Please run ingestion first.")
            sys.exit(1)

        for dataset_id, dataset_info in manifest.get("datasets", {}).items():
            input_file = Path(dataset_info["file_path"])
            if not input_file.exists():
                log_warning(f"Input file not found: {input_file}")
                continue

            log_info(f"Processing dataset: {dataset_id}")
            output_file = data_processed / f"processed_{dataset_id}.csv"

            # Call preprocessing function
            # Note: This assumes preprocess_dataset handles file I/O or we pass paths
            # For this script, we assume preprocess_dataset takes paths and writes output
            preprocess_dataset(input_file, output_file, dataset_id)

        log_info("Preprocessing stage completed successfully.")

    except Exception as e:
        log_error(f"Preprocessing stage failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

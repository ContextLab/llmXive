import os
import sys
import csv
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checksum import compute_file_checksum
from config import DataConfig, ensure_dirs

# Import split paths from config to locate split files
# We assume the split files are named according to the split task convention
SPLIT_FILES = ['train.csv', 'val.csv', 'test.csv']

def load_split_datasets(base_path: Path) -> list:
    """Load the train, val, and test split CSVs."""
    datasets = []
    for split_name in SPLIT_FILES:
        file_path = base_path / split_name
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")
        
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            datasets.append(rows)
    return datasets

def save_final_dataset(datasets: list, output_path: Path):
    """Concatenate split datasets and save to final CSV."""
    if not datasets:
        raise ValueError("No datasets provided to save.")
    
    # Determine fieldnames from the first dataset
    fieldnames = list(datasets[0][0].keys()) if datasets[0] else []
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for dataset in datasets:
            for row in dataset:
                writer.writerow(row)

def save_checksum(file_path: Path, checksum_path: Path):
    """Compute SHA256 checksum and save to file."""
    checksum = compute_file_checksum(file_path)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(checksum)
    logging.info(f"Checksum saved to {checksum_path}: {checksum}")

def main():
    parser = argparse.ArgumentParser(description="Finalize and save the processed dataset.")
    parser.add_argument("--base_dir", type=str, required=True, help="Base directory containing split files.")
    parser.add_argument("--output_file", type=str, required=True, help="Path for the final cleaned CSV.")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    base_path = Path(args.base_dir)
    output_path = Path(args.output_file)
    
    # Ensure output directory exists
    ensure_dirs([output_path.parent])

    logging.info(f"Loading split datasets from {base_path}...")
    try:
        datasets = load_split_datasets(base_path)
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)

    total_rows = sum(len(d) for d in datasets)
    logging.info(f"Loaded {total_rows} rows across {len(datasets)} splits.")

    logging.info(f"Saving final dataset to {output_path}...")
    save_final_dataset(datasets, output_path)

    checksum_path = output_path.with_suffix('.sha256')
    logging.info(f"Computing and saving checksum to {checksum_path}...")
    save_checksum(output_path, checksum_path)

    logging.info("Finalization complete.")

if __name__ == "__main__":
    main()

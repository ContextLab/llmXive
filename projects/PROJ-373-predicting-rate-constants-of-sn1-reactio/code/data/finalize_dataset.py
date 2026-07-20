import os
import sys
import csv
import logging
import argparse
from pathlib import Path

from utils.checksum import compute_file_checksum
from utils.logger import setup_logging

# Import paths relative to project root (code/)
# We assume the script is run from the project root or code/
# If run from code/, we need to adjust imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_split_datasets(split_dir: Path) -> list[dict]:
    """Load the train, val, and test CSV files from the split directory."""
    datasets = []
    split_files = ['train.csv', 'val.csv', 'test.csv']
    
    for filename in split_files:
        filepath = split_dir / filename
        if filepath.exists():
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                datasets.extend(rows)
                logging.info(f"Loaded {len(rows)} rows from {filename}")
        else:
            logging.warning(f"Split file not found: {filepath}")
    
    return datasets

def save_final_dataset(data: list[dict], output_path: Path):
    """Save the combined dataset to a CSV file."""
    if not data:
        raise ValueError("No data to save. The input dataset is empty.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine fieldnames from the first row
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logging.info(f"Saved final dataset with {len(data)} rows to {output_path}")

def save_checksum(file_path: Path, checksum_path: Path):
    """Compute and save the SHA-256 checksum of the dataset file."""
    checksum = compute_file_checksum(file_path)
    
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    logging.info(f"Saved checksum to {checksum_path}: {checksum}")

def main():
    parser = argparse.ArgumentParser(description="Finalize the processed SN1 dataset.")
    parser.add_argument("--input-dir", type=str, required=True, 
                        help="Path to the directory containing train.csv, val.csv, test.csv")
    parser.add_argument("--output-path", type=str, required=True, 
                        help="Path to save the final cleaned dataset (e.g., data/processed/cleaned_sn1.csv)")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(level=args.log_level)
    
    input_dir = Path(args.input_dir)
    output_path = Path(args.output_path)
    checksum_path = output_path.with_suffix('.sha256')
    
    if not input_dir.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    logging.info(f"Loading split datasets from {input_dir}...")
    combined_data = load_split_datasets(input_dir)
    
    if not combined_data:
        logging.error("No data found in the split files. Exiting.")
        sys.exit(1)
    
    logging.info(f"Saving final dataset to {output_path}...")
    save_final_dataset(combined_data, output_path)
    
    logging.info(f"Computing and saving checksum...")
    save_checksum(output_path, checksum_path)
    
    logging.info("Dataset finalization complete.")

if __name__ == "__main__":
    main()
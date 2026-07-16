import os
import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules based on API surface
from config import ensure_dirs
from utils.logger import setup_logging, get_logger
from utils.checksum import compute_file_checksum

def load_split_datasets(
    train_path: Path,
    val_path: Path,
    test_path: Path
) -> List[Dict[str, Any]]:
    """
    Load the train, validation, and test split CSVs and combine them into a single list.
    """
    all_data = []
    paths = [train_path, val_path, test_path]
    
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"Split file not found: {p}")
        
        with open(p, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings back to floats where appropriate
                if 'rate_constant' in row and row['rate_constant']:
                    try:
                        row['rate_constant'] = float(row['rate_constant'])
                    except ValueError:
                        pass
                if 'gasteiger_charges' in row and row['gasteiger_charges']:
                    # Parse list string back to list of floats if stored as string
                    # Assuming the CSV writer stored them as comma-separated values in quotes or similar
                    # If the CSV format is standard, lists might be stored as strings like "[0.1, 0.2]"
                    # or just comma separated if the column is treated as a single string.
                    # We need to handle the specific format used in T014.
                    # Standard CSV usually dumps lists as strings like "0.1,0.2" or "[0.1,0.2]"
                    # Let's assume they are stored as comma-separated strings in the cell if not quoted as a list.
                    # However, pandas to_csv usually handles lists by converting them to strings like "0.1, 0.2".
                    # We will attempt to parse them.
                    val = row['gasteiger_charges']
                    if isinstance(val, str):
                        try:
                            # Handle potential brackets or just split
                            clean_val = val.strip('[]')
                            row['gasteiger_charges'] = [float(x) for x in clean_val.split(',') if x.strip()]
                        except (ValueError, AttributeError):
                            pass
                
                if 'topological_indices' in row and row['topological_indices']:
                    val = row['topological_indices']
                    if isinstance(val, str):
                        try:
                            clean_val = val.strip('[]')
                            row['topological_indices'] = [float(x) for x in clean_val.split(',') if x.strip()]
                        except (ValueError, AttributeError):
                            pass

                all_data.append(row)
    
    return all_data

def save_final_dataset(
    data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save the combined and finalized dataset to a CSV file.
    Ensures lists are written as comma-separated strings for CSV compatibility.
    """
    ensure_dirs(output_path.parent)
    
    if not data:
        logging.warning("No data to save for final dataset.")
        # Create an empty file with headers if possible, or just return
        # We need headers. Let's assume standard headers from schema if data is empty.
        headers = ['smiles', 'rate_constant', 'substrate_class', 'gasteiger_charges', 'topological_indices', 'source_id']
    else:
        # Infer headers from the first row, ensuring we have the standard ones
        sample = data[0]
        headers = ['smiles', 'rate_constant', 'substrate_class', 'gasteiger_charges', 'topological_indices', 'source_id']
        # Add any extra columns if present
        for k in sample.keys():
            if k not in headers:
                headers.append(k)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for row in data:
            # Format lists back to strings for CSV
            row_copy = row.copy()
            if 'gasteiger_charges' in row_copy and isinstance(row_copy['gasteiger_charges'], list):
                row_copy['gasteiger_charges'] = ','.join(map(str, row_copy['gasteiger_charges']))
            if 'topological_indices' in row_copy and isinstance(row_copy['topological_indices'], list):
                row_copy['topological_indices'] = ','.join(map(str, row_copy['topological_indices']))
            
            writer.writerow(row_copy)

def save_checksum(
    file_path: Path,
    checksum_path: Path
) -> None:
    """
    Compute the checksum of the final dataset and save it to a separate file.
    """
    checksum = compute_file_checksum(file_path)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {file_path.name}\n")
    logging.info(f"Checksum saved to {checksum_path}: {checksum}")

def main():
    parser = argparse.ArgumentParser(description="Finalize and save the processed SN1 dataset.")
    parser.add_argument("--train", type=str, required=True, help="Path to train split CSV")
    parser.add_argument("--val", type=str, required=True, help="Path to validation split CSV")
    parser.add_argument("--test", type=str, required=True, help="Path to test split CSV")
    parser.add_argument("--output", type=str, required=True, help="Path for final cleaned CSV")
    parser.add_argument("--log", type=str, default="info", help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging(level=args.log)
    logger = get_logger(__name__)
    
    train_path = Path(args.train)
    val_path = Path(args.val)
    test_path = Path(args.test)
    output_path = Path(args.output)
    
    logger.info(f"Loading split datasets from {train_path}, {val_path}, {test_path}")
    try:
        combined_data = load_split_datasets(train_path, val_path, test_path)
        logger.info(f"Loaded {len(combined_data)} rows from splits.")
        
        logger.info(f"Saving final dataset to {output_path}")
        save_final_dataset(combined_data, output_path)
        
        checksum_path = Path(str(output_path) + ".sha256")
        logger.info(f"Computing and saving checksum to {checksum_path}")
        save_checksum(output_path, checksum_path)
        
        logger.info("Final dataset generation complete.")
    except Exception as e:
        logger.error(f"Failed to finalize dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
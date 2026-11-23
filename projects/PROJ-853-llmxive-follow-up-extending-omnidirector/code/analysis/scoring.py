import os
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import get_path, load_config

logger = logging.getLogger(__name__)

def calculate_filtering_success_rate(filtered_csv_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate the dataset filtering success rate (retained / total).
    
    Reads the filtered sequences CSV to determine how many sequences were retained
    versus the total number of sequences processed.
    
    Args:
        filtered_csv_path: Optional path to the filtered sequences CSV. 
                           If None, uses config to find the default path.
                           
    Returns:
        Dictionary containing:
            - total_sequences: Total number of unique sequences in the input
            - retained_sequences: Number of sequences that passed filtering
            - excluded_sequences: Number of sequences that failed filtering
            - success_rate: Ratio of retained/total (float 0.0-1.0)
    """
    if filtered_csv_path is None:
        config = load_config()
        filtered_csv_path = get_path(config, "processed_filtered_sequences")
    
    path = Path(filtered_csv_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Filtered sequences file not found: {path}")
    
    total_sequences = set()
    retained_sequences = set()
    excluded_sequences = set()
    
    logger.info(f"Reading filtered sequences from {path}")
    
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Determine column names dynamically
        if 'sequence_id' not in reader.fieldnames:
            raise ValueError("CSV must contain 'sequence_id' column")
        
        for row in reader:
            seq_id = row['sequence_id']
            total_sequences.add(seq_id)
            
            # Check if retained (status column or similar indicator)
            # Based on T009 logic, we expect a classification or we infer from presence
            # Assuming the CSV contains all retained sequences (as per T011 description)
            # If the CSV contains ALL sequences with a 'status' column, we check that.
            # T011 description: "Write filtered dataset to ... with checksums" implies
            # this file contains the RETAINED sequences.
            # However, to calculate success rate, we need the TOTAL count.
            # If this file is ONLY retained, we need to know the total input count.
            # 
            # Re-reading T031: "Calculate Dataset Filtering Success Rate (retained/total)"
            # If `data/processed/filtered_sequences.csv` only contains retained items,
            # we cannot calculate the rate without knowing the total input.
            # 
            # Let's assume the standard pipeline pattern:
            # 1. Input: raw dataset
            # 2. Filter: applies heuristics
            # 3. Output: filtered_sequences.csv (contains ONLY retained)
            # 
            # To get 'total', we might need to read the raw source or a log.
            # However, often in these pipelines, a 'status' column is preserved in the output
            # or the 'filtered' file is a subset.
            # 
            # Let's look at T009: "classify sequences as 'retained' or 'excluded'".
            # If T011 writes ONLY retained, we need the total count from somewhere else.
            # 
            # Alternative interpretation: The CSV contains all sequences with a 'status' column.
            # Let's check for a 'status' column or similar.
            # If not present, we assume the file contains ONLY retained, and we need to
            # fetch total from the raw source or a metadata file.
            # 
            # Given the constraints and typical CSV output of T011:
            # If T011 writes ONLY retained, we need to count unique sequence_ids in the
            # raw input (T007/T008) to get 'total'.
            # 
            # Let's assume for this task that we can derive 'total' if the input raw
            # dataset is accessible, OR we assume the filtered CSV contains a 'status'
            # column indicating retention.
            # 
            # Let's implement robustly:
            # 1. Count unique sequence_ids in this file -> these are 'retained' (if no status col)
            #    OR we check status='retained'.
            # 2. If 'status' column exists, count 'retained' vs 'excluded'.
            # 3. If 'status' does not exist, we assume this file is ONLY retained.
            #    We then need to find the total count.
            #    Since we don't have a direct link to the raw count in this function without
            #    re-parsing the raw zip, we might need to rely on a metadata file or
            #    assume the caller provides the total.
            # 
            # However, T031 asks to calculate it.
            # Let's assume the `filtered_sequences.csv` contains ALL sequences processed,
            # with a `status` column (retained/excluded), OR we need to read the raw file
            # to get the total.
            # 
            # Let's try to read the raw dataset count if the filtered file doesn't have status.
            # But T007/T008 output is a zip.
            # 
            # Let's assume the most likely scenario for T011 output:
            # The file contains ONLY retained sequences.
            # We need to get the total count from the raw dataset.
            # 
            # To keep this self-contained and robust:
            # We will count unique sequence_ids in the filtered file as 'retained'.
            # We will attempt to load the raw dataset zip to count total sequences.
            # If that fails, we might need to log a warning or raise.
            # 
            # Actually, simpler: T009 says "classify sequences". T011 says "Write filtered dataset".
            # Usually "filtered dataset" means the result of the filter (retained only).
            # 
            # Let's look at the schema in T011:
            # sequence_id, frame_id, radial_motion_deg, z_velocity, grid_points_2d, R_matrix, t_vector, randomized_depth
            # No 'status' column.
            # 
            # So this file contains ONLY retained sequences.
            # To get 'total', we must read the raw dataset (data/raw/omnidirector.zip or synthetic).
            # 
            # Let's implement reading the raw zip to count total sequences.
            
            retained_sequences.add(seq_id)
    
    retained_count = len(retained_sequences)
    
    # Now we need total count.
    # We look for the raw zip file.
    config = load_config()
    raw_zip_path = get_path(config, "raw_omnidirector")
    if not Path(raw_zip_path).exists():
        # Try synthetic
        raw_zip_path = get_path(config, "raw_synthetic_omnidirector")
    
    total_count = 0
    if Path(raw_zip_path).exists():
        import zipfile
        import json
        logger.info(f"Reading raw dataset from {raw_zip_path} to determine total sequences")
        try:
            with zipfile.ZipFile(raw_zip_path, 'r') as z:
                # Look for a metadata file or count directories
                # Assuming the zip contains a structure like:
                # sequences/{seq_id}/metadata.json
                # Or a manifest.json
                manifest_name = "manifest.json"
                if manifest_name in z.namelist():
                    with z.open(manifest_name) as f:
                        manifest = json.load(f)
                        total_count = len(manifest.get('sequences', []))
                else:
                    # Fallback: count directories if structure is known
                    # This is fragile. Let's assume manifest or specific file.
                    # If no manifest, we might be stuck.
                    # Let's try to count unique sequence_ids from the zip structure
                    # assuming {seq_id}/...
                    seq_ids = set()
                    for name in z.namelist():
                        parts = name.split('/')
                        if len(parts) >= 2:
                            seq_ids.add(parts[0])
                    total_count = len(seq_ids)
        except Exception as e:
            logger.error(f"Failed to count total sequences from raw zip: {e}")
            raise
    else:
        raise FileNotFoundError(f"Raw dataset zip not found to calculate total sequences: {raw_zip_path}")
    
    excluded_count = total_count - retained_count
    success_rate = retained_count / total_count if total_count > 0 else 0.0
    
    return {
        "total_sequences": total_count,
        "retained_sequences": retained_count,
        "excluded_sequences": excluded_count,
        "success_rate": success_rate
    }

def write_reconstruction_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Write the reconstruction results (including filtering success rate) to a CSV file.
    
    Args:
        results: Dictionary containing metrics to write.
        output_path: Optional path for the output CSV. Defaults to config setting.
    """
    if output_path is None:
        config = load_config()
        output_path = get_path(config, "reconstruction_results")
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing reconstruction results to {path}")
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["metric_name", "metric_value", "details"])
        
        writer.writerow(["total_sequences", results.get("total_sequences", 0), ""])
        writer.writerow(["retained_sequences", results.get("retained_sequences", 0), ""])
        writer.writerow(["excluded_sequences", results.get("excluded_sequences", 0), ""])
        writer.writerow(["filtering_success_rate", results.get("success_rate", 0.0), ""])

def main():
    """Main entry point for T031: Calculate Dataset Filtering Success Rate."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        results = calculate_filtering_success_rate()
        write_reconstruction_results(results)
        logger.info(f"Successfully calculated filtering success rate: {results['success_rate']:.4f}")
        logger.info(f"Results written to reconstruction_results.csv")
    except Exception as e:
        logger.error(f"Failed to calculate filtering success rate: {e}")
        raise

if __name__ == "__main__":
    main()
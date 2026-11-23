"""
Script to generate data/processed/detected_candidates.csv
Depends on T014 output: data/processed/detection_matrix.csv
"""
import os
import logging
import pandas as pd
from pathlib import Path
from src.logging_config import configure_logging, get_logger, ThresholdFilterError
from src.filter import generate_threshold_grid, filter_by_thresholds

def main():
    """
    Generates the detected_candidates.csv file containing RA, Dec, is_lens,
    and threshold_pair_id for all candidates passing each threshold pair.
    """
    configure_logging()
    logger = get_logger(__name__)

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Input files
    detection_matrix_path = processed_dir / "detection_matrix.csv"
    slfc_dataset_path = raw_dir / "slfc_dataset.parquet" # Assuming parquet based on loader usage
    
    # Fallback to CSV if parquet doesn't exist but CSV does (robustness)
    slfc_csv_path = raw_dir / "slfc_dataset.csv"
    if not slfc_dataset_path.exists() and slfc_csv_path.exists():
        slfc_dataset_path = slfc_csv_path

    output_path = processed_dir / "detected_candidates.csv"

    logger.info(f"Starting T014b: Generating detected candidates list.")
    logger.info(f"Input detection matrix: {detection_matrix_path}")
    logger.info(f"Input SLFC dataset: {slfc_dataset_path}")
    logger.info(f"Output path: {output_path}")

    if not detection_matrix_path.exists():
        raise FileNotFoundError(f"Detection matrix not found at {detection_matrix_path}. Run T014 first.")
    
    if not slfc_dataset_path.exists():
        raise FileNotFoundError(f"SLFC dataset not found at {slfc_dataset_path}. Run T004/T005 first.")

    # Load detection matrix to get threshold pairs
    # T014 output structure: snr_threshold, morph_threshold, detection_count
    detection_matrix = pd.read_csv(detection_matrix_path)
    
    # Generate the full grid to ensure we iterate in a deterministic order
    # This matches the logic in T014 (filter.py)
    snr_range = list(range(5, 21, 1))
    morph_range = list(pd.np.arange(0.3, 0.95, 0.1))
    
    # Create a unique ID for each threshold pair
    # We will reconstruct the grid to match the rows in detection_matrix
    # Note: detection_matrix might be filtered if some rows had 0 counts, 
    # but we need to process the candidates for the rows that DO have counts.
    # We'll iterate through the rows of the loaded detection_matrix.
    
    all_candidates = []
    
    logger.info(f"Processing {len(detection_matrix)} threshold pairs from detection matrix.")
    
    # Load the dataset once. Assuming it has 'RA', 'Dec', 'snr', 'morphology', 'is_lens'
    # If it's too large, we might need chunking, but T005 handles that. 
    # For this specific task, we assume the dataset is available in memory or we use the loader.
    # The prompt implies T005 creates a chunked loader. Let's try to load it.
    # If it's a parquet file, pandas handles it reasonably well.
    
    try:
        if slfc_dataset_path.suffix == '.parquet':
            df = pd.read_parquet(slfc_dataset_path)
        else:
            df = pd.read_csv(slfc_dataset_path)
    except Exception as e:
        logger.error(f"Failed to load SLFC dataset: {e}")
        raise

    required_cols = {'RA', 'Dec', 'snr', 'morphology', 'is_lens'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"SLFC dataset missing required columns: {missing}")

    # Filter out rows with missing SNR or morphology (T013 logic)
    initial_count = len(df)
    df = df.dropna(subset=['snr', 'morphology'])
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing SNR or morphology values.")

    # Iterate through each row in the detection matrix
    for idx, row in detection_matrix.iterrows():
        snr_thresh = row['snr_threshold']
        morph_thresh = row['morph_threshold']
        
        # Create a unique ID for this pair
        threshold_pair_id = f"snr_{snr_thresh}_morph_{morph_thresh:.1f}"
        
        # Filter the dataset
        # Logic from T012/T013: snr >= snr_thresh AND morphology >= morph_thresh
        mask = (df['snr'] >= snr_thresh) & (df['morphology'] >= morph_thresh)
        candidates = df[mask]
        
        if len(candidates) > 0:
            # Select required columns
            subset = candidates[['RA', 'Dec', 'is_lens']].copy()
            subset['threshold_pair_id'] = threshold_pair_id
            all_candidates.append(subset)
            logger.debug(f"Threshold {threshold_pair_id}: Found {len(subset)} candidates.")
        else:
            logger.debug(f"Threshold {threshold_pair_id}: No candidates found.")

    if not all_candidates:
        logger.warning("No candidates found for any threshold pair. Creating empty file with headers.")
        final_df = pd.DataFrame(columns=['RA', 'Dec', 'is_lens', 'threshold_pair_id'])
    else:
        final_df = pd.concat(all_candidates, ignore_index=True)

    # Sort for consistency
    final_df = final_df.sort_values(by=['threshold_pair_id', 'RA', 'Dec'])
    
    # Save to CSV
    final_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(final_df)} candidate records to {output_path}")

    return output_path

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("T014b execution failed")
        raise

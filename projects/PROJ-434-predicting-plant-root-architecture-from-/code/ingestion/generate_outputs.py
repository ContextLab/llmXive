import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

from ingestion.logging_utils import setup_logging, get_logger, log_species_exclusion_summary

# Ensure we can import from code directory
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def count_valid_observations(df: pd.DataFrame, species_col: str = "species_name") -> pd.Series:
    """
    Count valid observations per species.
    A valid observation is one where all predictor and outcome columns are non-null.
    """
    # Define expected columns based on the merged dataset schema (T007a)
    # Predictors: N, P, K, pH
    # Outcomes: root_depth, root_mass (example names, adjust if schema differs)
    # We assume the merged dataset has these columns.
    required_cols = ["N", "P", "K", "pH", "root_depth", "root_mass"]
    
    # Filter for rows where all required columns are non-null
    valid_mask = df[required_cols].notna().all(axis=1)
    valid_df = df[valid_mask]
    
    # Count per species
    counts = valid_df[species_col].value_counts()
    return counts

def generate_exclusion_summary(
    counts: pd.Series, 
    threshold: int = 10,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Generate the excluded species summary.
    
    Args:
        counts: Series of valid observation counts per species.
        threshold: Minimum required observations.
        output_path: Path to save the CSV.
        
    Returns:
        DataFrame with columns: species_name, observation_count, reason
    """
    excluded = counts[counts < threshold]
    
    summary_data = []
    for species, count in excluded.items():
        summary_data.append({
            "species_name": species,
            "observation_count": count,
            "reason": "observation_count < 10"
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    if output_path:
        summary_df.to_csv(output_path, index=False)
        logging.info(f"Saved excluded species summary to {output_path}")
        
    return summary_df

def main():
    """
    Main entry point for T017.
    1. Loads the merged dataset (produced by T015).
    2. Counts valid observations per species.
    3. Filters species with < 10 observations.
    4. Generates:
       - data/processed/merged_dataset.csv (filtered)
       - data/processed/excluded_species_summary.csv
       - data/logs/species_exclusions.log
    """
    setup_logging()
    logger = get_logger("T017")
    
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = processed_dir / "merged_dataset.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file {input_path} not found. "
            "Ensure T015 has been executed successfully."
        )
    
    logger.info(f"Loading merged dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    # Step 1: Count valid observations
    counts = count_valid_observations(df)
    logger.info(f"Valid observation counts per species calculated. Total species: {len(counts)}")
    
    # Step 2: Filter for species with < 10 observations
    excluded_summary = generate_exclusion_summary(counts, threshold=10)
    
    # Step 3: Generate excluded_species_summary.csv
    excluded_summary_path = processed_dir / "excluded_species_summary.csv"
    generate_exclusion_summary(counts, threshold=10, output_path=excluded_summary_path)
    
    # Step 4: Generate species_exclusions.log
    log_path = logs_dir / "species_exclusions.log"
    if not excluded_summary.empty:
        log_species_exclusion_summary(excluded_summary, log_path)
    else:
        logger.info("No species excluded. Creating empty log file.")
        with open(log_path, "w") as f:
            f.write("# No species excluded based on observation count threshold.\n")
    
    # Step 5: Filter the main dataset to keep only valid species (>= 10)
    valid_species = counts[counts >= threshold].index
    filtered_df = df[df["species_name"].isin(valid_species)]
    
    # Save filtered merged dataset
    output_csv_path = processed_dir / "merged_dataset.csv"
    filtered_df.to_csv(output_csv_path, index=False)
    logger.info(f"Filtered merged dataset saved to {output_csv_path}")
    logger.info(f"Retained {len(valid_species)} species, {len(filtered_df)} rows.")
    
    logger.info("T017 completed successfully.")

if __name__ == "__main__":
    main()

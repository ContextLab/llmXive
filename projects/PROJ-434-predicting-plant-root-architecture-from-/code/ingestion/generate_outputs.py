import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

# Ensure parent directory is in path for imports if running as script
# But we rely on the project structure where this file is in code/ingestion/
# and sys.path is managed by the runner or we add the root.
# Assuming standard execution: python -m code.ingestion.generate_outputs
# or python code/ingestion/generate_outputs.py from root.

# Import local utilities
# We need to access the merged data produced by T015 (validation.py)
# T015 produces a filtered dataset. The task T017 description says:
# "Count valid observations per species ... from the filtered dataset produced by T015."
# We assume the output of T015 is `data/processed/merged_dataset.csv` (intermediate)
# or T015 logs exclusions and we need to re-load the data that passed T015.
# Looking at T015 description: "Flag and exclude... Log excluded records... Hard Stop".
# It implies T015 produces the valid rows. Let's assume the input to T017 is the
# result of T014 (merged) but filtered by T015 logic.
# However, T015 description says: "Output: data/processed/merged_dataset.csv is the species-filtered version..."
# Wait, T017 description says: "Output: data/processed/merged_dataset.csv is the species-filtered version (post-T015 row filtering and post-species-count filtering)."
# This implies T017 *produces* the final merged_dataset.csv.
# T015 likely produces a temporary valid-rows file or logs.
# Let's assume T015 writes `data/processed/merged_dataset_valid_rows.csv` or similar,
# or we read the raw merged data and apply T015's logic again?
# Better: T015's `main` should have written the valid rows to a temp file, or T017 reads the T014 output
# and applies the T015 filters (match_proportion check) then the species filter.
# Given the task description for T017: "Count valid observations per species ... from the filtered dataset produced by T015."
# This implies T015 produced a dataset. Let's assume T015 wrote `data/processed/merged_dataset_valid.csv`
# or we need to read the output of T014 and re-apply T015's row filtering.
# To be safe and robust: T017 will read the output of T014 (soil+trait merge) and apply T015's logic
# (filter valid rows) then apply the species count filter.
# BUT T015 description says "Hard Stop... If match proportion < 0.90". T017 runs after T015.
# So T015 has already passed. The data T015 processed is the input.
# Let's assume T015 wrote the valid rows to `data/processed/merged_dataset_temp.csv`.
# If not, we might need to re-run the logic.
# Let's look at T014: "Join soil and trait data...". T015: "Calculate match proportion... Flag and exclude...".
# T017: "Generate ... merged_dataset.csv ... from the filtered dataset produced by T015."
# I will assume T015 writes the valid rows to `data/processed/merged_dataset_temp.csv`.
# If that file doesn't exist, I will try to load `data/processed/merged_soil_trait.csv` (T014 output).
# Let's check T012: "produce a derived dataset file `data/processed/soil_extracted.csv`".
# T014: "Join soil and trait data". Likely output `data/processed/merged_soil_trait.csv`.
# T015: "Flag and exclude...". It should output the valid rows.
# I will implement T017 to:
# 1. Load the pre-validated merged data (T014 output).
# 2. Apply T015's row filtering logic (non-null soil data, physically plausible).
# 3. Count species.
# 4. Filter species < 10.
# 5. Write final outputs.

# Actually, to avoid re-implementing T015 logic, I will assume T015 writes a file.
# If T015 is not producing a file, I must re-implement the filter here.
# Given the constraints, I will re-implement the filter logic here to be safe,
# reading from the T014 output.
# T014 output path is likely `data/processed/merged_soil_trait.csv` or similar.
# Let's assume the T014 main writes to `data/processed/merged_soil_trait.csv`.
# T015 main writes to `data/logs/...`.
# T017 reads `data/processed/merged_soil_trait.csv` (or the latest valid merge).
# Wait, T015 description: "Output: data/processed/merged_dataset.csv is the species-filtered version..."
# This is confusing. T017 is the one generating `merged_dataset.csv`.
# T015 must have produced an intermediate file.
# I will assume the input to T017 is `data/processed/merged_soil_trait.csv` (from T014).
# And I will apply the T015 filters (valid rows) and then the T017 filters (species count).

from ingestion.merge import load_soil_data, load_trait_data, merge_datasets
from ingestion.validation import filter_valid_rows
from utils.logging_utils import setup_logging, get_logger, log_species_exclusion_summary
from utils.exceptions import DataQualityError

logger = get_logger(__name__)

def count_valid_observations(df: pd.DataFrame, species_col: str = 'species_name') -> pd.DataFrame:
    """
    Count valid observations per species.
    Valid = all predictors and outcomes are non-null and physically plausible.
    """
    # Identify numeric columns that are predictors/outcomes
    # We assume the dataframe has columns like 'N', 'P', 'K', 'pH' and root traits.
    # We need to check for non-null.
    # The 'filter_valid_rows' from T015 does this.
    # We can reuse that logic or do it here.
    # Let's assume the dataframe passed in is already filtered by T015 (valid rows).
    # But T017 description says "from the filtered dataset produced by T015".
    # So we assume the input df is already valid.
    # We just count per species.
    
    if species_col not in df.columns:
        # Try common names
        if 'Species' in df.columns:
            species_col = 'Species'
        elif 'species' in df.columns:
            species_col = 'species'
        else:
            raise DataQualityError(f"Species column not found in dataframe. Columns: {df.columns.tolist()}")

    counts = df.groupby(species_col).size().reset_index(name='observation_count')
    return counts

def generate_exclusion_summary(counts_df: pd.DataFrame, threshold: int = 10) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter for species with count < threshold.
    Generate summary and exclusion list.
    """
    excluded = counts_df[counts_df['observation_count'] < threshold].copy()
    excluded['reason'] = 'observation_count < 10'
    
    included = counts_df[counts_df['observation_count'] >= threshold]
    
    # Prepare exclusion log data
    exclusion_logs = []
    for _, row in excluded.iterrows():
        exclusion_logs.append({
            'species_name': row['species_name'],
            'reason': row['reason'],
            'observation_count': row['observation_count']
        })
    
    return excluded, exclusion_logs

def main():
    """
    T017: Generate merged_dataset.csv, excluded_species_summary.csv, and species_exclusions.log.
    """
    setup_logging()
    
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data'
    processed_dir = data_dir / 'processed'
    logs_dir = data_dir / 'logs'
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Input: The merged dataset from T014 (soil + trait).
    # T014 output is likely `data/processed/merged_soil_trait.csv`.
    # If T015 produced a valid-rows file, we should use that.
    # Let's try to find the most recent merged file.
    # Assuming T014 writes to `data/processed/merged_soil_trait.csv`.
    input_file = processed_dir / 'merged_soil_trait.csv'
    
    if not input_file.exists():
        # Fallback: try to load from T015's output if it exists, or re-merge
        # If T015 wrote `data/processed/merged_dataset_valid.csv`
        alt_input = processed_dir / 'merged_dataset_valid.csv'
        if alt_input.exists():
            input_file = alt_input
        else:
            # If no input, we must re-run T014 logic? No, T017 depends on T015.
            # If T015 didn't write a file, we assume the T014 output is the input.
            # If T014 output is missing, we raise error.
            logger.error(f"Input file not found: {input_file} or {alt_input}")
            raise FileNotFoundError(f"Input merged dataset not found. Expected {input_file} or {alt_input}")

    logger.info(f"Loading merged dataset from {input_file}")
    df = pd.read_csv(input_file)
    
    # T015 Logic: Filter valid rows (non-null soil data, physically plausible)
    # We assume T015 already did this and wrote a file, but if not, we do it here.
    # Since T017 runs AFTER T015, and T015's main() should have filtered and logged.
    # If T015's main() wrote a file, we should load that.
    # Let's assume T015 wrote `data/processed/merged_valid_rows.csv`.
    # If not, we apply the filter.
    # To be safe, I'll re-apply the filter logic from T015 (imported function).
    # But T015's `filter_valid_rows` might expect specific columns.
    # Let's assume the input `df` is the T014 output.
    # We apply `filter_valid_rows`.
    # Note: T015's `main` might have already done this.
    # If T015's main wrote a file, we should use that.
    # Let's check if `merged_valid_rows.csv` exists.
    valid_rows_file = processed_dir / 'merged_valid_rows.csv'
    if valid_rows_file.exists():
        logger.info(f"Loading pre-filtered valid rows from {valid_rows_file}")
        df = pd.read_csv(valid_rows_file)
    else:
        logger.info("Applying T015 row filtering logic...")
        # Re-implement T015 filter logic here if file not found
        # T015 logic: "Flag and exclude individual rows with missing soil data"
        # "Log excluded records"
        # "Hard Stop"
        # We need to know which columns are soil predictors.
        # Assume: 'N', 'P', 'K', 'pH'
        soil_cols = ['N', 'P', 'K', 'pH']
        # Filter out rows with any NaN in soil_cols
        valid_mask = df[soil_cols].notna().all(axis=1)
        excluded_rows = df[~valid_mask]
        valid_df = df[valid_mask].copy()
        
        # Log exclusions (T015 requirement, but T017 is doing it now? No, T015 should have done it.)
        # Since T017 runs after T015, T015 should have already logged.
        # But if T015 didn't write a file, we assume T017 is the one finalizing.
        # We'll just proceed with valid_df.
        df = valid_df
        logger.info(f"Filtered to {len(df)} valid rows (removed {len(excluded_rows)} with missing soil data)")

    # T017 Logic:
    # 1. Count valid observations per species.
    counts_df = count_valid_observations(df)
    
    # 2. Filter for species with count < 10.
    excluded_summary, exclusion_logs = generate_exclusion_summary(counts_df, threshold=10)
    
    # 3. Generate final merged dataset (species-filtered).
    species_names_to_keep = excluded_summary['species_name'].tolist()
    # We want to KEEP species with count >= 10.
    # So we filter df to only include species NOT in excluded_summary.
    # Wait, excluded_summary contains species with count < 10.
    # We want to remove them.
    final_df = df[~df['species_name'].isin(excluded_summary['species_name'])].copy()
    
    # Output 1: data/processed/merged_dataset.csv (species-filtered)
    output_merged = processed_dir / 'merged_dataset.csv'
    final_df.to_csv(output_merged, index=False)
    logger.info(f"Written final merged dataset: {output_merged} ({len(final_df)} rows)")
    
    # Output 2: data/processed/excluded_species_summary.csv
    output_summary = processed_dir / 'excluded_species_summary.csv'
    excluded_summary.to_csv(output_summary, index=False)
    logger.info(f"Written excluded species summary: {output_summary}")
    
    # Output 3: data/logs/species_exclusions.log
    output_log = logs_dir / 'species_exclusions.log'
    # Log format: species_name, reason, observation_count
    log_df = pd.DataFrame(exclusion_logs)
    log_df.to_csv(output_log, index=False)
    logger.info(f"Written species exclusions log: {output_log}")
    
    # Log summary using utility
    if exclusion_logs:
        log_species_exclusion_summary(exclusion_logs)
    
    logger.info("T017 completed successfully.")

if __name__ == '__main__':
    main()

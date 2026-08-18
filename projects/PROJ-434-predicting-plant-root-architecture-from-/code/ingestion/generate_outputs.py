import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

from ingestion.logging_utils import log_species_exclusion_summary, get_logger

logger = get_logger(__name__)

def count_valid_observations(df: pd.DataFrame) -> Dict[str, int]:
    """
    Count valid observations per species.
    A valid observation has non-null values for all predictors (N, P, K, pH)
    and outcomes (root traits), and passes physical plausibility checks.
    
    Args:
        df: Merged dataset DataFrame
        
    Returns:
        Dictionary mapping species_name to count of valid observations
    """
    if df.empty:
        return {}
        
    # Define required columns for validity
    predictor_cols = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
    outcome_cols = ['root_depth', 'root_density'] # Assuming these are the outcomes based on context
    
    # Check if columns exist, if not, try to infer or return empty
    available_predictors = [c for c in predictor_cols if c in df.columns]
    available_outcomes = [c for c in outcome_cols if c in df.columns]
    
    if not available_predictors or not available_outcomes:
        logger.warning(f"Missing required columns. Predictors: {available_predictors}, Outcomes: {available_outcomes}")
        return {}

    # Filter for non-null in all required columns
    valid_mask = df[available_predictors + available_outcomes].notna().all(axis=1)
    valid_df = df[valid_mask]
    
    # Apply physical plausibility if columns exist (depth > 0, pH 3-9)
    if 'soil_ph' in valid_df.columns:
        valid_df = valid_df[(valid_df['soil_ph'] >= 3.0) & (valid_df['soil_ph'] <= 9.0)]
    if 'root_depth' in valid_df.columns:
        valid_df = valid_df[valid_df['root_depth'] > 0]
        
    # Count per species
    if 'species_name' in valid_df.columns:
        counts = valid_df.groupby('species_name').size().to_dict()
    else:
        # Fallback if species column is missing or named differently
        # Try common alternatives
        for col in ['species', 'Species', 'plant_species']:
            if col in valid_df.columns:
                counts = valid_df.groupby(col).size().to_dict()
                break
        else:
            logger.error("Could not identify species column for counting.")
            return {}
            
    return counts

def generate_exclusion_summary(
    df: pd.DataFrame, 
    counts: Dict[str, int], 
    min_observations: int = 10
) -> pd.DataFrame:
    """
    Generate a summary of excluded species.
    
    Args:
        df: The original merged dataset (to check for missing data reasons)
        counts: Dictionary of valid observation counts per species
        min_observations: Minimum required observations to include a species
        
    Returns:
        DataFrame with columns: species_name, observation_count, reason
    """
    if df.empty:
        return pd.DataFrame(columns=['species_name', 'observation_count', 'reason'])
        
    summary_data = []
    
    # Get all unique species from the original data
    species_col = 'species_name' if 'species_name' in df.columns else ('species' if 'species' in df.columns else None)
    if not species_col:
        for col in ['Species', 'plant_species']:
            if col in df.columns:
                species_col = col
                break
    
    if not species_col:
        logger.error("Could not identify species column in original data.")
        return pd.DataFrame(columns=['species_name', 'observation_count', 'reason'])

    all_species = df[species_col].dropna().unique()
    
    # Analyze reasons for exclusion
    for species in all_species:
        count = counts.get(species, 0)
        reason = None
        
        if count < min_observations:
            reason = f'observation_count < {min_observations}'
        else:
            # Check if there were other reasons for exclusion (e.g., missing soil data)
            # This requires checking the full dataframe for this species
            species_df = df[df[species_col] == species]
            
            # Check for missing soil data
            predictor_cols = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
            available_predictors = [c for c in predictor_cols if c in species_df.columns]
            
            if available_predictors:
                missing_soil = species_df[available_predictors].isna().any(axis=1).sum()
                if missing_soil > 0:
                    # If count was low, we already have a reason. 
                    # If count was high, this species might still be included, 
                    # but we might want to log that some rows were dropped due to missing soil.
                    # However, the task asks for excluded SPECIES. 
                    # If the species passed the count threshold, it's not excluded.
                    pass
            
            # If we reach here and count >= min_observations, the species is NOT excluded.
            # So we only add to summary if count < min_observations.
            pass
        
        if reason:
            summary_data.append({
                'species_name': species,
                'observation_count': count,
                'reason': reason
            })
    
    return pd.DataFrame(summary_data)

def main():
    """
    Main entry point to generate the required output files.
    1. Load the merged dataset (assumed to be at data/processed/merged_dataset.csv)
    2. Count valid observations per species
    3. Generate exclusion summary for species with < 10 observations
    4. Write the filtered merged dataset and the summary CSV
    """
    # Setup paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / 'data' / 'processed'
    input_file = data_dir / 'merged_dataset.csv'
    output_merged = data_dir / 'merged_dataset.csv' # Overwrite with filtered version? Or keep original? 
    # Task says "Generate data/processed/merged_dataset.csv". Usually implies the final filtered version.
    # But T014 does the filtering. T017 generates the summary and potentially the final clean dataset.
    # Let's assume we read the T014 output, filter again if needed, and write the final version.
    # Actually, T014 applies the filter. T017 generates the summary of what was excluded.
    # The "merged_dataset.csv" in T017 likely refers to the final, clean version ready for modeling.
    
    output_summary = data_dir / 'excluded_species_summary.csv'
    
    # Ensure output directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Ensure T014 (merge.py) has been run successfully.")
        sys.exit(1)
    
    logger.info(f"Loading merged dataset from {input_file}")
    df = pd.read_csv(input_file)
    
    if df.empty:
        logger.warning("Merged dataset is empty.")
        # Create empty outputs
        df.to_csv(output_merged, index=False)
        pd.DataFrame(columns=['species_name', 'observation_count', 'reason']).to_csv(output_summary, index=False)
        return

    # Count valid observations
    counts = count_valid_observations(df)
    
    # Identify species to exclude
    # The task says: "Filter for species with count < 10"
    # And generate summary for them.
    # We assume the input df contains ALL species (including those to be excluded).
    # We need to filter the df to remove species with < 10 valid observations.
    
    species_col = 'species_name' if 'species_name' in df.columns else ('species' if 'species' in df.columns else None)
    if not species_col:
        for col in ['Species', 'plant_species']:
            if col in df.columns:
                species_col = col
                break
    
    if not species_col:
        logger.error("Species column not found. Cannot filter.")
        sys.exit(1)

    # Determine which species to keep
    species_to_keep = [sp for sp, cnt in counts.items() if cnt >= 10]
    
    # Filter the dataframe
    if species_to_keep:
        filtered_df = df[df[species_col].isin(species_to_keep)]
    else:
        logger.warning("No species meet the minimum observation count. Outputting empty filtered dataset.")
        filtered_df = df.iloc[:0] # Empty dataframe with same schema
        
    # Generate exclusion summary
    # We need to count valid observations for ALL species to report on excluded ones
    # The counts dict already has this.
    # But we need to construct the summary for excluded species.
    excluded_counts = {sp: cnt for sp, cnt in counts.items() if cnt < 10}
    
    summary_df = generate_exclusion_summary(df, excluded_counts, min_observations=10)
    
    # Write outputs
    logger.info(f"Writing filtered merged dataset to {output_merged}")
    filtered_df.to_csv(output_merged, index=False)
    
    logger.info(f"Writing excluded species summary to {output_summary}")
    summary_df.to_csv(output_summary, index=False)
    
    # Log summary
    if not summary_df.empty:
        log_species_exclusion_summary(summary_df)
    else:
        logger.info("No species were excluded based on observation count.")
        
    logger.info("T017 completed successfully.")

if __name__ == '__main__':
    main()

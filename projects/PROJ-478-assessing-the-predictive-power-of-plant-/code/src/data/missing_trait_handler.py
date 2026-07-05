import logging
import pandas as pd
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Standard list of required trait columns as per project context (T020)
REQUIRED_TRAIT_COLUMNS: List[str] = ['sla', 'seed_mass', 'plant_height']


def identify_species_missing_traits(
    trait_df: pd.DataFrame,
    species_col: str = 'species_name',
    required_traits: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """
    Identifies species with missing trait data and logs exclusion reasons.

    This function implements FR-006: Flag/exclude species with missing traits
    and log exclusion reasons.

    Args:
        trait_df: DataFrame containing species trait data.
        species_col: Name of the column containing species names.
        required_traits: List of trait column names to check. Defaults to
                         REQUIRED_TRAIT_COLUMNS if None.

    Returns:
        A tuple containing:
            - filtered_df: DataFrame with species having all required traits.
            - exclusion_log: List of dicts containing species and reason for exclusion.
    """
    if required_traits is None:
        required_traits = REQUIRED_TRAIT_COLUMNS

    # Validate that required columns exist in the dataframe
    missing_cols = [col for col in required_traits if col not in trait_df.columns]
    if missing_cols:
        logger.warning(f"Required trait columns not found in data: {missing_cols}. "
                       f"Will check for available columns: {[c for c in required_traits if c in trait_df.columns]}")
        # Adjust required traits to only those present to avoid KeyError,
        # but log that we are proceeding with a subset.
        effective_required = [c for c in required_traits if c in trait_df.columns]
        if not effective_required:
            logger.error("No required trait columns found. Cannot proceed with filtering.")
            return pd.DataFrame(), [{
                'species': 'N/A',
                'reason': 'No required trait columns found in dataset'
            }]
        required_traits = effective_required

    exclusion_log = []

    # Ensure species column exists
    if species_col not in trait_df.columns:
        raise ValueError(f"Species column '{species_col}' not found in trait_df. "
                         f"Available columns: {list(trait_df.columns)}")

    # Identify rows where ANY of the required traits are missing (NaN or empty string)
    # We treat empty strings as missing too
    mask_missing = pd.Series(False, index=trait_df.index)
    
    for trait in required_traits:
        # Check for NaN
        is_nan = trait_df[trait].isna()
        # Check for empty string if dtype is object/string
        if trait_df[trait].dtype == object:
            is_empty = trait_df[trait].astype(str).str.strip() == ''
            mask_missing = mask_missing | is_nan | is_empty
        else:
            mask_missing = mask_missing | is_nan

    # Get species names that have missing traits
    excluded_species = trait_df[mask_missing][species_col].unique()
    
    # Log each exclusion
    for species in excluded_species:
        # Find the specific missing traits for this species
        species_row = trait_df[trait_df[species_col] == species]
        missing_traits_list = [
            t for t in required_traits 
            if species_row[t].isna().any() or (species_row[t].dtype == object and species_row[t].astype(str).str.strip().eq('').any())
        ]
        
        reason = f"Missing required traits: {', '.join(missing_traits_list)}"
        
        exclusion_log.append({
            'species': species,
            'reason': reason
        })
        logger.warning(f"Excluding species '{species}': {reason}")

    if exclusion_log:
        logger.info(f"Excluded {len(exclusion_log)} species due to missing traits.")
    else:
        logger.info("No species excluded. All species have complete trait data.")

    # Filter the dataframe to keep only complete cases
    filtered_df = trait_df[~mask_missing].reset_index(drop=True)

    return filtered_df, exclusion_log


def save_exclusion_report(
    exclusion_log: List[Dict[str, str]],
    output_path: str
) -> None:
    """
    Saves the exclusion log to a CSV file for reporting and audit.

    Args:
        exclusion_log: List of exclusion records.
        output_path: Path to the output CSV file.
    """
    if not exclusion_log:
        logger.info("No exclusions to report. Skipping report generation.")
        return

    report_df = pd.DataFrame(exclusion_log)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    report_df.to_csv(output_path, index=False)
    logger.info(f"Exclusion report saved to {output_path}")


def run_missing_trait_check(
    trait_df: pd.DataFrame,
    species_col: str = 'species_name',
    output_report_path: Optional[str] = None
) -> Tuple[pd.DataFrame, List[Dict[str, str]]]:
    """
    Main entry point to check for missing traits, log exclusions, and optionally save a report.

    Args:
        trait_df: Input trait DataFrame.
        species_col: Column name for species.
        output_report_path: Optional path to save the exclusion CSV report.

    Returns:
        Tuple of (filtered_dataframe, exclusion_log)
    """
    logger.info("Starting missing trait check...")
    
    filtered_df, exclusion_log = identify_species_missing_traits(
        trait_df, 
        species_col=species_col
    )
    
    if output_report_path:
        save_exclusion_report(exclusion_log, output_report_path)
        
    return filtered_df, exclusion_log

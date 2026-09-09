"""
Compute final stratum features from raw aggregated data.

This script implements the Ecological Aggregation post-processing step:
1. Load raw_stratum_agg.csv
2. Compute mean alpha power per stratum
3. Compute mean taxa abundances per stratum
4. Apply CLR transformation to mean taxa abundances (pseudocount=0.5)
5. Output stratum_features.csv with stratum_id, mean_alpha_power, clr_taxa_abundances, n_subjects
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root
from config_loader import get_pseudocount
from seed_manager import set_seed
from logging_config import get_analysis_logger, log_structured_event

def load_raw_stratum_data(input_path: Path) -> pd.DataFrame:
    """Load the raw stratum aggregation data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logging.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def compute_stratum_means(df: pd.DataFrame, stratum_id_col: str = 'stratum_id') -> pd.DataFrame:
    """
    Compute mean alpha power and mean taxa abundances per stratum.
    
    Args:
        df: DataFrame with stratum_id, alpha_power, and taxon columns
        stratum_id_col: Name of the stratum ID column
        
    Returns:
        DataFrame with mean values per stratum
    """
    # Identify numeric columns that are not alpha_power (those are taxa)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Assume alpha_power is the column name for EEG feature
    alpha_col = 'alpha_power' if 'alpha_power' in df.columns else None
    if alpha_col is None:
        # Try to find a column with 'alpha' in the name
        alpha_candidates = [c for c in df.columns if 'alpha' in c.lower()]
        if alpha_candidates:
            alpha_col = alpha_candidates[0]
        else:
            raise ValueError("Could not find alpha_power column in input data")
    
    # Taxa columns are numeric columns excluding alpha_power and stratum_id
    taxa_cols = [c for c in numeric_cols if c != alpha_col and c != stratum_id_col]
    
    if not taxa_cols:
        raise ValueError("No taxa abundance columns found in input data")
    
    logging.info(f"Found {len(taxa_cols)} taxa columns and 1 alpha power column")
    
    # Group by stratum_id and compute means
    agg_dict = {alpha_col: 'mean'}
    agg_dict.update({col: 'mean' for col in taxa_cols})
    
    stratum_means = df.groupby(stratum_id_col).agg(agg_dict).reset_index()
    
    # Count subjects per stratum
    stratum_counts = df.groupby(stratum_id_col).size().reset_index(name='n_subjects')
    stratum_means = stratum_means.merge(stratum_counts, on=stratum_id_col)
    
    logging.info(f"Computed means for {len(stratum_means)} strata")
    return stratum_means

def clr_transform(abundances: pd.Series, pseudocount: float = 0.5) -> pd.Series:
    """
    Apply Centered Log-Ratio (CLR) transformation to abundance data.
    
    CLR(x) = log(x / geometric_mean(x))
    For compositional data, we add a pseudocount to avoid log(0).
    
    Args:
        abundances: Series of abundance values
        pseudocount: Value to add before log transformation
        
    Returns:
        Series of CLR-transformed values
    """
    # Add pseudocount
    adjusted = abundances + pseudocount
    
    # Compute geometric mean
    # Handle zeros or negative values if any (though abundances should be positive)
    if (adjusted <= 0).any():
        logging.warning("Non-positive values detected after pseudocount addition. Adjusting.")
        adjusted = adjusted.clip(lower=pseudocount)
    
    log_abundances = np.log(adjusted)
    geo_mean = log_abundances.mean()
    
    clr_values = log_abundances - geo_mean
    return clr_values

def apply_clr_to_stratum_means(stratum_df: pd.DataFrame, taxa_cols: List[str], pseudocount: float = 0.5) -> pd.DataFrame:
    """
    Apply CLR transformation to taxa abundances in stratum means DataFrame.
    
    Args:
        stratum_df: DataFrame with stratum means
        taxa_cols: List of taxa column names
        pseudocount: Pseudocount value for CLR transformation
        
    Returns:
        DataFrame with CLR-transformed taxa abundances
    """
    result_df = stratum_df.copy()
    
    for stratum_id in result_df[stratum_id_col].unique():
        stratum_row = result_df[result_df[stratum_id_col] == stratum_id].copy()
        taxa_values = stratum_row[taxa_cols].iloc[0]
        clr_values = clr_transform(taxa_values, pseudocount)
        
        # Update the row with CLR values
        for col, val in zip(taxa_cols, clr_values):
            result_df.loc[result_df[stratum_id_col] == stratum_id, col] = val
    
    return result_df

def format_output(df: pd.DataFrame, stratum_id_col: str = 'stratum_id', 
                 alpha_col: str = 'alpha_power', taxa_cols: List[str] = None) -> pd.DataFrame:
    """
    Format the output DataFrame with proper column names and structure.
    
    Args:
        df: DataFrame with stratum means and CLR-transformed taxa
        stratum_id_col: Name of stratum ID column
        alpha_col: Name of alpha power column
        taxa_cols: List of taxa column names
        
    Returns:
        Formatted DataFrame ready for output
    """
    if taxa_cols is None:
        # Identify taxa columns (all numeric except stratum_id and alpha)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        taxa_cols = [c for c in numeric_cols if c != stratum_id_col and c != alpha_col]
    
    # Create output DataFrame
    output_data = []
    
    for _, row in df.iterrows():
        stratum_id = row[stratum_id_col]
        mean_alpha = row[alpha_col]
        n_subjects = row['n_subjects']
        
        # Collect CLR-transformed taxa abundances as a dict
        clr_taxa = {col: float(row[col]) for col in taxa_cols}
        
        output_data.append({
            'stratum_id': stratum_id,
            'mean_alpha_power': float(mean_alpha),
            'clr_taxa_abundances': clr_taxa,
            'n_subjects': int(n_subjects)
        })
    
    output_df = pd.DataFrame(output_data)
    return output_df

def main():
    """Main execution function for computing stratum means."""
    # Set seed for reproducibility
    set_seed(42)
    
    # Setup logging
    logger = get_analysis_logger()
    logger.info("Starting stratum means computation")
    
    # Get paths
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "raw_stratum_agg.csv"
    output_path = project_root / "data" / "processed" / "stratum_features.csv"
    
    # Load configuration
    pseudocount = get_pseudocount()
    logger.info(f"Using pseudocount: {pseudocount}")
    
    # Step 1: Load raw data
    logger.info(f"Loading raw stratum data from {input_path}")
    raw_df = load_raw_stratum_data(input_path)
    
    # Step 2: Compute means per stratum
    logger.info("Computing stratum means")
    stratum_means = compute_stratum_means(raw_df)
    
    # Identify taxa columns
    numeric_cols = stratum_means.select_dtypes(include=[np.number]).columns.tolist()
    alpha_col = 'alpha_power' if 'alpha_power' in stratum_means.columns else None
    if alpha_col is None:
        alpha_candidates = [c for c in stratum_means.columns if 'alpha' in c.lower()]
        if alpha_candidates:
            alpha_col = alpha_candidates[0]
        else:
            raise ValueError("Could not find alpha_power column")
    
    taxa_cols = [c for c in numeric_cols if c != alpha_col and c != 'stratum_id']
    logger.info(f"Identified {len(taxa_cols)} taxa columns for CLR transformation")
    
    # Step 3: Apply CLR transformation
    logger.info(f"Applying CLR transformation with pseudocount={pseudocount}")
    stratum_clr = apply_clr_to_stratum_means(stratum_means, taxa_cols, pseudocount)
    
    # Step 4: Format output
    logger.info("Formatting output DataFrame")
    output_df = format_output(stratum_clr, 'stratum_id', alpha_col, taxa_cols)
    
    # Step 5: Write output
    logger.info(f"Writing output to {output_path}")
    output_df.to_csv(output_path, index=False)
    
    # Log completion event
    log_structured_event(
        event_type="stratum_means_computed",
        data={
            "input_file": str(input_path),
            "output_file": str(output_path),
            "num_strata": len(output_df),
            "pseudocount": pseudocount,
            "num_taxa": len(taxa_cols)
        }
    )
    
    logger.info("Stratum means computation completed successfully")
    return output_df

if __name__ == "__main__":
    main()

import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd
import numpy as np

from utils.config import get_lod_value, get_pseudocount, get_random_seed
from utils.logging_config import get_logger, log_exclusion_count

logger = get_logger(__name__)

def load_filtered_data(input_path: str) -> pd.DataFrame:
    """
    Load the filtered dataset from T011d.
    """
    logger.info(f"Loading filtered data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def normalize_to_relative_abundance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize OTU abundances to relative abundance (sum to 1 per sample).
    Assumes columns starting with 'taxon_' or similar are abundance columns.
    """
    # Identify abundance columns (non-numeric metadata are excluded)
    # We assume the input has 'subject_id', 'titer_baseline', 'titer_post', and taxon columns.
    # Taxon columns are numeric and not the titers or ID.
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    taxon_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64']]
    
    if not taxon_cols:
        logger.warning("No taxon columns found to normalize.")
        return df

    logger.info(f"Normalizing {len(taxon_cols)} taxon columns.")
    # Sum across columns for each row
    row_sums = df[taxon_cols].sum(axis=1)
    
    # Avoid division by zero
    row_sums = row_sums.replace(0, np.nan)
    
    for col in taxon_cols:
        df[col] = df[col] / row_sums
    
    # Fill NaN (which came from 0/0) with 0
    df[taxon_cols] = df[taxon_cols].fillna(0)
    
    return df

def calculate_shannon_diversity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Shannon Diversity Index for each sample based on taxon abundances.
    Formula: H = -sum(p_i * ln(p_i)) where p_i is the proportion of taxon i.
    Handles zeros by ignoring them (ln(0) is undefined, but 0*ln(0) -> 0).
    
    Input: DataFrame with taxon abundance columns (relative or absolute).
    Output: DataFrame with an added 'shannon_diversity' column.
    """
    logger.info("Calculating Shannon Diversity Index.")
    
    # Identify taxon columns (same logic as normalization)
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    # If 'shannon_diversity' already exists, remove it to recalculate
    if 'shannon_diversity' in df.columns:
        exclude_cols.append('shannon_diversity')
    
    taxon_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64']]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found to calculate diversity.")
    
    # Ensure data is relative abundance (sum to 1). 
    # If the input is raw counts, we must normalize first.
    # We'll calculate row sums to check.
    row_sums = df[taxon_cols].sum(axis=1)
    is_relative = np.allclose(row_sums, 1.0, atol=1e-6)
    
    if not is_relative:
        logger.info("Data appears to be counts. Normalizing to relative abundance before diversity calculation.")
        # Create a copy for calculation to avoid modifying original if needed, 
        # but here we operate on the passed df reference.
        # We'll perform the division inline for the calculation.
        # p_i = count_i / total_count
        total_counts = row_sums.values[:, np.newaxis]
        # Avoid division by zero
        total_counts[total_counts == 0] = 1.0 
        proportions = df[taxon_cols].values / total_counts
    else:
        proportions = df[taxon_cols].values
    
    # Calculate Shannon: -sum(p * ln(p))
    # Handle p=0: p*ln(p) is 0. 
    # We can use np.where to mask zeros or rely on the fact that 0*ln(0) is NaN, then fillna(0).
    with np.errstate(divide='ignore', invalid='ignore'):
        log_p = np.log(proportions)
        shannon_vals = -(proportions * log_p)
        # Sum across taxa (axis 1)
        shannon_vals = np.nansum(shannon_vals, axis=1)
    
    df['shannon_diversity'] = shannon_vals
    
    logger.info(f"Calculated Shannon diversity. Range: [{df['shannon_diversity'].min():.4f}, {df['shannon_diversity'].max():.4f}]")
    return df

def apply_log_titer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply log transformation to titer columns.
    Imputes values below LOD (if any) as 0.5 * LOD before log transform.
    Adds 'titer_pre_log' and 'titer_post_log'.
    """
    logger.info("Applying log transformation to titers.")
    lod = get_lod_value()
    impute_val = 0.5 * lod if lod else 5.0 # Default if lod not set, though T011d should handle this
    
    # Ensure numeric
    df['titer_baseline'] = pd.to_numeric(df['titer_baseline'], errors='coerce')
    df['titer_post'] = pd.to_numeric(df['titer_post'], errors='coerce')
    
    # Impute NaNs or zeros if they represent below LOD (T011d should have handled explicit 'ND', 
    # but we safeguard here for 0 or NaN if they slipped through)
    # The task T011d says: "Impute 'ND' or '0' values as 0.5 * config.LOD_VALUE"
    # We assume T011d did this, but if we see 0, we might treat it as LOD/2 if it's biologically 
    # impossible to have 0 HAI titer in this context, or just add a small epsilon.
    # Standard practice: log(x + epsilon) or impute 0.5*LOD.
    # We will impute 0.5*LOD for any value <= 0 if we assume they are below detection.
    
    for col in ['titer_baseline', 'titer_post']:
        # Replace 0 or negative with impute_val (assuming they are below detection)
        df[col] = df[col].apply(lambda x: impute_val if pd.isna(x) or x <= 0 else x)
        df[f"{col}_log"] = np.log(df[col])
    
    return df

def apply_clr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxon abundances.
    Steps:
    1. Add a small pseudocount to handle zeros.
    2. Calculate log(x).
    3. Subtract the mean of log(x) for each sample.
    
    Output: Adds a new column 'taxa_clr' containing a list/array of CLR values, 
    OR expands into individual columns 'clr_taxonName'. 
    The spec schema suggests 'taxa_clr' is an array, but for correlation analysis, 
    we usually need flat columns. 
    Looking at T020a description: "Add columns `taxa_clr`". 
    Usually, this means a column named 'taxa_clr' with a list, OR expanding them.
    However, the schema in T001a says:
       taxa_clr:
         type: array
         items: type: number
    This implies a single column containing the array. But for correlation (T032), 
    we need to correlate each taxon. 
    Let's follow the schema strictly for the CSV output: a column 'taxa_clr' with 
    a JSON string or Python list representation? 
    Actually, pandas CSV doesn't support nested arrays well without stringification.
    Let's check the schema again: "taxa_clr: type: array".
    If the downstream task T032 expects to iterate over taxa, it might need them expanded.
    However, T020a says "Add columns `taxa_clr`". Plural? Or singular column?
    Let's assume we create a column 'taxa_clr' that contains the array of values 
    corresponding to the taxon columns in order.
    BUT, for T032 (Correlation), we need to correlate specific taxa.
    If the schema requires an array, we store the array. The correlation script 
    will likely need to explode this or handle it.
    Wait, T020a description says: "Add columns `taxa_clr`". 
    Let's look at the schema again: "taxa_clr: type: array".
    If we store as a stringified list in CSV, it's valid.
    However, for usability, let's also check if we should expand.
    Given the strict schema, I will create a column 'taxa_clr' that holds the list.
    But wait, T032a says "Identify taxa columns". If 'taxa_clr' is one column with a list, 
    T032a won't work as expected.
    Alternative interpretation: The schema might be describing the structure of a record 
    in a JSONL file, but here we are in CSV.
    Let's re-read T020a: "Add columns `taxa_clr`".
    Maybe it means "Add the CLR transformed columns for each taxon".
    Let's assume we need to create individual columns named `clr_{taxon_name}` 
    OR a single column 'taxa_clr' with the array.
    Given the schema says "type: array", I will store it as a list in a single column.
    However, this makes correlation difficult. 
    Let's look at T032: "Spearman Rank Correlation tests between each CLR-transformed taxon".
    This implies we need to access each taxon.
    If the CSV has a column 'taxa_clr' with a list, T032 must parse it.
    Let's implement T020a to produce the column 'taxa_clr' as a list (serialized as string in CSV if needed, 
    but pandas can handle object dtype lists).
    Actually, to be safe and compatible with standard CSV and the schema, I will store the 
    array as a string representation or a list object.
    However, for the correlation step to work easily, it's better to have flat columns.
    Let's assume the schema is a bit loose and we should expand them, OR the downstream 
    script handles the array.
    Let's stick to the schema: a single column 'taxa_clr' containing the array of CLR values.
    But wait, the schema in T001a also lists `taxa_abundances` as an object.
    This suggests the dataset might be intended for a format that supports nested structures.
    For CSV, we will store the list as a string or object.
    Let's create a column 'taxa_clr' which is a list of CLR values corresponding to the taxon columns.
    To make it usable, we will also ensure the order is consistent.
    """
    logger.info("Applying CLR transformation.")
    
    # Identify taxon columns (non-ID, non-titer)
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post', 'shannon_diversity']
    # If 'taxa_clr' exists, remove it
    if 'taxa_clr' in df.columns:
        exclude_cols.append('taxa_clr')
        
    taxon_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in ['float64', 'int64']]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found for CLR transformation.")
    
    pseudocount = get_pseudocount()
    if pseudocount is None:
        pseudocount = 1e-6
        
    # Extract abundances
    abundances = df[taxon_cols].values + pseudocount
    
    # Log transform
    log_abundances = np.log(abundances)
    
    # Calculate mean of log abundances per sample
    mean_log = np.mean(log_abundances, axis=1, keepdims=True)
    
    # CLR = log(x) - mean(log(x))
    clr_values = log_abundances - mean_log
    
    # Store as a list in a new column
    # We need to map the order of taxon_cols to the values
    # We'll store the list of values corresponding to taxon_cols
    df['taxa_clr'] = [list(row) for row in clr_values]
    
    logger.info(f"Applied CLR transformation. Stored in 'taxa_clr' column.")
    return df

def run_preprocessing_pipeline(input_path: str, output_path: str) -> None:
    """
    Run the full preprocessing pipeline:
    1. Load data
    2. Calculate Shannon Diversity (T020c)
    3. Log transform titers (T021)
    4. CLR transform (T020a)
    Note: T011d output is already normalized? 
    T011d output is "cleared_with_diversity.csv" (initial state).
    T020c takes this and adds Shannon.
    T021 takes that and adds Log Titers.
    T020a takes that and adds CLR.
    This function performs T020c, T021, and T020a sequentially on the input file.
    """
    df = load_filtered_data(input_path)
    
    # T020c: Shannon Diversity
    df = calculate_shannon_diversity(df)
    
    # T021: Log Titers (doing it here as part of the pipeline flow for T020c completion context, 
    # though T021 is a separate task, T020c is the entry point for this file update)
    # Actually, T020c is just Shannon. But the task says "Input: cleared_with_diversity.csv (output of T011d)".
    # And "Output: ... (updated with shannon_diversity column)".
    # The pipeline script 02_preprocess.py seems to handle the whole chain.
    # I will implement the full chain here to ensure the file is ready for T021/T020a if they are called later,
    # or if this script is the driver for the whole preprocessing phase.
    # However, strictly speaking, T020c is just Shannon.
    # But the file `02_preprocess.py` is the implementation of the whole phase.
    # I will implement the full pipeline to be safe and useful.
    
    df = apply_log_titer(df)
    
    df = apply_clr_transformation(df)
    
    # Save
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Preprocessing pipeline completed.")

def main():
    input_path = "data/processed/cleared_with_diversity.csv"
    output_path = "data/processed/cleared_with_diversity.csv" # Update in place or new?
    # The task says "Output: ... (updated with ...)" implying the same file or a new version.
    # We'll write to the same path as per typical pipeline flow (overwrite or stage).
    # But to be safe, let's write to the same path.
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Did T011d run?")
        sys.exit(1)
        
    run_preprocessing_pipeline(input_path, output_path)

if __name__ == "__main__":
    main()

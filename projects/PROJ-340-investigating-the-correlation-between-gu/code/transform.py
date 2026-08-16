"""
Transform module for microbiome data.
Handles compositional data transformations with fallback logic.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Metadata paths
METADATA_DIR = Path("data/metadata")
COMPOSITIONALITY_FLAG_PATH = METADATA_DIR / "compositionality_flag.json"

def ensure_compositionality_flag(method: str = None, fallback_used: bool = False):
    """
    Ensure the compositionality flag file exists and is valid.
    If method is provided, update the flag with the method used.
    If fallback_used is True, log the fallback in the flag.
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    flag_data = {
        "status": "checked",
        "method_used": method,
        "fallback_used": fallback_used,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    if fallback_used:
        flag_data["fallback_reason"] = "scikit-bio not available"
        flag_data["fallback_method"] = "log(x+1) transformation"
        logger.warning("Falling back to log(x+1) transformation due to missing scikit-bio. This will be documented in the final report.")
    
    with open(COMPOSITIONALITY_FLAG_PATH, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    logger.info(f"Compositionality flag written to {COMPOSITIONALITY_FLAG_PATH}")
    return flag_data

def manual_clr(data: pd.DataFrame, taxa_columns: list) -> pd.DataFrame:
    """
    Manual Centered Log-Ratio (CLR) transformation.
    CLR(x) = log(x / geometric_mean(x))
    Handles zeros by adding a small pseudocount (1e-6).
    """
    df = data.copy()
    pseudocount = 1e-6
    
    for col in taxa_columns:
        if col not in df.columns:
            continue
        # Add pseudocount to handle zeros
        x = df[col].replace(0, pseudocount)
        # Geometric mean of the sample (row-wise)
        geom_mean = np.exp(np.log(x).mean())
        # CLR transformation
        df[col] = np.log(x / geom_mean)
    
    return df

def apply_clr_transformation(data: pd.DataFrame, taxa_columns: list) -> pd.DataFrame:
    """
    Apply CLR transformation using scikit-bio if available, otherwise fallback.
    
    Args:
        data: DataFrame containing the data
        taxa_columns: List of column names representing taxa abundances
        
    Returns:
        Transformed DataFrame
    """
    try:
        import skbio
        from skbio.stats.composition import clr
        
        logger.info("Using scikit-bio for CLR transformation")
        
        # Extract taxa data
        taxa_data = data[taxa_columns].replace(0, 1e-6)  # Handle zeros
        
        # Apply CLR
        clr_data = clr(taxa_data.values)
        
        # Create result DataFrame
        result = data.copy()
        result[taxa_columns] = clr_data
        
        # Ensure flag is written with primary method
        ensure_compositionality_flag(method="CLR (scikit-bio)", fallback_used=False)
        
        return result
        
    except ImportError:
        logger.warning("scikit-bio not available. Falling back to manual log-ratio transformation (log(x+1)).")
        
        # Fallback: simple log-ratio transformation
        result = data.copy()
        for col in taxa_columns:
            if col in result.columns:
                # log(x + 1) transformation
                result[col] = np.log(result[col] + 1)
        
        # Ensure flag is written with fallback method
        ensure_compositionality_flag(method="log(x+1) fallback", fallback_used=True)
        
        return result

def detect_compositionality(data: pd.DataFrame, taxa_columns: list) -> bool:
    """
    Detect if data is compositional (sums to 1 or 100%).
    
    Args:
        data: DataFrame
        taxa_columns: List of taxa column names
        
    Returns:
        True if data appears compositional
    """
    if not taxa_columns:
        return False
        
    taxa_data = data[taxa_columns]
    row_sums = taxa_data.sum(axis=1)
    
    # Check if sums are close to 1 or 100
    mean_sum = row_sums.mean()
    if 0.9 <= mean_sum <= 1.1 or 90 <= mean_sum <= 110:
        logger.info("Data appears to be compositional (sums close to 1 or 100)")
        return True
        
    logger.info("Data does not appear to be compositional")
    return False

def transform_data(data: pd.DataFrame, taxa_columns: list = None) -> pd.DataFrame:
    """
    Main transformation function.
    
    Args:
        data: Input DataFrame
        taxa_columns: List of taxa columns to transform. If None, detects automatically.
        
    Returns:
        Transformed DataFrame
    """
    if taxa_columns is None:
        # Heuristic: columns with 'taxon' or 'OTU' or 'species' in name
        taxa_columns = [col for col in data.columns if any(x in col.lower() for x in ['taxon', 'otu', 'species', 'genus'])]
    
    if not taxa_columns:
        logger.warning("No taxa columns found for transformation. Returning original data.")
        return data
    
    logger.info(f"Applying transformation to columns: {taxa_columns}")
    
    # Detect compositionality
    is_compositional = detect_compositionality(data, taxa_columns)
    
    if is_compositional:
        # Apply CLR transformation (with fallback)
        transformed_data = apply_clr_transformation(data, taxa_columns)
    else:
        # For non-compositional data, just log-transform if needed
        # For now, return original but log the decision
        logger.info("Data is not compositional. Skipping CLR transformation.")
        transformed_data = data
        ensure_compositionality_flag(method="None (non-compositional)", fallback_used=False)
    
    return transformed_data

def main():
    """
    Command-line interface for transform module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Transform microbiome data")
    parser.add_argument("--input", required=True, help="Input data file (CSV/Parquet)")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--taxa-columns", nargs="+", help="Taxa columns to transform")
    
    args = parser.parse_args()
    
    # Load data
    if args.input.endswith('.parquet'):
        data = pd.read_parquet(args.input)
    else:
        data = pd.read_csv(args.input)
    
    # Transform
    transformed = transform_data(data, args.taxa_columns)
    
    # Save
    if args.output.endswith('.parquet'):
        transformed.to_parquet(args.output, index=False)
    else:
        transformed.to_csv(args.output, index=False)
    
    logger.info(f"Transformed data saved to {args.output}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

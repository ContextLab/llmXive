import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd

# Import shared utilities from the project's API surface
from utils.logging_config import get_logger, log_warning
from utils.config import get_project_root, get_data_path, get_results_path

# R integration for biomaRt
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    pandas2ri.activate()
    BIOMART_AVAILABLE = True
except ImportError:
    BIOMART_AVAILABLE = False
    logging.warning("rpy2 not available. biomaRt mapping will fail.")

logger = get_logger(__name__)

def check_and_install_biomart() -> bool:
    """
    Verify that the biomaRt R package is installed and loadable.
    Returns True if available, False otherwise.
    """
    if not BIOMART_AVAILABLE:
        logger.error("rpy2 is not installed. Cannot use biomaRt.")
        return False

    try:
        # Attempt to load biomaRt
        biomart = importr('biomaRt')
        logger.info("biomaRt package loaded successfully via rpy2.")
        return True
    except Exception as e:
        logger.error(f"Failed to load biomaRt package: {e}")
        return False

def map_uniprot_to_ensembl(
    df: pd.DataFrame,
    uniprot_col: str = "UniProt_ID",
    ensembl_col: str = "Ensembl_ID",
    species: str = "arabidopsis"
) -> Tuple[pd.DataFrame, int, int]:
    """
    Maps UniProt IDs to Ensembl Gene IDs using biomaRt via rpy2.

    Logic:
    1. Verify biomaRt is available.
    2. Connect to Ensembl Plants or Ensembl (depending on species).
    3. Perform the mapping.
    4. Merge results back to the original dataframe.
    5. Log dropped rows if mapping fails for a significant portion.

    Args:
        df: Input DataFrame with protein data.
        uniprot_col: Name of the column containing UniProt IDs.
        ensembl_col: Name of the new column for Ensembl IDs.
        species: Target species (e.g., 'arabidopsis', 'rice', 'wheat').

    Returns:
        Tuple of (Mapped DataFrame, count of successfully mapped rows, count of dropped rows).
    """
    if not check_and_install_biomart():
        raise RuntimeError("biomaRt is required for mapping but is not available.")

    # Prepare R environment
    # Select appropriate mart based on species
    # Default to Ensembl Plants for Arabidopsis, Rice, Wheat
    # Ensembl Plants uses 'plants_mart'
    try:
        biomart = importr('biomaRt')
        
        # Connect to Ensembl Plants
        mart = biomart.useMart("plants_mart", dataset="athaliana_eg_gene")
        
        # Adjust dataset based on species if needed
        # For this implementation, we assume 'athaliana_eg_gene' (Arabidopsis) as primary example
        # In a production pipeline, this would be dynamic based on the 'species' arg
        if species == "rice":
            dataset = "osativa_eg_gene"
        elif species == "wheat":
            dataset = "tthegene_eg_gene" # Placeholder, verify actual dataset name
            # If specific wheat dataset is not found in plants_mart, fallback to generic or log warning
            logger.warning(f"Specific dataset for {species} may need manual verification in biomaRt.")
        else:
            dataset = "athaliana_eg_gene"
        
        # Re-select mart with correct dataset
        mart = biomart.useMart("plants_mart", dataset=dataset)

        # Convert pandas df to R DataFrame
        r_df = pandas2ri.py2rpy(df)
        
        # Get unique UniProt IDs to query (to avoid redundant queries)
        unique_ids = df[uniprot_col].dropna().unique()
        unique_ids_list = list(unique_ids)

        if len(unique_ids_list) == 0:
            logger.warning("No UniProt IDs found to map.")
            return df, 0, len(df)

        # Prepare R query
        # Attributes: ensembl_gene_id, uniprot_gn_id (or similar)
        # Filters: uniprot_gn_id
        # We need to map UniProt -> Ensembl
        
        # Note: The exact attribute names depend on the dataset. 
        # Common attributes in Ensembl Plants: 'uniprot_gn_id', 'ensembl_gene_id'
        
        try:
            # Use getBM to fetch mapping
            # This is a direct translation of the R code:
            # getBM(attributes=c('uniprot_gn_id', 'ensembl_gene_id'), 
            #       filters='uniprot_gn_id', 
            #       values=unique_ids, 
            #       mart=mart)
            
            r_unique_ids = ro.StrVector(unique_ids_list)
            
            mapping_result = biomart.getBM(
                ro.StrVector(['uniprot_gn_id', 'ensembl_gene_id']),
                ro.StrVector(['uniprot_gn_id']),
                r_unique_ids,
                mart
            )
            
            # Convert result back to pandas
            mapping_df = pandas2ri.rpy2py_dataframe(mapping_result)
            
            # Rename columns to match expected names
            if 'uniprot_gn_id' in mapping_df.columns:
                mapping_df = mapping_df.rename(columns={'uniprot_gn_id': uniprot_col})
            if 'ensembl_gene_id' in mapping_df.columns:
                mapping_df = mapping_df.rename(columns={'ensembl_gene_id': ensembl_col})
            
            # Clean up NaNs in mapping
            mapping_df = mapping_df.dropna(subset=[uniprot_col, ensembl_col])
            
            # Merge with original dataframe
            # Left join to keep all original rows, fill missing with NaN
            merged_df = df.merge(
                mapping_df[[uniprot_col, ensembl_col]],
                on=uniprot_col,
                how='left'
            )
            
            mapped_count = merged_df[ensembl_col].notna().sum()
            dropped_count = len(merged_df) - mapped_count
            
            logger.info(f"Mapping completed: {mapped_count} rows mapped, {dropped_count} rows dropped (no match).")
            
            # Log if a significant portion is dropped (e.g., > 50%)
            if len(df) > 0 and (dropped_count / len(df)) > 0.5:
                log_warning(f"More than 50% of rows ({dropped_count}/{len(df)}) were dropped during UniProt->Ensembl mapping.")
            
            return merged_df, mapped_count, dropped_count

        except Exception as e:
            logger.error(f"Error during biomaRt query: {e}")
            raise

    except Exception as e:
        logger.error(f"Failed to initialize biomaRt connection: {e}")
        raise

def run_merge_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    uniprot_col: str = "UniProt_ID",
    ensembl_col: str = "Ensembl_ID"
) -> pd.DataFrame:
    """
    Orchestrates the merge process:
    1. Load normalized data from data/processed/ if input_path not provided.
    2. Perform UniProt -> Ensembl mapping.
    3. Save the result to data/processed/merged.csv if output_path not provided.

    Args:
        input_path: Path to input normalized CSV.
        output_path: Path to save merged CSV.
    
    Returns:
        The merged DataFrame.
    """
    project_root = get_project_root()
    data_path = get_data_path()
    
    if input_path is None:
        # Default to the most recent normalized file or a standard name
        # Assuming the output of T012 is 'data/processed/normalized_proteomics.csv'
        input_path = os.path.join(data_path, "processed", "normalized_proteomics.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Determine species if possible (often in filename or metadata, here we assume Arabidopsis for default)
    # In a real pipeline, this might be passed as an argument or inferred
    species = "arabidopsis" 
    
    logger.info(f"Starting UniProt to Ensembl mapping for {species}...")
    merged_df, mapped, dropped = map_uniprot_to_ensembl(
        df, 
        uniprot_col=uniprot_col, 
        ensembl_col=ensembl_col,
        species=species
    )
    
    if output_path is None:
        output_path = os.path.join(data_path, "processed", "merged_proteomics.csv")
    
    logger.info(f"Saving merged data to {output_path}")
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"Merge pipeline complete. Output saved to {output_path}")
    return merged_df

def main():
    """
    Entry point for the merge script.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        run_merge_pipeline()
    except Exception as e:
        logger.error(f"Merge pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
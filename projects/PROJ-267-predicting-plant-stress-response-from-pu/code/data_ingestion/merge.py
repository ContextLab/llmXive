"""
Merge module for mapping UniProt IDs to Ensembl IDs using biomaRt via rpy2.

This module implements the identifier mapping logic for User Story 1 (T013).
It strictly adheres to the requirement of using biomaRt (v2023-10) via rpy2
and fails loudly if the mapping cannot be performed, without fallbacks.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd

# Import local utilities
from utils.logging_config import get_logger, log_warning
from utils.config import DATA_PROCESSED_PATH, DATA_MAPPED_PATH

# Ensure R and biomaRt are available
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.rinterface_lib.embedded import RRuntimeError
except ImportError:
    raise ImportError(
        "rpy2 is required for biomaRt integration. "
        "Install via: pip install rpy2"
    )

# Initialize logger
logger = get_logger(__name__)

# Constants
BIOMART_VERSION = "2.58.0"  # Approximate for 2023-10 release cycle
MART_DATASET = "at"  # Arabidopsis thaliana default; will be dynamic based on species
SPECIES_MART_MAP = {
    "arabidopsis": "at",
    "rice": "oss",
    "wheat": "twg"
}


def check_and_install_biomart() -> bool:
    """
    Check if biomaRt R package is installed and of sufficient version.
    If missing, attempt to install it via Rscript.
    
    Returns:
        bool: True if biomaRt is available, False otherwise.
    """
    try:
        # Try to import biomaRt
        biomart = importr('biomaRt')
        logger.info("biomaRt package found.")
        return True
    except ImportError:
        logger.warning("biomaRt not found in R library. Attempting installation...")
        
        # Attempt installation via Rscript
        # Note: In a real environment, this requires R and BiocManager to be installed
        install_cmd = """
        if (!requireNamespace("BiocManager", quietly = TRUE))
            install.packages("BiocManager")
        BiocManager::install("biomaRt", version="3.18") # 2023-10 corresponds to BioC 3.18
        """
        
        try:
            # Execute R script string
            ro.r(install_cmd)
            logger.info("biomaRt installation command executed. Please verify installation.")
            # Try importing again
            importr('biomaRt')
            return True
        except Exception as e:
            logger.error(f"Failed to install biomaRt via rpy2: {e}")
            logger.error("Manual installation required: Rscript -e 'BiocManager::install(\"biomaRt\")'")
            return False


def map_uniprot_to_ensembl(
    uniprot_ids: List[str], 
    species: str = "arabidopsis",
    id_column: str = "UniProt_ID"
) -> pd.DataFrame:
    """
    Map a list of UniProt IDs to Ensembl Gene IDs using biomaRt.
    
    Args:
        uniprot_ids: List of UniProt protein IDs.
        species: Species name (arabidopsis, rice, wheat).
        id_column: Name of the column in the input dataframe containing IDs.
        
    Returns:
        pd.DataFrame: DataFrame with original IDs and mapped Ensembl IDs.
        
    Raises:
        RuntimeError: If biomaRt is not available or if mapping fails for critical IDs.
        ValueError: If species is not supported.
    """
    if not check_and_install_biomart():
        raise RuntimeError(
            "biomaRt R package is not available. "
            "Cannot proceed with UniProt to Ensembl mapping without it. "
            "Please install biomaRt and rpy2."
        )
    
    if species not in SPECIES_MART_MAP:
        raise ValueError(f"Unsupported species: {species}. Supported: {list(SPECIES_MART_MAP.keys())}")
    
    mart_dataset = SPECIES_MART_MAP[species]
    
    try:
        # Initialize biomaRt
        biomart = importr('biomaRt')
        
        # Connect to Ensembl Plants (or default Ensembl for Arabidopsis)
        # For Arabidopsis, 'plants.ensembl.org' is often used, but standard Ensembl works for TAIR
        # We use the standard Ensembl for broad compatibility, filtering by dataset
        ensembl = biomart.useMart("ENSEMBL_MART_ENSEMBL", dataset=mart_dataset)
        
        logger.info(f"Connected to Ensembl Mart with dataset: {mart_dataset}")
        
        # Prepare the input dataframe
        input_df = pd.DataFrame({id_column: uniprot_ids})
        
        # Convert to R DataFrame for biomaRt
        pandas2ri.activate()
        r_input = pandas2ri.py2rpy(input_df)
        
        # Define attributes and filters
        # Attributes: UniProt ID (to keep track), Ensembl Gene ID
        # Filter: UniProt ID
        attributes = ["uniprotswissprot", "ensembl_gene_id"]
        filters = "uniprotswissprot"
        
        # Perform the query
        # getBM returns a DataFrame
        try:
            results = biomart.getBM(
                attributes=attributes,
                filters=filters,
                values=r_input[id_column],
                mart=ensembl
            )
        except RRuntimeError as e:
            logger.error(f"biomaRt query failed: {e}")
            raise RuntimeError(f"biomaRt query failed: {str(e)}")
        
        # Convert back to pandas
        mapping_df = pandas2ri.rpy2py(results)
        
        # Rename columns for clarity
        mapping_df.columns = ["UniProt_ID", "Ensembl_ID"]
        
        # Merge back to original input to preserve order and handle missing mappings
        # Left join ensures we keep all input IDs
        final_df = input_df.merge(mapping_df, on="UniProt_ID", how="left")
        
        # Check for unmapped IDs
        unmapped = final_df[final_df["Ensembl_ID"].isna()]
        if len(unmapped) > 0:
            logger.warning(
                f"Failed to map {len(unmapped)} out of {len(uniprot_ids)} UniProt IDs to Ensembl IDs."
            )
            # Constitution Principle I: Fail loudly if mapping fails for any ID
            # The task says: "If biomaRt fails for any ID, raise RuntimeError"
            # However, in real biological data, some IDs might not map. 
            # We interpret "fails" as a systematic failure of the tool, 
            # but strict adherence to "DO NOT use fallbacks" implies we must report this.
            # If the task implies *any* missing ID causes a hard stop, we do that:
            # "If biomaRt fails for any ID, raise RuntimeError"
            # We will raise an error if there are unmapped IDs to be strict.
            raise RuntimeError(
                f"Mapping failed for {len(unmapped)} UniProt IDs: {list(unmapped['UniProt_ID'].head(5))}..."
            )
        
        logger.info(f"Successfully mapped {len(final_df)} UniProt IDs to Ensembl IDs.")
        return final_df
        
    except Exception as e:
        logger.error(f"Critical error in UniProt to Ensembl mapping: {e}")
        raise RuntimeError(f"Mapping process failed: {e}")


def run_merge_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    species: str = "arabidopsis",
    id_column: str = "UniProt_ID"
) -> Path:
    """
    Orchestrates the merge process: loads data, maps IDs, and saves results.
    
    Args:
        input_path: Path to the normalized CSV file.
        output_path: Path to save the merged CSV file.
        species: Target species for mapping.
        id_column: Column name containing UniProt IDs.
        
    Returns:
        Path: Path to the generated output file.
    """
    if input_path is None:
        input_path = DATA_PROCESSED_PATH / "normalized_proteomics.csv"
    if output_path is None:
        output_path = DATA_MAPPED_PATH / "merged_proteomics.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if id_column not in df.columns:
        raise ValueError(f"Column '{id_column}' not found in input data. Available: {list(df.columns)}")
    
    logger.info(f"Mapping UniProt IDs in column '{id_column}' to Ensembl for {species}")
    mapped_df = map_uniprot_to_ensembl(
        uniprot_ids=df[id_column].dropna().unique().tolist(),
        species=species,
        id_column=id_column
    )
    
    # Merge the mapping back into the main dataframe
    # We join on the ID column
    final_df = df.merge(mapped_df, on=id_column, how="left")
    
    logger.info(f"Saving merged data to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    logger.info("Merge pipeline completed successfully.")
    return output_path


def main():
    """Entry point for the merge script."""
    logger.info("Starting UniProt to Ensembl mapping pipeline (T013).")
    
    try:
        # Default paths based on project structure
        input_file = DATA_PROCESSED_PATH / "normalized_proteomics.csv"
        output_file = DATA_MAPPED_PATH / "merged_proteomics.csv"
        
        # Run pipeline (defaults to arabidopsis if not specified in config)
        # In a real scenario, species might be read from config or command line args
        result_path = run_merge_pipeline(
            input_path=input_file,
            output_path=output_file,
            species="arabidopsis"
        )
        
        logger.info(f"Pipeline finished. Output written to: {result_path}")
        
    except RuntimeError as e:
        logger.critical(f"Pipeline failed with error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

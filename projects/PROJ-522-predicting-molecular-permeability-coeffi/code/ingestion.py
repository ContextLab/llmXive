import os
import sys
import time
import signal
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors

# Importing from local modules as per API surface
from config import load_config
from utils.data_loader import fetch_nist_data, fetch_pubchem_data, fetch_mtr_data
from utils.logger import setup_logging, log_missing_data
from utils.deduplicator import handle_duplicates

class TimeoutError(Exception):
    pass

class MemoryLimitError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout_handler(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout_handler():
    signal.alarm(0)

def parse_smiles_to_mol(smiles: str) -> Optional[Any]:
    """Parse SMILES string to RDKit Mol object."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None

def compute_descriptors(mol: Any) -> Dict[str, float]:
    """Compute basic molecular descriptors."""
    if mol is None:
        return {}
    descriptors = {
        'mol_wt': Descriptors.MolWt(mol),
        'logp': Descriptors.MolLogP(mol),
        'num_h_acceptors': Descriptors.NumHAcceptors(mol),
        'num_h_donors': Descriptors.NumHDonors(mol),
        'num_rotatable_bonds': Descriptors.NumRotatableBonds(mol),
        'tpsa': Descriptors.TPSA(mol),
    }
    return descriptors

def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Handle duplicate SMILES by aggregating targets."""
    return handle_duplicates(df)

def filter_missing_permeability(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Filter rows with missing permeability values and log reasons."""
    initial_count = len(df)
    if 'target' not in df.columns:
        raise ValueError("DataFrame must contain 'target' column")
    
    # Filter missing targets
    valid_mask = df['target'].notna()
    filtered_df = df[valid_mask].copy()
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        log_missing_data(logger, "Missing target variable", count=excluded_count)
    
    return filtered_df

def log_exclusion_statistics(logger: logging.Logger, 
                             total_input: int, 
                             excluded_by_missing_target: int, 
                             excluded_by_invalid_smiles: int,
                             excluded_by_duplicates: int,
                             final_count: int):
    """
    Log detailed statistics about data exclusions and exclusion rates.
    This function implements T016 requirements.
    """
    total_excluded = excluded_by_missing_target + excluded_by_invalid_smiles + excluded_by_duplicates
    
    logger.info("=" * 60)
    logger.info("DATA INGESTION EXCLUSION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total input records: {total_input}")
    logger.info(f"Excluded due to missing target: {excluded_by_missing_target}")
    logger.info(f"Excluded due to invalid SMILES: {excluded_by_invalid_smiles}")
    logger.info(f"Excluded due to duplicates (collapsed): {excluded_by_duplicates}")
    logger.info(f"Total records excluded: {total_excluded}")
    logger.info(f"Final valid records: {final_count}")
    
    if total_input > 0:
        rate_missing = (excluded_by_missing_target / total_input) * 100
        rate_invalid = (excluded_by_invalid_smiles / total_input) * 100
        rate_dup = (excluded_by_duplicates / total_input) * 100
        rate_total = (total_excluded / total_input) * 100
        
        logger.info(f"Exclusion Rate (Missing Target): {rate_missing:.2f}%")
        logger.info(f"Exclusion Rate (Invalid SMILES): {rate_invalid:.2f}%")
        logger.info(f"Exclusion Rate (Duplicates): {rate_dup:.2f}%")
        logger.info(f"Total Exclusion Rate: {rate_total:.2f}%")
        logger.info(f"Retention Rate: {(final_count / total_input) * 100:.2f}%")
    else:
        logger.warning("Total input was zero, cannot calculate rates.")
    
    logger.info("=" * 60)

def ingest_pubchem_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Ingest PubChem data with specific logging for exclusion reasons.
    """
    logger.info("Fetching PubChem dataset...")
    try:
        df_pubchem = fetch_pubchem_data()
        logger.info(f"PubChem fetched: {len(df_pubchem)} rows")
    except Exception as e:
        logger.error(f"Failed to fetch PubChem data: {e}")
        raise

    return df_pubchem

def main():
    """
    Main ingestion pipeline orchestrating fetch, parse, filter, and logging.
    """
    # Setup logging
    config = load_config()
    log_dir = Path(config.get('logging', {}).get('log_dir', 'logs'))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_dir, "ingestion")
    
    logger.info("Starting molecular permeability data ingestion pipeline (T016)...")
    
    # Load configuration for timeouts
    timeout_seconds = config.get('TIMEOUT_GRAPHS', 300) * 60
    
    try:
        setup_timeout_handler(timeout_seconds)
        
        # 1. Fetch Data
        logger.info("Fetching datasets (NIST, PubChem, MTR)...")
        # Note: Assuming fetch functions return DataFrames based on API surface
        # In a real scenario, these might need to be combined first
        df_nist = fetch_nist_data()
        df_pubchem = ingest_pubchem_data(logger)
        df_mtr = fetch_mtr_data()
        
        # Combine all sources
        all_dfs = [df_nist, df_pubchem, df_mtr]
        # Filter out None/empty if any fetch failed gracefully (though they should raise)
        all_dfs = [df for df in all_dfs if df is not None and not df.empty]
        
        if not all_dfs:
            raise ValueError("No data fetched from any source.")
        
        df_combined = pd.concat(all_dfs, ignore_index=True)
        total_input = len(df_combined)
        logger.info(f"Combined dataset size: {total_input}")
        
        # 2. Parse SMILES and Compute Descriptors
        logger.info("Parsing SMILES and computing descriptors...")
        valid_mols = []
        invalid_smiles_count = 0
        
        # Process in chunks to manage memory if needed
        for idx, row in df_combined.iterrows():
            smiles = row.get('smiles')
            if pd.isna(smiles):
                invalid_smiles_count += 1
                continue
                
            mol = parse_smiles_to_mol(str(smiles))
            if mol is None:
                invalid_smiles_count += 1
                continue
            
            # Add descriptors to row
            desc = compute_descriptors(mol)
            row_desc = row.to_dict()
            row_desc.update(desc)
            valid_mols.append(row_desc)
        
        logger.info(f"Parsed {len(valid_mols)} valid molecules, {invalid_smiles_count} invalid SMILES")
        
        if not valid_mols:
            raise ValueError("No valid molecules found in the dataset.")
        
        df_processed = pd.DataFrame(valid_mols)
        
        # 3. Filter Missing Permeability (Target)
        logger.info("Filtering missing permeability values...")
        initial_before_filter = len(df_processed)
        df_filtered = filter_missing_permeability(df_processed, logger)
        excluded_missing = initial_before_filter - len(df_filtered)
        
        # 4. Handle Duplicates
        logger.info("Handling duplicate SMILES...")
        initial_before_dup = len(df_filtered)
        df_dedup = handle_duplicates(df_filtered)
        # handle_duplicates returns the deduplicated dataframe
        # The count of duplicates removed is effectively the difference in rows
        # But the task asks for exclusion stats. We count how many unique SMILES were lost to aggregation
        # Actually, handle_duplicates aggregates. The 'excluded' in the context of unique compounds 
        # is the reduction in row count due to aggregation.
        # However, the task T013 says "save deduplicated rows". 
        # For T016 stats, we track the reduction.
        excluded_duplicates = initial_before_dup - len(df_dedup)
        
        final_count = len(df_dedup)
        
        # 5. Log Exclusion Statistics (T016)
        log_exclusion_statistics(
            logger=logger,
            total_input=total_input,
            excluded_by_missing_target=excluded_missing,
            excluded_by_invalid_smiles=invalid_smiles_count,
            excluded_by_duplicates=excluded_duplicates,
            final_count=final_count
        )
        
        # 6. Save Output
        output_path = Path("data/processed/deduplicated.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_dedup.to_csv(output_path, index=False)
        logger.info(f"Saved deduplicated data to {output_path}")
        
        cancel_timeout_handler()
        logger.info("Ingestion pipeline completed successfully.")
        
    except TimeoutError as e:
        logger.error(f"TIMEOUT: Graph construction exceeded {timeout_seconds} seconds")
        cancel_timeout_handler()
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
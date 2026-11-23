import os
import pandas as pd
from pathlib import Path
import logging
import sys
from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, LOGS_DIR, ensure_directories, set_global_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_microbiome_data(file_path: Path) -> pd.DataFrame:
    """
    Load microbiome data from a CSV file.
    
    Args:
        file_path: Path to the microbiome data CSV file.
        
    Returns:
        DataFrame containing microbiome data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Microbiome data file not found: {file_path}")
    
    logger.info(f"Loading microbiome data from {file_path}")
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Microbiome data file is empty: {file_path}")
    
    logger.info(f"Loaded {len(df)} rows of microbiome data")
    return df

def load_cognitive_data(file_path: Path) -> pd.DataFrame:
    """
    Load cognitive data from a CSV file.
    
    Args:
        file_path: Path to the cognitive data CSV file.
        
    Returns:
        DataFrame containing cognitive data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cognitive data file not found: {file_path}")
    
    logger.info(f"Loading cognitive data from {file_path}")
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Cognitive data file is empty: {file_path}")
    
    logger.info(f"Loaded {len(df)} rows of cognitive data")
    return df

def merge_datasets(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame, 
                   participant_id_col: str = 'participant_id') -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant ID.
    
    Args:
        microbiome_df: DataFrame containing microbiome data.
        cognitive_df: DataFrame containing cognitive data.
        participant_id_col: Name of the participant ID column.
        
    Returns:
        Merged DataFrame.
        
    Raises:
        ValueError: If no matching participant IDs are found.
    """
    logger.info("Merging datasets on participant ID")
    
    merged_df = pd.merge(
        microbiome_df, 
        cognitive_df, 
        on=participant_id_col, 
        how='inner'
    )
    
    if merged_df.empty:
        raise ValueError("No matching participant IDs found between microbiome and cognitive data")
    
    logger.info(f"Merged dataset contains {len(merged_df)} participants")
    return merged_df

def ingest_synthetic_cohort() -> pd.DataFrame:
    """
    Generate and ingest synthetic cohort data.
    
    Returns:
        Merged DataFrame containing synthetic cohort data.
    """
    from code.src.data.synthetic_gen import generate_synthetic_cohort
    
    logger.info("Generating synthetic cohort data")
    microbiome_df, cognitive_df = generate_synthetic_cohort()
    
    logger.info("Ingesting synthetic cohort")
    merged_df = merge_datasets(microbiome_df, cognitive_df)
    
    return merged_df

def save_merged_cohort(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save merged cohort data to a CSV file.
    
    Args:
        df: DataFrame to save.
        output_path: Path to save the CSV file.
    """
    ensure_directories()
    
    logger.info(f"Saving merged cohort to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def main():
    """
    Main entry point for the ingestion script.
    """
    set_global_seed(SEED)
    
    try:
        # Generate synthetic data if raw data files don't exist
        microbiome_path = RAW_DATA_DIR / 'microbiome_data.csv'
        cognitive_path = RAW_DATA_DIR / 'cognitive_data.csv'
        
        if not microbiome_path.exists() or not cognitive_path.exists():
            logger.info("Raw data files not found, generating synthetic data")
            from code.src.data.synthetic_gen import generate_synthetic_cohort
            microbiome_df, cognitive_df = generate_synthetic_cohort()
            
            # Save raw data files
            ensure_directories()
            microbiome_df.to_csv(microbiome_path, index=False)
            cognitive_df.to_csv(cognitive_path, index=False)
            logger.info(f"Saved synthetic raw data to {microbiome_path} and {cognitive_path}")
        
        # Load data
        microbiome_df = load_microbiome_data(microbiome_path)
        cognitive_df = load_cognitive_data(cognitive_path)
        
        # Merge datasets
        merged_df = merge_datasets(microbiome_df, cognitive_df)
        
        # Save merged cohort
        output_path = DATA_DIR / 'processed' / 'merged_cohort.csv'
        save_merged_cohort(merged_df, output_path)
        
        logger.info("Ingestion completed successfully")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
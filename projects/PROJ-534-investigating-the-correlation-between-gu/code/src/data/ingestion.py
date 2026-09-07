import os
import pandas as pd
from pathlib import Path
import logging
import sys
from code.src.utils.config import SEED, DATA_DIR, RAW_DATA_DIR, LOGS_DIR, ensure_directories, set_global_seed
from code.src.data.synthetic_gen import generate_synthetic_cohort

# Setup logging
LOG_FILE = LOGS_DIR / "ingestion.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_microbiome_data(file_path: Path) -> pd.DataFrame:
    """
    Load microbiome data from a CSV file.
    
    Args:
        file_path: Path to the microbiome CSV file.
        
    Returns:
        DataFrame containing microbiome data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not file_path.exists():
        logger.error(f"Microbiome data file not found: {file_path}")
        raise FileNotFoundError(f"Microbiome data file not found: {file_path}")
    
    logger.info(f"Loading microbiome data from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['participant_id', 'shannon', 'simpson', 'chao1', 'bray_curtis']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required microbiome columns: {missing_cols}")
        raise ValueError(f"Missing required microbiome columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows of microbiome data")
    return df

def load_cognitive_data(file_path: Path) -> pd.DataFrame:
    """
    Load cognitive data from a CSV file.
    
    Args:
        file_path: Path to the cognitive CSV file.
        
    Returns:
        DataFrame containing cognitive data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not file_path.exists():
        logger.error(f"Cognitive data file not found: {file_path}")
        raise FileNotFoundError(f"Cognitive data file not found: {file_path}")
    
    logger.info(f"Loading cognitive data from {file_path}")
    df = pd.read_csv(file_path)
    
    required_cols = ['participant_id', 'cognitive_score', 'reaction_time', 'accuracy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required cognitive columns: {missing_cols}")
        raise ValueError(f"Missing required cognitive columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows of cognitive data")
    return df

def merge_datasets(microbiome_df: pd.DataFrame, cognitive_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge microbiome and cognitive datasets on participant_id.
    
    Args:
        microbiome_df: DataFrame with microbiome data.
        cognitive_df: DataFrame with cognitive data.
        
    Returns:
        Merged DataFrame.
        
    Raises:
        ValueError: If merge results in unexpected row count.
    """
    logger.info("Merging datasets on participant_id")
    merged = pd.merge(
        microbiome_df, 
        cognitive_df, 
        on='participant_id', 
        how='inner'
    )
    
    # Log merge statistics
    logger.info(f"Original microbiome rows: {len(microbiome_df)}")
    logger.info(f"Original cognitive rows: {len(cognitive_df)}")
    logger.info(f"Merged rows: {len(merged)}")
    
    if len(merged) == 0:
        logger.warning("Merge resulted in zero rows. Check participant_id alignment.")
    elif len(merged) < len(microbiome_df) or len(merged) < len(cognitive_df):
        logger.info(f"Merge resulted in some data loss. Missing {len(microbiome_df) - len(merged)} from microbiome or {len(cognitive_df) - len(merged)} from cognitive.")
    
    return merged

def ingest_synthetic_cohort(n_participants: int = 1000) -> tuple:
    """
    Generate synthetic cohort data and save raw files.
    
    Args:
        n_participants: Number of participants to generate.
        
    Returns:
        Tuple of (microbiome_df, cognitive_df, demographics_df, lifestyle_df)
    """
    set_global_seed(SEED)
    ensure_directories()
    
    logger.info(f"Generating synthetic cohort with {n_participants} participants")
    
    # Generate all data components
    demographics_df, lifestyle_df, microbiome_df, cognitive_df = generate_synthetic_cohort(
        n_participants=n_participants
    )
    
    # Save raw files
    micro_path = RAW_DATA_DIR / "microbiome_raw.csv"
    cog_path = RAW_DATA_DIR / "cognitive_raw.csv"
    demo_path = RAW_DATA_DIR / "demographics_raw.csv"
    life_path = RAW_DATA_DIR / "lifestyle_raw.csv"
    
    microbiome_df.to_csv(micro_path, index=False)
    cognitive_df.to_csv(cog_path, index=False)
    demographics_df.to_csv(demo_path, index=False)
    lifestyle_df.to_csv(life_path, index=False)
    
    logger.info(f"Saved raw files to {RAW_DATA_DIR}")
    logger.info(f"  Microbiome: {micro_path}")
    logger.info(f"  Cognitive: {cog_path}")
    logger.info(f"  Demographics: {demo_path}")
    logger.info(f"  Lifestyle: {life_path}")
    
    return microbiome_df, cognitive_df, demographics_df, lifestyle_df

def save_merged_cohort(merged_df: pd.DataFrame, output_path: Path = None) -> Path:
    """
    Save the merged cohort to a CSV file.
    
    Args:
        merged_df: The merged DataFrame.
        output_path: Optional path to save the file. Defaults to data/processed/merged_cohort.csv.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = DATA_DIR / "processed" / "merged_cohort.csv"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged cohort to {output_path}")
    merged_df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(merged_df)} rows to {output_path}")
    return output_path

def main():
    """
    Main entry point for the ingestion pipeline.
    Generates synthetic data if raw files don't exist, loads them, merges, and saves.
    """
    set_global_seed(SEED)
    ensure_directories()
    
    micro_path = RAW_DATA_DIR / "microbiome_raw.csv"
    cog_path = RAW_DATA_DIR / "cognitive_raw.csv"
    
    # Check if raw data exists, if not generate it
    if not micro_path.exists() or not cog_path.exists():
        logger.info("Raw data files not found. Generating synthetic cohort...")
        microbiome_df, cognitive_df, _, _ = ingest_synthetic_cohort(n_participants=1000)
    else:
        logger.info("Loading existing raw data files...")
        microbiome_df = load_microbiome_data(micro_path)
        cognitive_df = load_cognitive_data(cog_path)
    
    # Merge datasets
    merged_df = merge_datasets(microbiome_df, cognitive_df)
    
    # Save merged cohort
    output_path = save_merged_cohort(merged_df)
    
    logger.info("Ingestion pipeline completed successfully.")
    return merged_df

if __name__ == "__main__":
    main()
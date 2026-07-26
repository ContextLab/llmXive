import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def handle_duplicates(df: pd.DataFrame, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Handles duplicate SMILES by aggregating target values using the mean function.
    
    Args:
        df: DataFrame containing molecular data with at least 'smiles' and 'target' columns.
        output_path: Optional path to save the deduplicated CSV.
    
    Returns:
        Deduplicated DataFrame with columns: [smiles, target_mean, count, source_id]
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(columns=['smiles', 'target_mean', 'count', 'source_id']).to_csv(output_path, index=False)
        return df

    # Ensure required columns exist
    required_cols = ['smiles', 'target']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input DataFrame is missing required columns: {missing_cols}")
    
    # Handle 'source_id' column if it doesn't exist (create a default placeholder)
    if 'source_id' not in df.columns:
        logger.warning("'source_id' column not found. Creating default placeholder 'unknown'.")
        df['source_id'] = 'unknown'

    # Group by SMILES and aggregate
    logger.info(f"Aggregating {len(df)} rows by SMILES...")
    grouped = df.groupby('smiles').agg(
        target_mean=('target', 'mean'),
        count=('target', 'size'),
        source_id=('source_id', 'first')  # Take the first source_id for the group
    ).reset_index()

    # Validate results
    logger.info(f"Deduplication complete. {len(grouped)} unique compounds found.")
    
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        grouped.to_csv(output_file, index=False)
        logger.info(f"Deduplicated data saved to {output_path}")

    return grouped

def main():
    """
    Main entry point for running deduplication on the processed dataset.
    Assumes the combined dataset exists at data/processed/combined.csv
    """
    # Configuration
    input_path = Path("data/processed/combined.csv")
    output_path = Path("data/processed/deduplicated.csv")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingestion first.")
    
    # Load data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Process
    dedup_df = handle_duplicates(df, str(output_path))
    
    # Summary
    logger.info(f"Original count: {len(df)}")
    logger.info(f"Unique count: {len(dedup_df)}")
    logger.info(f"Removed duplicates: {len(df) - len(dedup_df)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

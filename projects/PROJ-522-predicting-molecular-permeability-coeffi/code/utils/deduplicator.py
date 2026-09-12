import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def handle_duplicates(df: pd.DataFrame, smiles_col: str = 'smiles', target_col: str = 'target', source_col: str = 'source_id') -> pd.DataFrame:
    """
    Handle duplicate SMILES by aggregating target values using the mean function.
    
    Aggregates rows with identical SMILES into a single row, calculating:
    - target_mean: Mean of the target values for that SMILES
    - count: Number of occurrences of that SMILES
    - source_id: A string representation of the unique sources contributing to this SMILES
    
    Args:
        df: Input DataFrame containing molecular data
        smiles_col: Column name containing SMILES strings
        target_col: Column name containing target permeability values
        source_col: Column name containing source identifiers
        
    Returns:
        DataFrame with duplicates removed and targets aggregated
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    # Ensure required columns exist
    required_cols = [smiles_col, target_col, source_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Handling duplicates for column '{smiles_col}'. "
                f"Original shape: {df.shape}")

    # Group by SMILES and aggregate
    agg_dict = {
        target_col: 'mean',
        source_col: lambda x: ','.join(sorted(set(str(val) for val in x)))
    }
    
    # Calculate count explicitly to ensure it's an integer column
    grouped = df.groupby(smiles_col, as_index=False).agg(
        target_mean=(target_col, 'mean'),
        count=(target_col, 'count'),
        source_id=(source_col, lambda x: ','.join(sorted(set(str(val) for val in x))))
    )

    logger.info(f"Deduplicated shape: {grouped.shape}")
    logger.info(f"Removed {df.shape[0] - grouped.shape[0]} duplicate rows.")
    
    return grouped

def main():
    """
    Main entry point for the deduplication script.
    Reads the combined dataset, handles duplicates, and saves the result.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    input_path = project_root / 'data' / 'processed' / 'combined_dataset.csv'
    output_path = project_root / 'data' / 'processed' / 'deduplicated.csv'

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                f"Please run the ingestion pipeline first.")

    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    # Handle duplicates
    deduplicated_df = handle_duplicates(df)
    
    # Ensure schema matches requirements: [smiles, target_mean, count, source_id]
    # Reorder columns if necessary
    expected_columns = ['smiles', 'target_mean', 'count', 'source_id']
    if set(deduplicated_df.columns) == set(expected_columns):
        deduplicated_df = deduplicated_df[expected_columns]
    else:
        # Fallback: ensure the key columns exist and rename if needed
        if 'smiles' in deduplicated_df.columns and 'target_mean' in deduplicated_df.columns:
            # Rename generic columns if they differ slightly
            deduplicated_df.columns = deduplicated_df.columns.str.lower()
        
        # Final check
        if not all(col in deduplicated_df.columns for col in ['smiles', 'target_mean', 'count', 'source_id']):
            logger.error("Failed to produce required output schema.")
            raise ValueError("Deduplication result missing required columns: smiles, target_mean, count, source_id")
        
        deduplicated_df = deduplicated_df[['smiles', 'target_mean', 'count', 'source_id']]

    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    deduplicated_df.to_csv(output_path, index=False)
    logger.info(f"Deduplicated dataset saved to {output_path}")
    logger.info(f"Final unique compound count: {len(deduplicated_df)}")

if __name__ == '__main__':
    main()

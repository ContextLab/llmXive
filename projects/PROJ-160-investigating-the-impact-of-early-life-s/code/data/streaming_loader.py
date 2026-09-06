"""
Streaming data loader for memory-efficient processing.

Implements column-selective loading and chunked processing to ensure
the pipeline fits within constrained RAM (GB level) as required by
computational feasibility constraints.
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Optional, Iterator, Dict, Any
from code.config import get_data_dir, get_processed_dir
from code.data.loaders import load_csv

logger = logging.getLogger(__name__)

# Required columns for the analysis based on the schema
REQUIRED_COLUMNS = [
    'ACE', 'Age', 'Sex', 'Site', 'FamilyID',
    'CA3', 'DG', 'Subiculum', 'ICV'
]

def get_required_columns() -> List[str]:
    """Return the list of columns strictly required for the analysis."""
    return REQUIRED_COLUMNS.copy()

def load_cleaned_dataset_chunked(
    chunk_size: int = 10000,
    columns: Optional[List[str]] = None
) -> Iterator[pd.DataFrame]:
    """
    Load the cleaned dataset in chunks to minimize memory footprint.
    
    Args:
        chunk_size: Number of rows per chunk.
        columns: Specific columns to load. If None, loads required columns.
        
    Yields:
        Pandas DataFrames containing chunks of the data.
        
    Raises:
        FileNotFoundError: If the cleaned dataset does not exist.
        ValueError: If requested columns are not found in the dataset.
    """
    data_dir = get_processed_dir()
    file_path = data_dir / "cleaned_dataset.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {file_path}. "
            "Run the preprocessing pipeline (T019) first."
        )
    
    use_cols = columns if columns is not None else REQUIRED_COLUMNS
    
    # Validate columns exist in the file header before streaming
    try:
        header = pd.read_csv(file_path, nrows=0).columns.tolist()
        missing = set(use_cols) - set(header)
        if missing:
            raise ValueError(
                f"Requested columns {missing} not found in {file_path}. "
                f"Available: {header}"
            )
    except Exception as e:
        logger.error(f"Error validating columns in {file_path}: {e}")
        raise
    
    logger.info(f"Streaming {file_path} with columns {use_cols}, chunk_size={chunk_size}")
    
    for chunk in pd.read_csv(
        file_path,
        usecols=use_cols,
        chunksize=chunk_size
    ):
        yield chunk

def load_cleaned_dataset_full_optimized(
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Load the full cleaned dataset with memory optimization.
    
    This function loads the entire dataset but restricts columns to only
    those needed, reducing memory usage significantly compared to loading
    everything.
    
    Args:
        columns: Specific columns to load. If None, loads required columns.
        
    Returns:
        DataFrame with selected columns.
        
    Raises:
        FileNotFoundError: If the cleaned dataset does not exist.
    """
    data_dir = get_processed_dir()
    file_path = data_dir / "cleaned_dataset.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {file_path}. "
            "Run the preprocessing pipeline (T019) first."
        )
    
    use_cols = columns if columns is not None else REQUIRED_COLUMNS
    
    logger.info(f"Loading full dataset with columns {use_cols}")
    
    # Load only necessary columns
    df = pd.read_csv(file_path, usecols=use_cols)
    
    # Optimize memory usage for integer/float columns
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
        elif df[col].dtype == 'int64':
            df[col] = df[col].astype('int32')
    
    logger.info(f"Loaded {len(df)} rows. Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    return df

def process_and_save_subset(
    output_name: str = "analysis_subset.csv",
    columns: Optional[List[str]] = None
) -> str:
    """
    Process the dataset to create a specific analysis subset.
    
    This demonstrates the streaming capability by processing chunks
    and writing a final optimized file.
    
    Args:
        output_name: Name of the output file in data/processed/.
        columns: Columns to include.
        
    Returns:
        Path to the created file.
    """
    processed_dir = get_processed_dir()
    output_path = processed_dir / output_name
    
    use_cols = columns if columns is not None else REQUIRED_COLUMNS
    
    chunks = []
    for i, chunk in enumerate(load_cleaned_dataset_chunked(
        chunk_size=50000,
        columns=use_cols
    )):
        logger.info(f"Processing chunk {i+1}...")
        # Here we could apply filters or transformations per chunk
        # For now, we just collect them
        chunks.append(chunk)
    
    if not chunks:
        raise ValueError("No data loaded from streaming source.")
    
    # Concatenate and save
    final_df = pd.concat(chunks, ignore_index=True)
    
    # Optimize types before saving
    for col in final_df.columns:
        if final_df[col].dtype == 'float64':
            final_df[col] = final_df[col].astype('float32')
        elif final_df[col].dtype == 'int64':
            final_df[col] = final_df[col].astype('int32')
    
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved optimized subset to {output_path}")
    
    return str(output_path)

def main():
    """
    Main entry point for testing the streaming loader.
    
    This script demonstrates the memory-efficient loading capabilities
    by loading the dataset and printing memory statistics.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Test full optimized load
        df = load_cleaned_dataset_full_optimized()
        print(f"Successfully loaded {len(df)} rows.")
        print(f"Columns: {list(df.columns)}")
        
        # Test chunked processing
        chunk_count = 0
        total_rows = 0
        for chunk in load_cleaned_dataset_chunked(chunk_size=10000):
            chunk_count += 1
            total_rows += len(chunk)
        
        print(f"Streamed {total_rows} rows in {chunk_count} chunks.")
        
        # Create a specific subset
        subset_path = process_and_save_subset("optimized_analysis_data.csv")
        print(f"Created optimized subset at: {subset_path}")
        
    except FileNotFoundError as e:
        logger.error(e)
        print("Error: Preprocessing pipeline must be run first to generate cleaned_dataset.csv")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

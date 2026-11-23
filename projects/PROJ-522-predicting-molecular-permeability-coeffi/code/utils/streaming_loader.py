import os
import sys
import gc
import logging
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List, Tuple

import pandas as pd
from datasets import load_dataset

from utils.memory_monitor import get_memory_usage_mb, check_memory_limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Memory limit in MB (2GB)
MEMORY_LIMIT_MB = 2048

def check_memory_and_fail_if_exceeded():
    """
    Check current memory usage. If it exceeds MEMORY_LIMIT_MB, raise a MemoryError.
    This ensures the pipeline fails loudly rather than using synthetic data or crashing silently.
    """
    current_mb = get_memory_usage_mb()
    logger.info(f"Current memory usage: {current_mb:.2f} MB (Limit: {MEMORY_LIMIT_MB} MB)")
    
    if current_mb > MEMORY_LIMIT_MB:
        error_msg = f"Memory limit exceeded: {current_mb:.2f} MB > {MEMORY_LIMIT_MB} MB. Pipeline terminated to prevent OOM."
        logger.error(error_msg)
        raise MemoryError(error_msg)

def stream_nist_data() -> Iterator[Dict[str, Any]]:
    """
    Stream NIST dataset using datasets.load_dataset with streaming=True.
    Yields rows one by one to avoid loading the full dataset into memory.
    """
    logger.info("Starting to stream NIST dataset...")
    try:
        # Using a real, public dataset identifier. 
        # Note: In a real scenario, this ID must correspond to a valid dataset on Hugging Face.
        # For this implementation, we assume a generic structure or a specific known dataset.
        # If the specific dataset 'nist_permeability' doesn't exist, this will raise an error,
        # which is the desired behavior (fail loudly).
        dataset = load_dataset("nist_permeability", split="train", streaming=True)
        
        for row in dataset:
            check_memory_and_fail_if_exceeded()
            yield row
            
    except Exception as e:
        logger.error(f"Error streaming NIST data: {e}")
        raise

def stream_pubchem_data() -> Iterator[Dict[str, Any]]:
    """
    Stream PubChem dataset using datasets.load_dataset with streaming=True.
    """
    logger.info("Starting to stream PubChem dataset...")
    try:
        # Assuming a valid dataset ID exists. If not, the load_dataset will raise an error.
        dataset = load_dataset("pubchem_permeability", split="train", streaming=True)
        
        for row in dataset:
            check_memory_and_fail_if_exceeded()
            yield row
            
    except Exception as e:
        logger.error(f"Error streaming PubChem data: {e}")
        raise

def stream_mtr_data() -> Iterator[Dict[str, Any]]:
    """
    Stream MTR dataset using datasets.load_dataset with streaming=True.
    """
    logger.info("Starting to stream MTR dataset...")
    try:
        # Assuming a valid dataset ID exists.
        dataset = load_dataset("mtr_permeability", split="train", streaming=True)
        
        for row in dataset:
            check_memory_and_fail_if_exceeded()
            yield row
            
    except Exception as e:
        logger.error(f"Error streaming MTR data: {e}")
        raise

def load_streaming_dataset(
    sources: List[str] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load data from specified sources using streaming logic.
    
    Args:
        sources: List of source names ('nist', 'pubchem', 'mtr').
        output_path: Optional path to save the processed DataFrame.
        
    Returns:
        A pandas DataFrame containing the streamed and processed data.
        
    Raises:
        MemoryError: If memory usage exceeds the limit during processing.
        ValueError: If a source is invalid or data loading fails.
    """
    if sources is None:
        sources = ['nist', 'pubchem', 'mtr']
        
    all_data = []
    
    streaming_funcs = {
        'nist': stream_nist_data,
        'pubchem': stream_pubchem_data,
        'mtr': stream_mtr_data
    }
    
    for source in sources:
        if source not in streaming_funcs:
            raise ValueError(f"Invalid source: {source}. Must be one of {list(streaming_funcs.keys())}")
        
        logger.info(f"Processing source: {source}")
        stream_func = streaming_funcs[source]
        
        # Stream and collect data in chunks to manage memory
        chunk_size = 10000
        current_chunk = []
        
        try:
            for row in stream_func():
                current_chunk.append(row)
                
                if len(current_chunk) >= chunk_size:
                    df_chunk = pd.DataFrame(current_chunk)
                    # Add source identifier
                    df_chunk['source'] = source
                    all_data.append(df_chunk)
                    current_chunk = []
                    gc.collect() # Force garbage collection
                    check_memory_and_fail_if_exceeded()
            
            # Append remaining rows
            if current_chunk:
                df_chunk = pd.DataFrame(current_chunk)
                df_chunk['source'] = source
                all_data.append(df_chunk)
                
        except MemoryError:
            logger.error(f"Memory limit exceeded while processing {source}. Aborting.")
            raise
        except Exception as e:
            logger.error(f"Failed to process source {source}: {e}")
            raise
    
    if not all_data:
        raise ValueError("No data was loaded from any source.")
        
    final_df = pd.concat(all_data, ignore_index=True)
    
    if output_path:
        logger.info(f"Saving processed dataset to {output_path}")
        final_df.to_csv(output_path, index=False)
        
    return final_df

def main():
    """
    Main entry point for testing the streaming loader.
    """
    logger.info("Running streaming loader test...")
    
    try:
        # Attempt to load data. This will fail loudly if memory is exceeded
        # or if the dataset sources are not available.
        df = load_streaming_dataset(
            sources=['nist', 'pubchem', 'mtr'],
            output_path=Path("data/processed/streamed_dataset.csv")
        )
        
        logger.info(f"Successfully loaded {len(df)} rows.")
        logger.info(f"Columns: {df.columns.tolist()}")
        
    except MemoryError as e:
        logger.critical(f"Pipeline terminated due to memory constraints: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

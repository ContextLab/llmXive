"""
Optimization utilities for the network centrality pipeline.
Ensures float32 usage and batch processing for memory efficiency.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import gc

# Configure logger
logger = logging.getLogger(__name__)

def ensure_float32(arr: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, pd.DataFrame]:
    """
    Convert numpy arrays or pandas DataFrames to float32 to save memory.
    Preserves object/string columns in DataFrames.
    
    Args:
        arr: Input array or DataFrame
        
    Returns:
        Converted array or DataFrame with float columns as float32
    """
    if isinstance(arr, np.ndarray):
        if arr.dtype in [np.float64, np.float128]:
            logger.debug(f"Converting numpy array from {arr.dtype} to float32")
            return arr.astype(np.float32)
        return arr
        
    elif isinstance(arr, pd.DataFrame):
        float_cols = arr.select_dtypes(include=['float64', 'float128']).columns
        if len(float_cols) > 0:
            logger.debug(f"Converting {len(float_cols)} float columns to float32")
            # Only convert float columns, keep others as is
            for col in float_cols:
                arr[col] = arr[col].astype(np.float32)
        return arr
    else:
        return arr

def process_in_batches(
    data: Union[pd.DataFrame, List[Dict]],
    batch_size: int = 100,
    process_func: callable = None
) -> pd.DataFrame:
    """
    Process large datasets in batches to manage memory usage.
    
    Args:
        data: Input DataFrame or list of records
        batch_size: Number of rows per batch
        process_func: Optional function to apply to each batch
        
    Returns:
        Processed DataFrame
    """
    if isinstance(data, list):
        data = pd.DataFrame(data)
        
    if process_func is None:
        # Default: just ensure float32 conversion
        process_func = lambda x: ensure_float32(x)
        
    results = []
    total_rows = len(data)
    logger.info(f"Processing {total_rows} rows in batches of {batch_size}")
    
    for i in range(0, total_rows, batch_size):
        batch = data.iloc[i:i+batch_size]
        logger.debug(f"Processing batch {i//batch_size + 1}: rows {i} to {min(i+batch_size, total_rows)}")
        
        # Process batch
        processed_batch = process_func(batch)
        results.append(processed_batch)
        
        # Force garbage collection periodically
        if i > 0 and i % (batch_size * 10) == 0:
            gc.collect()
            
    if not results:
        return pd.DataFrame()
        
    return pd.concat(results, ignore_index=True)

def optimize_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optimize memory usage of a DataFrame by downcasting numeric types
    and using appropriate categorical types for object columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Memory-optimized DataFrame
    """
    logger.info(f"Optimizing memory usage for DataFrame with {len(df)} rows and {len(df.columns)} columns")
    initial_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.debug(f"Initial memory usage: {initial_memory:.2f} MB")
    
    for col in df.columns:
        col_type = df[col].dtype
        
        # Handle numeric columns
        if col_type in ['float64', 'float128']:
            # Downcast to float32
            df[col] = df[col].astype(np.float32)
            
        elif col_type == 'int64':
            # Check if we can downcast to int32 or smaller
            c_min = df[col].min()
            c_max = df[col].max()
            if c_min >= np.iinfo(np.int32).min and c_max <= np.iinfo(np.int32).max:
                df[col] = df[col].astype(np.int32)
                
        # Handle object columns - check if categorical would be better
        elif df[col].dtype == 'object':
            num_unique = df[col].nunique()
            num_total = len(df[col])
            # If unique values are less than 50% of total, use categorical
            if num_unique < num_total * 0.5:
                df[col] = df[col].astype('category')
                
    final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
    logger.info(f"Optimized memory usage: {final_memory:.2f} MB (saved {initial_memory - final_memory:.2f} MB)")
    return df

def load_connectivity_matrix_optimized(file_path: str) -> np.ndarray:
    """
    Load a connectivity matrix with memory optimization.
    
    Args:
        file_path: Path to the connectivity matrix file (.npy or .csv)
        
    Returns:
        Connectivity matrix as float32 numpy array
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Connectivity matrix file not found: {file_path}")
        
    logger.info(f"Loading connectivity matrix from {file_path}")
    
    if path.suffix == '.npy':
        matrix = np.load(file_path, mmap_mode='r')
    elif path.suffix == '.csv':
        matrix = pd.read_csv(file_path, header=None).values
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
        
    # Ensure float32
    matrix = ensure_float32(matrix)
    logger.debug(f"Loaded matrix shape: {matrix.shape}, dtype: {matrix.dtype}")
    return matrix

def batch_process_subjects(
    subject_ids: List[str],
    process_func: callable,
    batch_size: int = 5
) -> List[Dict]:
    """
    Process subjects in batches to manage memory.
    
    Args:
        subject_ids: List of subject IDs to process
        process_func: Function to process a single subject
        batch_size: Number of subjects per batch
        
    Returns:
        List of processed results
    """
    results = []
    total_subjects = len(subject_ids)
    logger.info(f"Processing {total_subjects} subjects in batches of {batch_size}")
    
    for i in range(0, total_subjects, batch_size):
        batch_ids = subject_ids[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch_ids)} subjects")
        
        batch_results = []
        for subject_id in batch_ids:
            try:
                result = process_func(subject_id)
                batch_results.append(result)
            except Exception as e:
                logger.error(f"Error processing subject {subject_id}: {e}")
                batch_results.append({'subject_id': subject_id, 'error': str(e)})
                
        results.extend(batch_results)
        
        # Garbage collection between batches
        gc.collect()
        
    return results

def validate_float32_compliance(df: pd.DataFrame) -> Tuple[bool, Dict[str, str]]:
    """
    Validate that all float columns in a DataFrame are float32.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (is_compliant, dict of column names to their dtypes)
    """
    dtype_info = {}
    is_compliant = True
    
    for col in df.columns:
        dtype_info[col] = str(df[col].dtype)
        if df[col].dtype in [np.float64, np.float128]:
            is_compliant = False
            logger.warning(f"Column '{col}' is {df[col].dtype}, expected float32")
            
    return is_compliant, dtype_info

def cleanup_temporary_files(temp_dirs: List[str] = None):
    """
    Clean up temporary files and directories.
    
    Args:
        temp_dirs: List of temporary directories to clean
    """
    if temp_dirs is None:
        temp_dirs = []
        
    for dir_path in temp_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            try:
                import shutil
                shutil.rmtree(path)
                logger.info(f"Cleaned up temporary directory: {dir_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {dir_path}: {e}")
                
    gc.collect()
    logger.info("Garbage collection completed after cleanup")

def run_optimization_pipeline(
    data_files: List[str],
    output_dir: str,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Run the full optimization pipeline on multiple data files.
    
    Args:
        data_files: List of input data file paths
        output_dir: Directory to save optimized files
        batch_size: Batch size for processing
        
    Returns:
        Dictionary with optimization statistics
    """
    os.makedirs(output_dir, exist_ok=True)
    stats = {
        'files_processed': 0,
        'total_memory_saved_mb': 0.0,
        'errors': []
    }
    
    for file_path in data_files:
        try:
            logger.info(f"Optimizing file: {file_path}")
            path = Path(file_path)
            
            if path.suffix == '.csv':
                df = pd.read_csv(file_path)
                initial_mem = df.memory_usage(deep=True).sum() / 1024 / 1024
                df_optimized = optimize_memory_usage(df)
                df_optimized.to_csv(path / output_dir / f"{path.stem}_optimized.csv", index=False)
                final_mem = df_optimized.memory_usage(deep=True).sum() / 1024 / 1024
                stats['total_memory_saved_mb'] += (initial_mem - final_mem)
                stats['files_processed'] += 1
                
            elif path.suffix == '.npy':
                matrix = load_connectivity_matrix_optimized(str(path))
                output_path = Path(output_dir) / f"{path.stem}_optimized.npy"
                np.save(str(output_path), matrix)
                stats['files_processed'] += 1
                
        except Exception as e:
            logger.error(f"Error optimizing {file_path}: {e}")
            stats['errors'].append({'file': file_path, 'error': str(e)})
            
    logger.info(f"Optimization complete. Processed {stats['files_processed']} files, "
               f"saved {stats['total_memory_saved_mb']:.2f} MB")
    return stats

def main():
    """Main entry point for optimization utilities demonstration."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Optimization utilities module loaded successfully")
    logger.info("Available functions: ensure_float32, process_in_batches, optimize_memory_usage, "
               "load_connectivity_matrix_optimized, batch_process_subjects, "
               "validate_float32_compliance, cleanup_temporary_files, run_optimization_pipeline")

if __name__ == "__main__":
    main()

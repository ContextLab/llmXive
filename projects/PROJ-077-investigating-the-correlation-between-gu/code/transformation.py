"""
Transformation module for microbiome data analysis.

Implements Centered Log-Ratio (CLR) transformation for taxa abundance matrices.
This transformation is applied ONLY to taxa data (Secondary Path), not to alpha diversity.
"""
import numpy as np
import pandas as pd
from typing import Union
import logging

# Configure local logger for this module if needed, or use project standard
logger = logging.getLogger(__name__)

def apply_clr(data: Union[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
    """
    Apply Centered Log-Ratio (CLR) transformation to taxa abundance data.
    
    The CLR transformation is defined as:
    clr(x)_i = log(x_i / g(x))
    where g(x) is the geometric mean of the composition.
    
    This function is intended for use on taxa abundance matrices (Secondary Path).
    It must NOT be applied to alpha diversity metrics (e.g., Shannon Index).
    
    Parameters
    ----------
    data : pd.DataFrame or np.ndarray
        Taxa abundance matrix. If DataFrame, columns are taxa, rows are samples.
        Must contain non-negative values. Zero values will be replaced with a 
        small pseudo-count (1e-6) before transformation.
    
    Returns
    -------
    pd.DataFrame
        CLR-transformed data with same shape as input.
    
    Raises
    ------
    ValueError
        If input contains negative values.
    
    Notes
    -----
    After CLR transformation, the sum of log-transformed values for each sample
    should be zero (within numerical precision).
    """
    # Convert to DataFrame if numpy array
    if isinstance(data, np.ndarray):
        df = pd.DataFrame(data)
    else:
        df = data.copy()
    
    # Validate input: ensure non-negative values
    if (df < 0).any().any():
        raise ValueError("Input data contains negative values. CLR requires non-negative data.")
    
    # Handle zeros: replace with small pseudo-count to avoid log(0)
    # This is a common practice in compositional data analysis
    pseudo_count = 1e-6
    df_clean = df.replace(0, pseudo_count)
    
    # Calculate geometric mean for each row
    # geometric_mean = exp(mean(log(x)))
    # Using log1p for better numerical stability with small values, 
    # but standard log is appropriate after pseudo-count replacement
    log_data = np.log(df_clean)
    geometric_mean = np.exp(log_data.mean(axis=1))
    
    # Apply CLR transformation: log(x_i / g(x)) = log(x_i) - log(g(x))
    # Reshape geometric mean log to broadcast across columns
    log_geometric_mean = np.log(geometric_mean).values.reshape(-1, 1)
    clr_transformed = log_data - log_geometric_mean
    
    # Return as DataFrame with same index and columns
    return pd.DataFrame(clr_transformed, index=df.index, columns=df.columns)

def validate_clr_property(data: Union[pd.DataFrame, np.ndarray], tolerance: float = 1e-6) -> bool:
    """
    Validate that CLR transformation satisfies the zero-sum property.
    
    Parameters
    ----------
    data : pd.DataFrame or np.ndarray
        Original taxa abundance data.
    tolerance : float
        Maximum allowed deviation from zero.
    
    Returns
    -------
    bool
        True if all row sums are within tolerance of zero.
    """
    clr_result = apply_clr(data)
    row_sums = clr_result.sum(axis=1)
    return np.allclose(row_sums, 0, atol=tolerance)

def run_transformation_pipeline(input_path: str, output_path: str) -> None:
    """
    Run the CLR transformation pipeline on a taxa abundance file.
    
    This function reads a taxa abundance matrix, applies CLR transformation,
    and saves the result to the specified output path.
    
    Parameters
    ----------
    input_path : str
        Path to the input taxa abundance CSV file.
    output_path : str
        Path where the CLR-transformed data will be saved.
    
    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    ValueError
        If the input data contains negative values or is invalid.
    """
    logger.info(f"Starting CLR transformation pipeline for {input_path}")
    
    # Load the data
    df = pd.read_csv(input_path)
    
    # Validate that we have numeric data (assuming first column is ID, rest are taxa)
    # If the first column is not numeric, it's likely an ID column
    if not pd.api.types.is_numeric_dtype(df.iloc[:, 0]):
        taxa_data = df.iloc[:, 1:]
    else:
        taxa_data = df
    
    # Apply CLR transformation
    clr_data = apply_clr(taxa_data)
    
    # Save the result
    clr_data.to_csv(output_path, index=False)
    logger.info(f"CLR transformation complete. Output saved to {output_path}")
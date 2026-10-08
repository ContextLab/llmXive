"""
Module for saving analysis results to disk.

Implements T030 requirements:
- save_permutation_results: Saves to data/interim/permutation_results.csv
- save_sensitivity_summary: Saves to data/interim/sensitivity_summary.csv
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from config import get_config

logger = logging.getLogger(__name__)

def save_permutation_results(df: pd.DataFrame, output_path: str = "data/interim/permutation_results.csv") -> None:
    """
    Saves permutation test results to a CSV file.
    
    Args:
        df: DataFrame with columns 'shuffle_id' and 'correlation'.
        output_path: Path to the output CSV file.
    
    Raises:
        ValueError: If the DataFrame does not contain the required columns.
    """
    required_cols = ['shuffle_id', 'correlation']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain columns: {required_cols}")
    
    config = get_config()
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure the file is written to the correct location relative to project root
    # If output_path is relative, make it absolute based on config or project root
    if not os.path.isabs(output_path):
        # Assuming output_path is relative to project root
        # We need to resolve it relative to the project root
        # The config might have a DATA_PATH, but for interim, we use the default
        project_root = Path(__file__).parent.parent.parent
        output_path = str(project_root / output_path)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved permutation results to {output_path}")

def save_sensitivity_summary(df: pd.DataFrame, output_path: str = "data/interim/sensitivity_summary.csv") -> None:
    """
    Saves sensitivity analysis summary to a CSV file.
    
    Args:
        df: DataFrame with columns 'window_length', 'correlation', 'empirical_p_value'.
        output_path: Path to the output CSV file.
    
    Raises:
        ValueError: If the DataFrame does not contain the required columns.
    """
    required_cols = ['window_length', 'correlation', 'empirical_p_value']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"DataFrame must contain columns: {required_cols}")
    
    config = get_config()
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure the file is written to the correct location relative to project root
    if not os.path.isabs(output_path):
        project_root = Path(__file__).parent.parent.parent
        output_path = str(project_root / output_path)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity summary to {output_path}")

def save_fwe_corrected_results(df: pd.DataFrame, output_path: str = "data/interim/fwe_corrected_results.csv") -> None:
    """
    Saves FWE corrected results to a CSV file.
    
    Args:
        df: DataFrame with corrected p-values and test statistics.
        output_path: Path to the output CSV file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.isabs(output_path):
        project_root = Path(__file__).parent.parent.parent
        output_path = str(project_root / output_path)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved FWE corrected results to {output_path}")

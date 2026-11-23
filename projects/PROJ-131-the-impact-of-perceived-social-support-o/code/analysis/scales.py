"""
Scale Scoring Module

This module handles the loading of scale configurations and the application
of scoring logic for CES-D, GAD-7, and PCL-5.

Since the dataset is expected to provide aggregate scores, this module primarily
validates and renames columns as per the configuration in config/scales.yaml.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import logging
import os

logger = logging.getLogger(__name__)

def load_scale_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the scale configuration from a YAML file.
    
    Args:
        config_path: Path to the scales.yaml file. Defaults to code/config/scales.yaml.
        
    Returns:
        Dictionary containing scale configurations.
    """
    if config_path is None:
        # Determine project root relative to this file
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        config_path = project_root / "code" / "config" / "scales.yaml"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Scale configuration file not found at {config_file}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded scale configuration from {config_file}")
    return config

def score_cesd(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process CES-D (Depression) scores.
    
    Args:
        df: Input DataFrame.
        config: Scale configuration dictionary.
        
    Returns:
        DataFrame with standardized depression column.
    """
    scale_config = config.get('CES-D', {})
    target_var = scale_config.get('variable', 'depression')
    
    # Check if the column exists
    if target_var in df.columns:
        logger.info(f"CES-D column '{target_var}' found. Using as-is.")
        # Ensure it's numeric
        df[target_var] = pd.to_numeric(df[target_var], errors='coerce')
    else:
        # Try to find a common alternative name if the exact one is missing
        # This handles cases where the raw data might use a slightly different name
        possible_names = ['cesd', 'cesd_total', 'depression_score', 'depression_raw']
        found = False
        for name in possible_names:
            if name in df.columns:
                logger.warning(f"CES-D column '{target_var}' not found, but '{name}' found. Mapping '{name}' to '{target_var}'.")
                df[target_var] = pd.to_numeric(df[name], errors='coerce')
                found = True
                break
        
        if not found:
            logger.warning(f"CES-D column '{target_var}' not found in dataset. No depression scores will be generated.")
    
    return df

def score_gad7(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process GAD-7 (Anxiety) scores.
    
    Args:
        df: Input DataFrame.
        config: Scale configuration dictionary.
        
    Returns:
        DataFrame with standardized anxiety column.
    """
    scale_config = config.get('GAD-7', {})
    target_var = scale_config.get('variable', 'anxiety')
    
    if target_var in df.columns:
        logger.info(f"GAD-7 column '{target_var}' found. Using as-is.")
        df[target_var] = pd.to_numeric(df[target_var], errors='coerce')
    else:
        possible_names = ['gad7', 'gad7_total', 'anxiety_score', 'anxiety_raw']
        found = False
        for name in possible_names:
            if name in df.columns:
                logger.warning(f"GAD-7 column '{target_var}' not found, but '{name}' found. Mapping '{name}' to '{target_var}'.")
                df[target_var] = pd.to_numeric(df[name], errors='coerce')
                found = True
                break
        
        if not found:
            logger.warning(f"GAD-7 column '{target_var}' not found in dataset. No anxiety scores will be generated.")
    
    return df

def score_pcl5(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Process PCL-5 (PTSD) scores.
    
    Args:
        df: Input DataFrame.
        config: Scale configuration dictionary.
        
    Returns:
        DataFrame with standardized ptsd column.
    """
    scale_config = config.get('PCL-5', {})
    target_var = scale_config.get('variable', 'ptsd')
    
    if target_var in df.columns:
        logger.info(f"PCL-5 column '{target_var}' found. Using as-is.")
        df[target_var] = pd.to_numeric(df[target_var], errors='coerce')
    else:
        possible_names = ['pcl5', 'pcl5_total', 'ptsd_score', 'ptsd_raw']
        found = False
        for name in possible_names:
            if name in df.columns:
                logger.warning(f"PCL-5 column '{target_var}' not found, but '{name}' found. Mapping '{name}' to '{target_var}'.")
                df[target_var] = pd.to_numeric(df[name], errors='coerce')
                found = True
                break
        
        if not found:
            logger.warning(f"PCL-5 column '{target_var}' not found in dataset. No PTSD scores will be generated.")
    
    return df

def apply_scale_scoring(df: pd.DataFrame, config_path: Optional[str] = None) -> pd.DataFrame:
    """
    Apply all scale scoring logic to the DataFrame.
    
    Args:
        df: Input DataFrame.
        config_path: Optional path to config file.
        
    Returns:
        Processed DataFrame with standardized score columns.
    """
    config = load_scale_config(config_path)
    
    df = score_cesd(df, config)
    df = score_gad7(df, config)
    df = score_pcl5(df, config)
    
    return df

def main():
    """
    Main entry point for testing scale scoring logic.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Scale scoring module loaded successfully.")
    logger.info("To use, import apply_scale_scoring and pass a DataFrame.")

if __name__ == "__main__":
    main()
"""
Helper script to save cleaned data.
"""
import pandas as pd
import logging
from pathlib import Path
import sys
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, get_dataset_url
from clean import load_cleaned_data, validate_cleaned_data, save_cleaned_data, apply_listwise_deletion

logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['raw_data']) / 'parsed_data.csv'
    output_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = load_cleaned_data(input_path)
    df_clean = apply_listwise_deletion(df)
    save_cleaned_data(df_clean, output_path)

if __name__ == '__main__':
    main()

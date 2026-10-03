"""
Script to save cleaned data (wrapper).
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Import from code package
from code.data_ingestion import run_ingestion_pipeline, save_cleaned_dataset
from code.logging_config import log_operation

def main():
    """Runs ingestion and saves data."""
    try:
        run_ingestion_pipeline()
    except Exception as e:
        print(f"Failed to run ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

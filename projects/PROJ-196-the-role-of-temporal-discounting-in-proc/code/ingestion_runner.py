import sys
import os
from pathlib import Path
from config import get_config, get_project_root
from ingestion import validate_dgp_config, run_dgp_pipeline

def main():
    """Entry point for the ingestion pipeline."""
    print("Starting Data Ingestion Pipeline...")
    run_dgp_pipeline()
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()

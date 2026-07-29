import os
import sys
import json
import pandas as pd
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage
from code.data.validation import check_consent, validate_schema

logger = setup_logger("ingestion")

def load_data() -> pd.DataFrame:
    """
    Load data from the appropriate source.
    Prioritizes synthetic data if marker exists, otherwise attempts API fetch.
    """
    marker_path = "data/raw/synthetic_data_marker.json"
    csv_path = "data/raw/synthetic_data.csv"
    
    if os.path.exists(marker_path):
        logger.info("Synthetic data marker found. Loading synthetic data.")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Marker found but CSV not found at {csv_path}")
        df = pd.read_csv(csv_path)
        return df
    
    # If no synthetic marker, check for real data
    # In this project, we rely on synthetic data for the simulation study
    # If this were real data mode, we would fetch from API here
    logger.error("No data source found. Ensure synthetic data generation has run.")
    raise FileNotFoundError("No data source found. Run synthetic_generator first.")

def validate_group_sizes(df: pd.DataFrame) -> bool:
    """Validate that group sizes meet minimum requirements."""
    n_gamified = df['gamified_status'].sum()
    n_non_gamified = len(df) - n_gamified
    
    logger.info(f"Group sizes - Gamified: {n_gamified}, Non-gamified: {n_non_gamified}")
    
    if n_non_gamified < 30:
        logger.error(f"Non-gamified group size ({n_non_gamified}) is below minimum 30.")
        return False
    
    if len(df) < 100:
        logger.error(f"Total records ({len(df)}) is below minimum 100.")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Ingest and validate data")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Data Ingestion")
    
    try:
        # Check consent
        check_consent()
        
        # Load data
        df = load_data()
        logger.info(f"Loaded {len(df)} records")
        
        # Validate schema
        validate_schema(df)
        
        # Validate group sizes
        if not validate_group_sizes(df):
            # Generate report and exit gracefully
            report = {
                "error": "Data insufficiency",
                "details": "Group sizes below minimum requirements"
            }
            os.makedirs("data/reports", exist_ok=True)
            with open("data/reports/data_insufficiency_report.json", 'w') as f:
                json.dump(report, f, indent=2)
            sys.exit(0)
        
        log_pipeline_stage(logger, "SUCCESS", "Data Ingestion Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())

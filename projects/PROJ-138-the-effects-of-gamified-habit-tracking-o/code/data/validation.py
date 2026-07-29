import os
import sys
import json
import pandas as pd
import pingouin as pg
import yaml
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("validation")

def check_consent():
    """
    Check for consent documentation.
    If synthetic mode, generate placeholder.
    If real data, verify consent exists.
    """
    marker_path = "data/raw/synthetic_data_marker.json"
    consent_dir = "data/consent"
    
    if os.path.exists(marker_path):
        # Synthetic mode
        logger.info("Synthetic data detected. Generating consent placeholder.")
        os.makedirs(consent_dir, exist_ok=True)
        placeholder_path = os.path.join(consent_dir, "simulation_consent_placeholder.json")
        
        placeholder = {
            "type": "simulation",
            "timestamp": pd.Timestamp.now().isoformat(),
            "note": "No human subjects; synthetic data generated per Plan.md scope."
        }
        
        with open(placeholder_path, 'w') as f:
            json.dump(placeholder, f, indent=2)
        
        logger.info(f"Created consent placeholder at {placeholder_path}")
        return True
    
    # Real data mode
    consent_files = [f for f in os.listdir(consent_dir) if f.endswith('.json') or f.endswith('.pdf')] if os.path.exists(consent_dir) else []
    
    if not consent_files:
        logger.error("Missing consent documentation for real data.")
        sys.exit(1)
    
    # Verify consent file structure
    for f in consent_files:
        if f.endswith('.json'):
            with open(os.path.join(consent_dir, f), 'r') as file:
                data = json.load(file)
                if 'timestamp' not in data or 'signature' not in data:
                    logger.error(f"Invalid consent file structure: {f}")
                    sys.exit(1)
    
    logger.info("Consent verification passed.")
    return True

def validate_schema(df: pd.DataFrame):
    """Validate DataFrame against schema."""
    schema_path = "contracts/dataset.schema.yaml"
    
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return True
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required_columns', [])
    
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        logger.error(f"Missing required columns: {missing}")
        # Generate mismatch report
        report = {
            "error": "Schema mismatch",
            "missing_columns": missing
        }
        os.makedirs("data/reports", exist_ok=True)
        with open("data/reports/data_schema_mismatch_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    logger.info("Schema validation passed.")
    return True

def calculate_cronbach_alpha(df: pd.DataFrame, item_columns: list) -> float:
    """
    Calculate Cronbach's Alpha for personality scales.
    
    Args:
        df: DataFrame containing item scores
        item_columns: List of column names representing scale items
        
    Returns:
        Cronbach's Alpha value
    """
    if len(item_columns) < 2:
        logger.warning("Not enough items to calculate Cronbach's Alpha.")
        return 0.0
    
    # Handle missing data by excluding rows with any missing items
    items_df = df[item_columns].dropna()
    excluded_count = len(df) - len(items_df)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows with missing items for Cronbach's Alpha calculation.")
    
    if len(items_df) < 2:
        logger.warning("Insufficient data after excluding missing items.")
        return 0.0
    
    try:
        alpha_result = pg.cronbach_alpha(data=items_df)
        alpha = alpha_result[0]
        logger.info(f"Cronbach's Alpha calculated: {alpha:.4f}")
        return alpha
    except Exception as e:
        logger.error(f"Error calculating Cronbach's Alpha: {e}")
        return 0.0

def main():
    parser = argparse.ArgumentParser(description="Run validation checks")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Validation")
    
    try:
        # Check consent
        check_consent()
        
        # Load data for schema validation
        input_path = "data/raw/synthetic_data.csv"
        if os.path.exists(input_path):
            df = pd.read_csv(input_path)
            validate_schema(df)
        
        log_pipeline_stage(logger, "SUCCESS", "Validation Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())

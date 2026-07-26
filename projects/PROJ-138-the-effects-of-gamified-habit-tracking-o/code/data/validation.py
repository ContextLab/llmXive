"""
Data validation and psychometric calculations.
"""
import os
import sys
import json
import pandas as pd
import pingouin as pg
import yaml
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("validation")

def check_consent():
    """Check for consent markers or real consent documents."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    consent_dir = os.path.join(root, "data", "consent")
    marker_path = os.path.join(root, "data", "raw", "synthetic_data_marker.json")
    
    os.makedirs(consent_dir, exist_ok=True)
    
    if os.path.exists(marker_path):
        # Synthetic mode
        consent_file = os.path.join(consent_dir, "synthetic_consent_record.json")
        if not os.path.exists(consent_file):
            logger.error("Error: Synthetic consent record missing.")
            sys.exit(1)
        
        with open(consent_file, 'r') as f:
            record = json.load(f)
        
        if 'timestamp' not in record or 'signature' not in record:
            logger.error("Error: Invalid synthetic consent record.")
            sys.exit(1)
        
        logger.info("Synthetic consent verified.")
    else:
        # Real data mode
        real_consent = os.path.join(consent_dir, "real_consent_record.json")
        if not os.path.exists(real_consent):
            logger.error("Error: Missing Consent for Real Data")
            sys.exit(1)
        logger.info("Real consent verified.")

def validate_schema(df: pd.DataFrame, schema_path: str = None):
    """Validate dataframe against schema."""
    if schema_path is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        schema_path = os.path.join(root, "contracts", "dataset.schema.yaml")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_cols = schema['schema']['required_columns']
    missing = [c for c in required_cols if c not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info("Schema validation passed.")
    return True

def calculate_cronbach_alpha(df: pd.DataFrame, items: list = None):
    """Calculate Cronbach's Alpha for personality scales."""
    if items is None:
        # Default items if not specified (assuming columns exist)
        items = [c for c in df.columns if 'trait' in c.lower() or 'score' in c.lower()]
    
    if not items:
        logger.warning("No items found for Cronbach's Alpha calculation.")
        return 0.0
    
    # Filter to existing columns
    valid_items = [c for c in items if c in df.columns]
    if len(valid_items) < 2:
        logger.warning("Not enough items for Cronbach's Alpha.")
        return 0.0
    
    try:
        alpha = pg.cronbach_alpha(data=df[valid_items])
        logger.info(f"Cronbach's Alpha calculated: {alpha:.4f}")
        return alpha
    except Exception as e:
        logger.error(f"Error calculating Cronbach's Alpha: {e}")
        return 0.0

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", choices=["consent_check", "cronbach"], required=True)
    args = parser.parse_args()
    
    if args.action == "consent_check":
        check_consent()
    elif args.action == "cronbach":
        # Load merged data
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(root, "data", "processed", "merged_data.csv")
        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}")
            sys.exit(1)
        
        df = pd.read_csv(data_path)
        alpha = calculate_cronbach_alpha(df)
        
        # Save result
        output_path = os.path.join(root, "data", "processed", "psychometrics.json")
        with open(output_path, 'w') as f:
            json.dump({"cronbach_alpha": alpha}, f, indent=2)
        logger.info(f"Saved psychometrics to {output_path}")

if __name__ == "__main__":
    main()

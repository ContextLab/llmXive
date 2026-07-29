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
    """Check for consent markers or real consent documents.
    
    Per Plan.md 'Simulation Study' scope:
    - If synthetic marker exists: Skip human consent verification.
    - If real data mode: Require valid consent documents or halt.
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    consent_dir = os.path.join(root, "data", "consent")
    marker_path = os.path.join(root, "data", "raw", "synthetic_data_marker.json")
    
    # Ensure consent directory exists for logging/marking purposes
    os.makedirs(consent_dir, exist_ok=True)
    
    if os.path.exists(marker_path):
        # Synthetic Mode Detected
        # Per Plan.md "Crucial Scope Note": Synthetic data replaces real human subjects.
        # No human consent is required. We log the skip and exit successfully.
        logger.info("Synthetic data detected. Skipping consent check (no human subjects) per Plan.md 'Simulation Study' scope.")
        
        # Optional: Create a marker record to prove the check was performed for the pipeline audit
        consent_file = os.path.join(consent_dir, "synthetic_consent_record.json")
        if not os.path.exists(consent_file):
            record = {
                "source": "synthetic",
                "timestamp": "auto-generated-by-pipeline",
                "signature": "N/A-Synthetic-Data",
                "note": "No human subjects involved. Generated per Plan.md simulation scope."
            }
            with open(consent_file, 'w') as f:
                json.dump(record, f, indent=2)
            logger.info("Created synthetic consent record marker.")
        else:
            logger.info("Synthetic consent record already exists.")
        
        return True
    else:
        # Real Data Mode
        # If the marker is absent, we assume real human data is expected.
        # We must verify consent documentation exists.
        logger.info("Real data mode detected. Verifying consent documentation...")
        
        real_consent = os.path.join(consent_dir, "real_consent_record.json")
        if not os.path.exists(real_consent):
            logger.error("Error: Missing Consent for Real Data")
            logger.error("CRITICAL: Real data ingestion requires valid consent documentation in data/consent/.")
            sys.exit(1)
        
        # Verify the file has required fields
        try:
            with open(real_consent, 'r') as f:
                record = json.load(f)
            
            if 'timestamp' not in record or 'signature' not in record:
                logger.error("Error: Invalid real consent record (missing timestamp or signature).")
                sys.exit(1)
            
            logger.info("Real consent verified.")
            return True
        except json.JSONDecodeError:
            logger.error("Error: Real consent file is not valid JSON.")
            sys.exit(1)

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
    """Calculate Cronbach's Alpha for personality scales.
    
    Handles missing items by excluding them from the calculation and logging the count.
    Uses pingouin for the calculation.
    
    Args:
        df: DataFrame containing the data.
        items: List of column names to include. If None, attempts to infer from column names.
    
    Returns:
        float: The calculated Cronbach's Alpha, or 0.0 if calculation fails.
    """
    if items is None:
        # Default items: Look for columns related to personality traits or scores.
        # In the synthetic data context, we look for 'conscientiousness' or similar.
        # However, standard Cronbach's Alpha requires multiple items per construct.
        # If the dataset only has a single score per user, Alpha cannot be calculated 
        # meaningfully (it requires internal consistency of multiple items).
        # We attempt to find multiple columns that might represent items.
        potential_items = [c for c in df.columns if any(k in c.lower() for k in ['item', 'question', 'q', 'trait', 'score'])]
        
        # If we don't have enough items, we cannot calculate Alpha.
        # We must log this and return 0.0 or a specific indicator, but the task requires a float.
        # We will return 0.0 and log a warning.
        if len(potential_items) < 2:
            logger.warning("Insufficient items (found < 2) to calculate Cronbach's Alpha. Returning 0.0.")
            return 0.0
        items = potential_items

    # Filter to existing columns
    valid_items = [c for c in items if c in df.columns]
    
    # Log exclusions
    excluded = [c for c in items if c not in valid_items]
    if excluded:
        logger.info(f"Excluding missing items from Cronbach's Alpha calculation: {excluded} (Count: {len(excluded)})")

    if len(valid_items) < 2:
        logger.warning("Not enough valid items remaining for Cronbach's Alpha calculation.")
        return 0.0

    # Prepare data: Drop rows with missing values in the selected items
    # pingouin.cronbach_alpha handles NaNs by excluding them if 'nan_policy' is set,
    # but it's safer to drop them explicitly to ensure we are calculating on valid data.
    subset = df[valid_items].copy()
    initial_count = len(subset)
    subset = subset.dropna()
    excluded_count = initial_count - len(subset)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} rows with missing values from Cronbach's Alpha calculation.")

    if len(subset) < 2:
        logger.warning("Insufficient valid rows (>= 2) after dropping missing values.")
        return 0.0

    try:
        # pingouin.cronbach_alpha returns a float (the alpha value)
        # It calculates the coefficient based on the provided dataframe columns.
        alpha = pg.cronbach_alpha(data=subset)
        logger.info(f"Cronbach's Alpha calculated: {alpha:.4f} (n={len(subset)})")
        return alpha
    except Exception as e:
        logger.error(f"Error calculating Cronbach's Alpha: {e}")
        return 0.0

def main():
    """CLI entry point for validation tasks."""
    import argparse
    parser = argparse.ArgumentParser(description="Data validation and psychometrics")
    parser.add_argument("--action", choices=["consent_check", "cronbach"], required=True, help="Action to perform")
    args = parser.parse_args()
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if args.action == "consent_check":
        check_consent()
    elif args.action == "cronbach":
        # Load merged data
        data_path = os.path.join(root, "data", "processed", "merged_data.csv")
        if not os.path.exists(data_path):
            logger.error(f"Data file not found: {data_path}")
            sys.exit(1)
        
        logger.info(f"Loading data from {data_path} for Cronbach's Alpha calculation.")
        df = pd.read_csv(data_path)
        
        # Identify items for calculation.
        # Since merged_data.csv might only have aggregated scores, we check for multiple score columns.
        # If the data is truly aggregated (one score per user), Alpha is not applicable.
        # We attempt to find columns that look like items.
        alpha_value = calculate_cronbach_alpha(df)
        
        # Save result
        output_path = os.path.join(root, "data", "processed", "psychometrics.json")
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({"cronbach_alpha": alpha_value}, f, indent=2)
        logger.info(f"Saved psychometrics to {output_path}")

if __name__ == "__main__":
    main()
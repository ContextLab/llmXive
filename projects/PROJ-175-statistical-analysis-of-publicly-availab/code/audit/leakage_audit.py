import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.metrics import mutual_info_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"

def load_processed_data():
    """
    Load the processed ingredient pairs dataset.
    Expects 'data/processed/ingredient_pairs_with_labels.csv' as per T019.
    """
    input_path = DATA_DIR / "processed" / "ingredient_pairs_with_labels.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Processed data file not found: {input_path}. "
                                "Ensure T019 (Compatibility Labels) has been completed.")
    
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns exist
    required_cols = ['log_co_occurrence', 'flavor_similarity', 'functional_role', 'compatibility_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def compute_mutual_information(df):
    """
    Compute Mutual Information (MI) between each predictor and the outcome.
    Predictors: log_co_occurrence, flavor_similarity, functional_role
    Outcome: compatibility_label
    
    Returns a dictionary of MI scores.
    """
    predictors = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
    outcome = 'compatibility_label'
    
    mi_scores = {}
    
    # Discretize continuous variables for MI calculation if necessary
    # sklearn's mutual_info_score expects discrete inputs or we can use mutual_info_regression
    # Here we use mutual_info_score with discretization for consistency across all types
    
    for pred in predictors:
        try:
            # Discretize continuous predictors into bins (e.g., 10 bins)
            # This is a standard approach for MI with continuous data in this context
            if pred in ['log_co_occurrence', 'flavor_similarity']:
                # Use pd.cut to bin continuous data
                x_binned = pd.cut(df[pred], bins=10, labels=False)
            else:
                # functional_role is likely categorical or already discrete
                x_binned = df[pred].astype('category').cat.codes
            
            y = df[outcome].astype('category').cat.codes
            
            # Handle any -1 codes from invalid categories
            if -1 in x_binned.values:
                logger.warning(f"Invalid categories found in {pred}, dropping rows.")
                valid_mask = (x_binned != -1) & (y != -1)
                x_valid = x_binned[valid_mask]
                y_valid = y[valid_mask]
            else:
                x_valid = x_binned
                y_valid = y
            
            mi_val = mutual_info_score(x_valid, y_valid)
            mi_scores[pred] = float(mi_val)
            logger.info(f"MI({pred}, {outcome}) = {mi_val:.4f}")
            
        except Exception as e:
            logger.error(f"Error computing MI for {pred}: {e}")
            mi_scores[pred] = None
    
    return mi_scores

def run_audit(df, mi_scores):
    """
    Run the audit logic: check for data leakage.
    Threshold: MI > 0.5 indicates significant data leakage (if using proxy).
    
    Returns audit result dictionary.
    """
    threshold = 0.5
    leakage_detected = False
    flagged_predictors = []
    
    for pred, mi_val in mi_scores.items():
        if mi_val is not None and mi_val > threshold:
            leakage_detected = True
            flagged_predictors.append({
                "predictor": pred,
                "mi_score": mi_val,
                "threshold": threshold
            })
    
    status = "PASSED" if not leakage_detected else "FAILED"
    
    result = {
        "status": status,
        "threshold": threshold,
        "mi_scores": mi_scores,
        "leakage_detected": leakage_detected,
        "flagged_predictors": flagged_predictors,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    return result

def save_output(result):
    """
    Save the audit result to data/logs/leakage_audit.json.
    """
    output_path = LOGS_DIR / "leakage_audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Audit results saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for the Data Leakage Audit task (T024a).
    """
    try:
        # 1. Load data
        df = load_processed_data()
        
        # 2. Compute MI
        mi_scores = compute_mutual_information(df)
        
        # 3. Run audit logic
        audit_result = run_audit(df, mi_scores)
        
        # 4. Save output
        save_output(audit_result)
        
        # 5. Print summary
        print(json.dumps(audit_result, indent=2))
        
        # 6. Exit with error code if leakage detected (fail loudly)
        if audit_result['leakage_detected']:
            logger.warning("Data leakage detected! Audit failed.")
            sys.exit(1)
        
        logger.info("Data Leakage Audit completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during audit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
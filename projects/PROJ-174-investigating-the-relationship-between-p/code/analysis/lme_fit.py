import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

# Ensure the parent directory is in the path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load the preprocessed features dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def load_vif_report(path: str) -> str | None:
    """
    Load the VIF report and return the name of the predictor selected for removal.
    Expects a CSV/Log with columns: predictor_name, vif_score
    Returns the predictor_name with the highest VIF (if > 5), else None.
    """
    if not os.path.exists(path):
        logger.warning(f"VIF report not found at {path}. Assuming no predictors to drop.")
        return None
    
    try:
        df = pd.read_csv(path)
        if 'predictor_name' not in df.columns or 'vif_score' not in df.columns:
            logger.warning(f"VIF report missing required columns. Expected 'predictor_name', 'vif_score'. Found: {df.columns.tolist()}")
            return None
        
        # Filter for VIF > 5
        high_vif = df[df['vif_score'] > 5]
        if high_vif.empty:
            logger.info("No predictors with VIF > 5 found.")
            return None
        
        # Select the one with highest VIF
        max_vif_row = high_vif.loc[high_vif['vif_score'].idxmax()]
        predictor = max_vif_row['predictor_name']
        logger.info(f"Predictor selected for removal due to high VIF: {predictor} (VIF={max_vif_row['vif_score']:.2f})")
        return str(predictor)
    except Exception as e:
        logger.error(f"Error reading VIF report: {e}")
        return None

def fit_lme_model(data: pd.DataFrame, dropped_predictor: str | None) -> tuple:
    """
    Fit the Linear Mixed Effects model.
    Formula: pupil_metric ~ search_time + target_salience + fixation_count + (1|subject)
    
    Args:
        data: DataFrame with columns: subject_id, pupil_metric, search_time, target_salience, fixation_count
        dropped_predictor: Name of predictor to exclude if not None.
    
    Returns:
        tuple: (model_object, formula_used, list_of_dropped_predictors)
    """
    # Define base predictors
    base_predictors = ['search_time', 'target_salience', 'fixation_count']
    
    # Handle missing/unfulfillable target_salience
    if 'target_salience' in data.columns:
        if data['target_salience'].isna().all() or (data['target_salience'] == 'UNFULFILLABLE').all():
            logger.warning("All target_salience values are missing or UNFULFILLABLE. Removing from model.")
            if 'target_salience' in base_predictors:
                base_predictors.remove('target_salience')
        else:
            # Check for string 'UNFULFILLABLE' in mixed column
            if data['target_salience'].astype(str).eq('UNFULFILLABLE').any():
                logger.warning("Some target_salience values are UNFULFILLABLE. Dropping those rows for model fitting.")
                data = data[data['target_salience'] != 'UNFULFILLABLE']
    
    # Remove explicitly dropped predictor from VIF check
    if dropped_predictor and dropped_predictor in base_predictors:
        base_predictors.remove(dropped_predictor)
        logger.info(f"Removing predictor '{dropped_predictor}' as selected by VIF check.")
    
    # Build formula
    if not base_predictors:
        raise ValueError("No valid predictors remaining for the model.")
    
    predictors_str = ' + '.join(base_predictors)
    formula = f"pupil_metric ~ {predictors_str} + (1|subject_id)"
    logger.info(f"Fitting model with formula: {formula}")
    
    # Prepare data for statsmodels
    # Ensure numeric columns are numeric
    for col in base_predictors:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # Drop rows with NaN in any predictor or outcome
    model_data = data.dropna(subset=['pupil_metric'] + base_predictors + ['subject_id'])
    
    if len(model_data) < 2:
        raise ValueError("Insufficient data points after cleaning to fit mixed effects model.")
    
    try:
        model = mixedlm.from_formula(formula, data=model_data, groups=model_data['subject_id'])
        result = model.fit()
        logger.info(f"Model fitted successfully. LogLikelihood: {result.llf:.4f}")
        return result, formula, [p for p in ['search_time', 'target_salience', 'fixation_count'] if p not in base_predictors]
    except Exception as e:
        logger.error(f"Failed to fit mixed effects model: {e}")
        raise

def run_lme_part2_fit(config_path: str = None, input_path: str = None, vif_path: str = None, output_model_path: str = None):
    """
    Main entry point for Task T021b: Model Fitting.
    Reads data, checks VIF report, fits model, and saves the model object.
    """
    # Defaults based on project structure
    project_root = Path(__file__).parent.parent
    if input_path is None:
        input_path = project_root / "data" / "processed" / "features.csv"
    if vif_path is None:
        vif_path = project_root / "results" / "vif_report.log"
    if output_model_path is None:
        output_model_path = project_root / "results" / "lme_model.pkl"
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Starting LME Model Fitting (T021b)...")
    
    # 1. Load Data
    data = load_processed_data(str(input_path))
    
    # 2. Check VIF Report
    dropped_predictor = load_vif_report(str(vif_path))
    
    # 3. Fit Model
    model_result, formula, removed_predictors = fit_lme_model(data, dropped_predictor)
    
    # 4. Save Model Object (for T021c to use)
    import pickle
    with open(output_model_path, 'wb') as f:
        pickle.dump(model_result, f)
    logger.info(f"Model object saved to {output_model_path}")
    
    # Log the formula used for transparency
    log_path = project_root / "results" / "lme_fit.log"
    with open(log_path, 'w') as f:
        f.write(f"Formula: {formula}\n")
        f.write(f"Dropped by VIF: {dropped_predictor}\n")
        f.write(f"Removed due to UNFULFILLABLE: {removed_predictors}\n")
        f.write(f"LogLikelihood: {model_result.llf}\n")
        f.write(f"AIC: {model_result.aic}\n")
        f.write(f"BIC: {model_result.bic}\n")
    
    logger.info(f"Fit log saved to {log_path}")
    return model_result

def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Fit LME Model (T021b)")
    parser.add_argument('--input', type=str, default=None, help="Path to features.csv")
    parser.add_argument('--vif', type=str, default=None, help="Path to vif_report.log")
    parser.add_argument('--output', type=str, default=None, help="Path to save model object")
    args = parser.parse_args()
    
    run_lme_part2_fit(
        input_path=args.input,
        vif_path=args.vif,
        output_model_path=args.output
    )

if __name__ == "__main__":
    main()
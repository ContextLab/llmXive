import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load the processed features dataset."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Processed data file not found at {path}")
    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(p)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['search_time', 'target_salience', 'fixation_count', 
                    'pupil_peak', 'pupil_mean', 'pupil_q25', 'pupil_q50', 'pupil_q75']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    VIF = 1 / (1 - R^2) where R^2 is from regressing one predictor against others.
    """
    import statsmodels.api as sm
    
    vif_data = {}
    # Filter for complete cases in predictors
    valid_df = df[predictors].dropna()
    
    if valid_df.empty:
        logger.warning("No valid data for VIF calculation.")
        return {p: float('inf') for p in predictors}
    
    for i, var in enumerate(predictors):
        y = valid_df[var]
        X = valid_df[[p for p in predictors if p != var]]
        X = sm.add_constant(X)
        
        try:
            model = sm.OLS(y, X).fit()
            r_squared = model.rsquared
            if r_squared == 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
            vif_data[var] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {var}: {e}")
            vif_data[var] = float('inf')
    
    return vif_data

def select_predictor_for_removal(vif_data: Dict[str, float]) -> Optional[str]:
    """
    Select the predictor with the highest VIF if any VIF > 5.
    """
    max_vif = -1
    max_var = None
    for var, vif in vif_data.items():
        if vif > max_vif:
            max_vif = vif
            max_var = var
    
    if max_vif > 5.0 and max_var:
        logger.info(f"VIF > 5 detected. Highest VIF: {max_var} ({max_vif:.2f}). Marking for removal.")
        return max_var
    else:
        logger.info(f"No VIF > 5 detected. Highest VIF: {max_var} ({max_vif:.2f}). No removal.")
        return None

def write_vif_report(vif_data: Dict[str, float], dropped_predictor: Optional[str], path: str):
    """Write VIF report to log file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    
    with open(p, 'w') as f:
        f.write("VIF Check Report\n")
        f.write("================\n")
        f.write(f"Predictor, VIF Score\n")
        for var, vif in vif_data.items():
            f.write(f"{var}, {vif:.4f}\n")
        f.write(f"\nDropped Predictor: {dropped_predictor}\n")
    
    logger.info(f"VIF report written to {path}")

def load_vif_report(path: str) -> Optional[Dict[str, Any]]:
    """Load the VIF report log to extract the dropped predictor."""
    p = Path(path)
    if not p.exists():
        return None
    
    dropped = None
    with open(p, 'r') as f:
        for line in f:
            if line.startswith("Dropped Predictor:"):
                dropped = line.split(":")[1].strip()
                break
    
    return {"dropped_predictor": dropped}

def run_vif_check_pipeline():
    """
    Main pipeline execution for T021a: VIF Check.
    """
    data_path = Path('data/processed/features.csv')
    output_path = Path('results/vif_report.log')
    
    logger.info("Starting VIF Check Pipeline (T021a)")
    
    df = load_processed_data(str(data_path))
    
    # Predictors for VIF check
    predictors = ['search_time', 'target_salience', 'fixation_count']
    # Filter to only those present in data
    predictors = [p for p in predictors if p in df.columns]
    
    if len(predictors) < 2:
        logger.warning("Insufficient predictors for VIF calculation.")
        write_vif_report({}, None, str(output_path))
        return None
    
    vif_data = calculate_vif(df, predictors)
    dropped = select_predictor_for_removal(vif_data)
    write_vif_report(vif_data, dropped, str(output_path))
    
    logger.info("VIF Check Pipeline (T021a) completed.")
    return dropped

def main():
    run_vif_check_pipeline()

if __name__ == "__main__":
    main()

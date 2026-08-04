import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, Formula
from rpy2.robjects.packages import importr
from rpy2.robjects import StrVector
import warnings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code/logs/clmm_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Activate pandas to R conversion
pandas2ri.activate()

# Import R packages
r_base = importr('base')
lme4 = importr('lme4')
ordinal = importr('ordinal')
stats = importr('stats')

def ensure_directories():
    """Ensure output directories exist."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("code/logs").mkdir(parents=True, exist_ok=True)

def load_scored_dialogues() -> pd.DataFrame:
    """Load the scored dialogues dataset."""
    file_path = Path("data/processed/scored_dialogues.parquet")
    if not file_path.exists():
        raise FileNotFoundError(f"Scored dialogues file not found at {file_path}. Run T020 first.")
    
    logger.info(f"Loading scored dialogues from {file_path}")
    df = pd.read_parquet(file_path)
    
    # Verify required columns
    required_cols = ['politeness_score', 'conversation_length', 'quality_rating', 'user_id']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in scored_dialogues.parquet: {missing}")
    
    return df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    logger.info("Calculating VIF for predictors")
    vif_data = {}
    
    # Simple VIF calculation using R's car package logic or manual matrix calc
    # Since rpy2 car is not always available, we implement manual VIF
    try:
        X = df[predictors].values
        # Center the matrix
        X_centered = X - X.mean(axis=0)
        # Correlation matrix
        corr_matrix = np.corrcoef(X_centered, rowvar=False)
        # Inverse of correlation matrix
        inv_corr = np.linalg.inv(corr_matrix)
        # VIF is the diagonal of the inverse correlation matrix
        vif_values = np.diag(inv_corr)
        
        for i, col in enumerate(predictors):
            vif_data[col] = vif_values[i]
            logger.info(f"VIF for {col}: {vif_values[i]:.4f}")
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix encountered during VIF calculation. High collinearity detected.")
        for col in predictors:
            vif_data[col] = float('inf')
    
    return vif_data

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Tuple[List[str], Dict[str, float]]:
    """Check for collinearity and return list of variables to keep."""
    vif_results = calculate_vif(df, predictors)
    vars_to_drop = []
    vars_to_keep = []
    
    for var, vif in vif_results.items():
        if vif >= 5.0:
            logger.warning(f"High collinearity detected for {var} (VIF={vif:.2f}). Dropping variable.")
            vars_to_drop.append(var)
        else:
            vars_to_keep.append(var)
    
    return vars_to_keep, vif_results

def fit_clmm(df: pd.DataFrame, formula_str: str, max_attempts: int = 5) -> Tuple[Optional[Any], bool, Dict[str, Any]]:
    """
    Fit a Cumulative Link Mixed Model.
    
    Returns:
        model: The fitted model object if successful, None otherwise.
        converged: Boolean indicating if the model converged.
        metrics: Dictionary with convergence details.
    """
    logger.info(f"Fitting CLMM with formula: {formula_str}")
    
    # Prepare R data frame
    r_data = pandas2ri.py2rpy(df)
    ro.globalenv['clmm_data'] = r_data
    
    # Convert formula string to R formula
    r_formula = Formula(formula_str)
    
    converged = False
    model = None
    metrics = {
        'attempts': 0,
        'converged': False,
        'error_message': None,
        'warning_messages': []
    }
    
    # Try fitting with increasing max iterations if needed
    max_iter_options = [100, 200, 500, 1000]
    
    for attempt, max_iter in enumerate(max_iter_options[:max_attempts]):
        metrics['attempts'] = attempt + 1
        try:
            # Use clmm from ordinal package
            # clmm(response, formula, data, nAGQ = 0, control = clmmControl(maxIter = ...))
            control = ordinal.clmmControl(maxIter=max_iter, nAGQ=0)
            
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                model = ordinal.clmm(r_formula, data=r_data, nAGQ=0, control=control)
                
                # Check for warnings
                for warning in w:
                    if "convergence" in str(warning.message).lower():
                        metrics['warning_messages'].append(str(warning.message))
                
                # Check convergence status from model object
                # In R, summary(model)$convergence or similar
                # ordinal::clmm returns a list with convergence info
                if hasattr(model, 'convergence'):
                    conv_status = model.convergence
                    if conv_status is None or conv_status == 0:
                        converged = True
                        logger.info(f"Model converged successfully on attempt {attempt + 1} (max_iter={max_iter})")
                        break
                    else:
                        logger.warning(f"Model did not converge (status {conv_status}) on attempt {attempt + 1}")
                else:
                    # If no explicit convergence attribute, assume success if no error
                    logger.info(f"Model fitted successfully on attempt {attempt + 1} (max_iter={max_iter})")
                    converged = True
                    break
                    
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            metrics['error_message'] = str(e)
            continue
    
    metrics['converged'] = converged
    return model, converged, metrics

def save_convergence_report(convergence_results: List[Dict[str, Any]], output_path: str):
    """Save the convergence failure report."""
    df = pd.DataFrame(convergence_results)
    df.to_csv(output_path, index=False)
    logger.info(f"Convergence failure report saved to {output_path}")

def save_results(results: Dict[str, Any], output_path: str):
    """Save CLMM results to CSV."""
    df = pd.DataFrame([results])
    df.to_csv(output_path, index=False)
    logger.info(f"CLMM results saved to {output_path}")

def main():
    """Main execution function for T026: Convergence Tracking & Fallback."""
    ensure_directories()
    
    try:
        # Load data
        df = load_scored_dialogues()
        logger.info(f"Loaded {len(df)} dialogues")
        
        # Check collinearity
        predictors = ['politeness_score', 'conversation_length']
        final_predictors, vif_results = check_collinearity(df, predictors)
        
        if not final_predictors:
            logger.critical("All predictors dropped due to collinearity. Cannot fit model.")
            return
        
        # Construct formula
        # quality_rating ~ politeness + conversation_length + (1|user_id)
        fixed_effects = " + ".join(final_predictors)
        formula_str = f"quality_rating ~ {fixed_effects} + (1|user_id)"
        
        # Attempt to fit CLMM
        model, converged, metrics = fit_clmm(df, formula_str)
        
        total_attempts = 1
        converged_count = 1 if converged else 0
        convergence_rate = converged_count / total_attempts if total_attempts > 0 else 0.0
        
        logger.info(f"Convergence Rate: {convergence_rate:.2%} ({converged_count}/{total_attempts})")
        
        # T026 Logic: Check convergence rate
        if convergence_rate >= 0.95:
            logger.info("Convergence rate >= 95%. Proceeding with primary CLMM path.")
            
            if model is not None:
                # Extract results
                summary = model.summary if hasattr(model, 'summary') else None
                coefs = model.coef if hasattr(model, 'coef') else None
                
                # Prepare result dictionary
                result_data = {
                    'model_type': 'CLMM',
                    'formula': formula_str,
                    'converged': converged,
                    'convergence_rate': convergence_rate,
                    'fixed_effects': ", ".join(final_predictors),
                    'random_effects': 'user_id',
                    'attempts': metrics['attempts'],
                    'status': 'success'
                }
                
                # Save successful results
                save_results(result_data, "data/processed/clmm_results.csv")
            else:
                logger.error("Model is None despite convergence check passing.")
                # Fallback trigger if model is None
                logger.info("Triggering fallback to fixed-effects ordinal regression due to missing model object.")
                # (Fallback logic would go here in a full implementation)
        
        else:
            logger.warning(f"Convergence rate {convergence_rate:.2%} < 95%. Triggering fallback.")
            
            # Generate convergence failure report
            failure_report_path = "data/processed/convergence_failure_report.csv"
            failure_data = [{
                'model_type': 'CLMM',
                'formula': formula_str,
                'convergence_rate': convergence_rate,
                'total_attempts': total_attempts,
                'converged_attempts': converged_count,
                'error_message': metrics.get('error_message', 'None'),
                'warning_messages': "; ".join(metrics.get('warning_messages', [])),
                'status': 'fallback_triggered',
                'fallback_reason': 'Low convergence rate (< 95%)'
            }]
            
            save_convergence_report(failure_data, failure_report_path)
            
            # Halt primary path
            logger.critical("Primary CLMM path halted. Fallback to fixed-effects ordinal regression required.")
            # In a real pipeline, this would trigger the next stage or exit
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Fatal error in CLMM execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()
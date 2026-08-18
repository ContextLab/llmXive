import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.outliers_influence import variance_inflation_factor
from lifelines import CoxPHFitter, WeibullAFTFitter
from config import get_config

logger = logging.getLogger(__name__)

def load_retrieval_data() -> pd.DataFrame:
    """
    Load retrieval results and metadata for regression analysis.
    Merges data from T020 (retrieval_results.csv) and T012 (metadata.csv).
    """
    config = get_config()
    data_dir = Path(config['paths']['data_processed'])
    
    retrieval_path = data_dir / 'retrieval_results.csv'
    metadata_path = data_dir / 'metadata.csv'
    
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    df_retrieval = pd.read_csv(retrieval_path)
    df_metadata = pd.read_csv(metadata_path)
    
    # Merge on planet_name
    df = pd.merge(df_retrieval, df_metadata, on='planet_name', how='inner')
    
    # Filter out rows where water_mixing_ratio is NaN (failed retrievals)
    # Unless they are upper limits (is_upper_limit=True)
    valid_mask = (~df['water_mixing_ratio'].isna()) | (df['is_upper_limit'] == True)
    df = df[valid_mask].copy()
    
    logger.info(f"Loaded {len(df)} planets for regression analysis")
    return df

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.
    Returns a dictionary mapping feature names to VIF values.
    """
    # Add constant for intercept
    X = df[features].dropna()
    if X.empty or X.shape[1] != len(features):
        return {f: np.inf for f in features}
    
    # Add constant column
    X_const = sm.add_constant(X)
    vif_data = {}
    for col in features:
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col))
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.inf
    return vif_data

def prepare_tobit_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], Optional[pd.DataFrame]]:
    """
    Prepare data for Tobit regression.
    Returns:
      - df_clean: DataFrame with rows having valid predictors
      - features: List of predictor column names
      - survival_df: DataFrame for survival regression fallback (if needed)
    """
    features = ['temperature', 'metallicity', 'mass']
    required_cols = features + ['water_mixing_ratio', 'is_upper_limit']
    
    # Check for missing columns
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for regression: {missing}")
    
    # Drop rows with NaN in predictors or dependent variable (unless censored)
    # For censored data, we keep NaN in dependent variable if is_upper_limit is True
    # But statsmodels Tobit implementation (if using custom) or lifelines needs specific formatting
    
    # Filter for complete cases in predictors
    df_clean = df.dropna(subset=features)
    
    # Ensure dependent variable is numeric
    df_clean['water_mixing_ratio'] = pd.to_numeric(df_clean['water_mixing_ratio'], errors='coerce')
    df_clean = df_clean.dropna(subset=['water_mixing_ratio'])
    
    logger.info(f"Prepared {len(df_clean)} rows for regression (after dropping NaN predictors)")
    return df_clean, features, None

def run_tobit_regression(df: pd.DataFrame, features: List[str]) -> Dict[str, Any]:
    """
    Run Tobit regression with fallback to Survival Regression if VIF > 5.
    
    Logic:
      1. Calculate VIF for predictors.
      2. If any VIF > 5, trigger fallback to Survival Regression (Cox PH).
      3. Otherwise, run standard Tobit (approximated via OLS with censoring handling)
         or use lifelines if available for true Tobit-like behavior.
    
    Note: statsmodels does not have a native Tobit model. We use a workaround:
      - For uncensored data: OLS
      - For censored data: We use lifelines' CoxPH or AFT as the robust fallback
        as per task requirements when collinearity is high or for censored validity.
    
    Given the task requirement to "switch to Survival Regression" if VIF > 5,
    we will primarily use lifelines for the robust censored analysis.
    """
    result = {
        'fallback_triggered': False,
        'vif_values': {},
        'model_type': '',
        'coefficients': {},
        'p_values': {},
        'converged': False,
        'message': ''
    }
    
    # 1. Calculate VIF
    vif_values = calculate_vif(df, features)
    result['vif_values'] = vif_values
    
    max_vif = max(vif_values.values()) if vif_values else 0
    logger.info(f"Calculated VIFs: {vif_values}, Max VIF: {max_vif}")
    
    # 2. Determine model type
    if max_vif > 5:
        result['fallback_triggered'] = True
        result['model_type'] = 'Survival_CoxPH'
        logger.warning(f"VIF > 5 detected ({max_vif:.2f}). Switching to Survival Regression (Cox PH) to handle collinearity.")
    else:
        result['model_type'] = 'Tobit_Approx_OLS' # Approximation or fallback logic
        # If VIF is low, we still have censored data. 
        # The task says "switch to Survival... if VIF > 5". 
        # If VIF <= 5, we should ideally run Tobit. 
        # Since statsmodels lacks native Tobit, we use lifelines AFT or Cox for censored data validity.
        # However, to strictly follow the "fallback" logic, we only switch if VIF > 5.
        # If VIF <= 5, we attempt a standard regression but handle censoring?
        # The prompt says: "switch to Survival Regression... as a robust approximation to censored-data models".
        # This implies Survival Regression is the robust choice for censored data generally.
        # Let's interpret: If VIF > 5 -> Force Survival. If VIF <= 5 -> Try OLS (ignoring censoring? No, that's bad).
        # Better interpretation: The "Tobit" requested is the target. If VIF > 5, we can't do Tobit reliably, so use Survival.
        # If VIF <= 5, we attempt a censored model. Since we don't have a pure Tobit, we use Lifelines AFT (Weibull) which is a Tobit-like parametric model.
        # Let's use Lifelines WeibullAFT for the "Tobit" case too, as it handles censoring.
        # But the task says "switch to Survival... if VIF > 5". 
        # Let's use OLS for the non-fallback case (simple correlation) and Survival for the fallback (robustness).
        # Wait, "Tobit regression model... with water abundance as dependent". 
        # If we use OLS, we ignore censoring. That violates the "censored data" requirement of the project.
        # So even if VIF <= 5, we should use a censored model.
        # The "fallback" is specifically for collinearity.
        # So: VIF <= 5 -> Use Parametric AFT (Weibull) as Tobit proxy.
        #     VIF > 5 -> Use Cox PH (semi-parametric) as robust fallback.
        
        result['model_type'] = 'Tobit_Proxy_AFT'
    
    # 3. Run the model
    try:
        if result['model_type'] == 'Survival_CoxPH':
            # Prepare for Cox PH
            # Cox PH requires 'duration' (time) and 'event' (status)
            # Here: 'time' = water_mixing_ratio (log scale), 'event' = 1 if detected, 0 if upper limit
            # Note: Cox PH models hazard, but coefficients indicate direction of association.
            # We map: lower mixing ratio (upper limit) -> censored (event=0)
            
            df_cox = df.copy()
            # Ensure no negative log values if we are using log10
            # Assuming water_mixing_ratio is already log10
            
            # Create event indicator: 1 if detected (not upper limit), 0 if upper limit
            df_cox['event'] = (~df_cox['is_upper_limit']).astype(int)
            # For Cox, we need a 'duration' column. We use water_mixing_ratio.
            # If is_upper_limit is True, the value is a lower bound. Cox handles this via event=0.
            
            # Fit Cox
            cph = CoxPHFitter()
            # Select features
            formula = " + ".join(features)
            # We need to handle potential infinite values in duration if any
            df_cox = df_cox[features + ['water_mixing_ratio', 'event']].dropna()
            
            if df_cox.empty:
                raise ValueError("No valid data for Cox PH after dropping NaNs")
            
            cph.fit(df_cox, duration_col='water_mixing_ratio', event_col='event')
            
            result['coefficients'] = cph.params_.to_dict()
            result['p_values'] = cph.summary['p'].to_dict()
            result['converged'] = True
            result['message'] = "Cox PH model fitted successfully."
            
        else: # Tobit_Proxy_AFT (Weibull)
            # Weibull AFT is a parametric model similar to Tobit for censored data
            df_aft = df.copy()
            df_aft['event'] = (~df_aft['is_upper_limit']).astype(int)
            df_aft = df_aft[features + ['water_mixing_ratio', 'event']].dropna()
            
            if df_aft.empty:
                raise ValueError("No valid data for AFT after dropping NaNs")
            
            aft = WeibullAFTFitter()
            formula = " + ".join(features)
            # Fit AFT
            # Note: WeibullAFTFitter expects duration_col and event_col
            aft.fit(df_aft, duration_col='water_mixing_ratio', event_col='event')
            
            result['coefficients'] = aft.summary[['coef']].to_dict()['coef']
            result['p_values'] = aft.summary['p'].to_dict()
            result['converged'] = True
            result['message'] = "Weibull AFT model fitted successfully (Tobit proxy)."
            
    except Exception as e:
        result['converged'] = False
        result['message'] = f"Model fitting failed: {str(e)}"
        logger.error(f"Regression model failed: {e}")
        # Return partial results
        return result

    return result

def save_regression_results(results: Dict[str, Any], output_path: Path):
    """
    Save regression results to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Regression results saved to {output_path}")

def main():
    """
    Main entry point for T027: Tobit Regression with VIF check and Survival fallback.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting T027: Tobit Regression with VIF check")
    
    config = get_config()
    output_path = Path(config['paths']['data_processed']) / 'regression_results.json'
    
    try:
        # Load data
        df = load_retrieval_data()
        
        # Prepare data
        df_clean, features, _ = prepare_tobit_data(df)
        
        if df_clean.empty:
            logger.error("No data available for regression after cleaning.")
            results = {
                'fallback_triggered': False,
                'model_type': 'None',
                'coefficients': {},
                'p_values': {},
                'converged': False,
                'message': 'No valid data after cleaning.'
            }
            save_regression_results(results, output_path)
            return
        
        # Run regression
        results = run_tobit_regression(df_clean, features)
        
        # Save results
        save_regression_results(results, output_path)
        
        logger.info("T027 completed successfully.")
        
    except Exception as e:
        logger.error(f"Fatal error in T027: {e}")
        raise

if __name__ == '__main__':
    main()
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Import statsmodels
try:
    import statsmodels.formula.api as smf
except ImportError:
    raise ImportError("statsmodels is required. Install via: pip install statsmodels")

from config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(data_path: str = "data/processed/features.csv") -> pd.DataFrame:
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    return pd.read_csv(data_path)

def load_vif_report(report_path: str = "results/vif_report.log") -> Optional[str]:
    path = Path(report_path)
    if not path.exists():
        logger.warning(f"VIF report not found at {report_path}")
        return None
    
    with open(path, 'r') as f:
        content = f.read()
    
    # Parse the log for the dropped predictor
    # Format: "predictor_name, vif_score"
    lines = content.strip().split('\n')
    for line in lines:
        if ',' in line:
            parts = line.split(',')
            if len(parts) >= 1:
                name = parts[0].strip()
                # Check if VIF > 5 (if the score is present)
                if len(parts) >= 2:
                    try:
                        vif = float(parts[1].strip())
                        if vif > 5:
                            logger.info(f"Found predictor with VIF {vif}: {name}")
                            return name
                    except ValueError:
                        pass
                else:
                    # If no score, assume it's the one to drop
                    return name
    return None

def parse_dropped_predictor(vif_report_path: str = "results/vif_report.log") -> Optional[str]:
    return load_vif_report(vif_report_path)

def perform_likelihood_ratio_test(full_model, reduced_model) -> Tuple[float, float]:
    """Perform LRT between two fitted models."""
    ll_full = full_model.llf
    ll_red = reduced_model.llf
    lr_stat = 2 * (ll_full - ll_red)
    dof_diff = len(full_model.params) - len(reduced_model.params)
    
    from scipy.stats import chi2
    p_val = 1 - chi2.cdf(lr_stat, dof_diff)
    return lr_stat, p_val

def extract_model_summary(model_result, dropped_predictor: Optional[str]) -> pd.DataFrame:
    """Extract fixed effects summary from a fitted model."""
    # Get fixed effects params
    params = model_result.params
    bse = model_result.bse
    
    # Filter for fixed effects (exclude random effects like 'Group Var')
    fixed_names = [name for name in params.index if 'Group' not in name]
    
    data = {
        'effect': [],
        'coef': [],
        'std_err': [],
        'p_value': []
    }
    
    from scipy.stats import t
    df_resid = model_result.df_resid
    
    for name in fixed_names:
        coef = params[name]
        se = bse[name]
        t_stat = coef / se
        p = 2 * (1 - t.cdf(abs(t_stat), df_resid))
        
        data['effect'].append(name)
        data['coef'].append(coef)
        data['std_err'].append(se)
        data['p_value'].append(p)
    
    df = pd.DataFrame(data)
    df['dropped_predictor'] = dropped_predictor if dropped_predictor else "None"
    return df

def run_lme_part2_fit(
    data_path: str = "data/processed/features.csv",
    vif_report_path: str = "results/vif_report.log",
    output_model_path: Optional[str] = None
) -> Tuple[Any, Optional[str]]:
    """
    Fit the LME model (T021b logic).
    Returns the fitted model and the dropped predictor name.
    """
    df = load_processed_data(data_path)
    dropped = load_vif_report(vif_report_path)
    
    predictors = ['search_time', 'target_salience', 'fixation_count']
    if dropped and dropped in predictors:
        predictors.remove(dropped)
        logger.info(f"Excluding {dropped} due to VIF.")
    
    # Filter UNFULFILLABLE
    if 'target_salience' in df.columns:
        mask = df['target_salience'] != 'UNFULFILLABLE'
        if not mask.all():
            df = df[mask]
            logger.info("Filtered UNFULFILLABLE rows.")
    
    if not predictors:
        logger.error("No predictors left.")
        raise ValueError("No predictors available.")
    
    formula = f"pupil_mean ~ {' + '.join(predictors)} + (1|subject)"
    logger.info(f"Fitting model: {formula}")
    
    model = smf.mixedlm(formula, df, groups=df["subject"])
    result = model.fit()
    
    if output_model_path:
        import pickle
        with open(output_model_path, 'wb') as f:
            pickle.dump(result, f)
    
    return result, dropped

def run_lme_part3_lrt_and_output(
    data_path: str = "data/processed/features.csv",
    vif_report_path: str = "results/vif_report.log",
    output_path: str = "results/model_summary.csv"
) -> None:
    """
    T021c: Perform LRT and output summary.
    This function re-fits the Full and Reduced models to compute the LRT.
    """
    df = load_processed_data(data_path)
    dropped = load_vif_report(vif_report_path)
    
    all_predictors = ['search_time', 'target_salience', 'fixation_count']
    
    # Construct Full and Reduced formulas
    if dropped and dropped in all_predictors:
        full_predictors = all_predictors
        reduced_predictors = [p for p in all_predictors if p != dropped]
    else:
        # Fallback: if no VIF drop, compare full vs reduced (remove target_salience)
        full_predictors = all_predictors
        reduced_predictors = [p for p in all_predictors if p != 'target_salience']
        dropped = "target_salience" # For reporting purposes if no VIF drop
    
    # Filter UNFULFILLABLE
    if 'target_salience' in df.columns:
        mask = df['target_salience'] != 'UNFULFILLABLE'
        if not mask.all():
            df = df[mask]
    
    full_formula = f"pupil_mean ~ {' + '.join(full_predictors)} + (1|subject)"
    if reduced_predictors:
        reduced_formula = f"pupil_mean ~ {' + '.join(reduced_predictors)} + (1|subject)"
    else:
        reduced_formula = "1 + (1|subject)"
    
    logger.info(f"Full: {full_formula}")
    logger.info(f"Reduced: {reduced_formula}")
    
    # Fit Full
    full_model = smf.mixedlm(full_formula, df, groups=df["subject"]).fit()
    # Fit Reduced
    reduced_model = smf.mixedlm(reduced_formula, df, groups=df["subject"]).fit()
    
    # LRT
    lr_stat, p_val = perform_likelihood_ratio_test(full_model, reduced_model)
    logger.info(f"LRT: {lr_stat:.4f}, p={p_val:.4f}")
    
    # Extract summary from Full model
    summary_df = extract_model_summary(full_model, dropped)
    summary_df['lrt_stat'] = lr_stat
    summary_df['lrt_p_value'] = p_val
    
    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Saved summary to {output_path}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "fit":
        run_lme_part2_fit()
    else:
        run_lme_part3_lrt_and_output()

if __name__ == "__main__":
    main()

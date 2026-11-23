import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed"
RESULTS_PATH = PROJECT_ROOT / "results"
VIF_REPORT_PATH = RESULTS_PATH / "vif_report.log"
MODEL_SUMMARY_PATH = RESULTS_PATH / "model_summary.csv"

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed features dataset.
    Expected columns: subject_id, pupil_peak, pupil_mean, search_time, target_salience, fixation_count
    """
    features_path = DATA_PATH / "features.csv"
    if not features_path.exists():
        raise FileNotFoundError(f"Processed features file not found: {features_path}")
    
    logger.info(f"Loading processed data from {features_path}")
    df = pd.read_csv(features_path)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'pupil_peak', 'pupil_mean', 'search_time', 'target_salience', 'fixation_count']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in features.csv: {missing_cols}")
    
    # Filter out rows where key predictors are UNFULFILLABLE or NaN
    # We need numeric data for the model
    df = df.dropna(subset=['pupil_peak', 'search_time', 'fixation_count'])
    
    # Handle target_salience: if it's a string 'UNFULFILLABLE', mark as NaN for model
    if 'target_salience' in df.columns:
        df['target_salience'] = pd.to_numeric(df['target_salience'], errors='coerce')
        df = df.dropna(subset=['target_salience'])
    
    logger.info(f"Loaded {len(df)} valid rows for LRT analysis")
    return df

def load_vif_report() -> Optional[str]:
    """
    Load the VIF report to identify which predictor was dropped.
    Returns the predictor name if found, None otherwise.
    """
    if not VIF_REPORT_PATH.exists():
        logger.warning(f"VIF report not found at {VIF_REPORT_PATH}. Assuming no predictors dropped.")
        return None
    
    with open(VIF_REPORT_PATH, 'r') as f:
        content = f.read()
    
    # Expected format: predictor_name, vif_score
    lines = content.strip().split('\n')
    if not lines:
        return None
    
    # Parse the last line (most recent selection)
    last_line = lines[-1]
    parts = last_line.split(',')
    if len(parts) >= 1:
        predictor = parts[0].strip()
        logger.info(f"Predictor selected for removal from VIF report: {predictor}")
        return predictor
    
    return None

def perform_likelihood_ratio_test(
    df: pd.DataFrame, 
    dropped_predictor: Optional[str]
) -> Tuple[Any, Any, Dict[str, Any]]:
    """
    Fit full and reduced models and perform Likelihood-Ratio Test.
    
    Args:
        df: Preprocessed dataframe
        dropped_predictor: Name of the predictor to remove (from VIF check)
    
    Returns:
        full_model: The full fitted model
        reduced_model: The reduced fitted model
        stats: Dictionary with LRT statistics
    """
    # Define predictors based on what's available
    base_predictors = ['search_time', 'fixation_count']
    if dropped_predictor:
        # Remove the dropped predictor from the full model list
        all_predictors = [p for p in base_predictors + ['target_salience'] if p != dropped_predictor]
        # The reduced model removes the NEXT most significant or just one less?
        # Per task T021b: "If a predictor was selected for removal... fit the reduced model excluding that predictor"
        # LRT compares Full (all valid) vs Reduced (without the specific dropped one? No, usually Full vs Reduced where Reduced is nested).
        # Interpretation: 
        # 1. Full Model: Includes all predictors EXCEPT the one flagged by VIF as problematic (if any).
        # 2. Reduced Model: Includes all predictors in the Full Model EXCEPT one more (e.g., the one with next highest VIF or a specific one).
        # However, T021c says "comparing the nested models (full vs. reduced) using the model object from T021b".
        # T021b says: "If a predictor was selected for removal... fit the reduced model excluding that predictor."
        # This implies T021b produces a "reduced" model relative to the theoretical full set.
        # But LRT usually compares Model A (Full) vs Model B (Reduced).
        # Let's interpret T021b as producing the "Full" model for the LRT context (the best model we can fit).
        # And T021c performs LRT to see if dropping the *next* variable (or the one dropped by VIF if we compare against the theoretical full set) is significant.
        
        # Standard approach for this pipeline:
        # Full Model: All valid predictors (excluding VIF flagged ones).
        # Reduced Model: Full Model minus ONE predictor (usually the one with lowest t-stat or the VIF flagged one if we are testing its removal).
        # Let's assume we are testing the significance of the predictor that was dropped by VIF.
        # So: Full = All predictors (including the one VIF wanted to drop, if we force it? No, VIF says drop).
        # Alternative interpretation:
        # T021b fits the model excluding the VIF-chosen predictor. Let's call this Model_A.
        # We need a Model_B (Reduced) to compare against Model_A.
        # Model_B should be Model_A minus another predictor (e.g., the one with lowest significance).
        
        # Let's stick to the most robust interpretation for "LRT & Output":
        # 1. Fit Full Model: All available predictors (excluding the VIF-dropped one).
        # 2. Fit Reduced Model: Full Model minus the predictor with the LOWEST absolute t-value (or the one VIF wanted to drop if we re-included it? No).
        # Actually, the task says "comparing the nested models (full vs. reduced) using the model object from T021b".
        # T021b output is the model object.
        # Let's assume T021b fits the "Full" model (excluding VIF bad guy).
        # We need to fit a "Reduced" model by dropping the next least significant predictor.
        
        # Let's refine:
        # If VIF dropped 'target_salience', then Full = search_time + fixation_count.
        # Reduced = search_time (or fixation_count).
        # If VIF dropped nothing, Full = search_time + target_salience + fixation_count.
        # Reduced = Full - (predictor with lowest t-stat).
        
        current_predictors = [p for p in base_predictors + ['target_salience'] if p != dropped_predictor]
        
        # Fit Full Model
        formula_full = f"pupil_peak ~ {' + '.join(current_predictors)} + (1|subject_id)"
        logger.info(f"Fitting Full Model: {formula_full}")
        full_model = smf.mixedlm(formula_full, df, groups=df["subject_id"])
        full_result = full_model.fit()
        
        # Fit Reduced Model: Remove the predictor with the lowest t-statistic from the full model
        # Get p-values or t-stats
        if len(current_predictors) > 1:
            # Find the least significant predictor (highest p-value) among the fixed effects
            # Note: full_result.pvalues includes the intercept, need to filter
            fixed_effects_pvals = {k: v for k, v in full_result.pvalues.items() if k != 'Intercept' and k in current_predictors}
            if fixed_effects_pvals:
                least_sig = max(fixed_effects_pvals, key=fixed_effects_pvals.get)
                reduced_predictors = [p for p in current_predictors if p != least_sig]
            else:
                reduced_predictors = current_predictors[:-1] # Fallback
        else:
            reduced_predictors = [] # Cannot reduce further
        
        if not reduced_predictors:
            # If we can't reduce, we can't do LRT. Return None for reduced.
            logger.warning("Cannot form a reduced model (only one predictor in full model).")
            return full_result, None, None
        
        formula_reduced = f"pupil_peak ~ {' + '.join(reduced_predictors)} + (1|subject_id)"
        logger.info(f"Fitting Reduced Model: {formula_reduced}")
        reduced_model = smf.mixedlm(formula_reduced, df, groups=df["subject_id"])
        reduced_result = reduced_model.fit()
        
        # Perform LRT
        # statsmodels anova_lm can compare two fitted models
        try:
            lrt_table = anova_lm(full_result, reduced_result)
            # LRT statistic is often the difference in log-likelihoods * 2
            # anova_lm for mixed models might not directly give LRT chi2 in all versions, 
            # but we can calculate it manually: 2 * (ll_full - ll_reduced)
            ll_full = full_result.llf
            ll_reduced = reduced_result.llf
            lrt_stat = 2 * (ll_full - ll_reduced)
            # Degrees of freedom difference
            df_diff = full_result.df_model - reduced_result.df_model
            if df_diff <= 0:
                df_diff = 1 # Fallback
            
            from scipy.stats import chi2
            p_value = 1 - chi2.cdf(lrt_stat, df_diff)
            
            stats = {
                "lrt_statistic": lrt_stat,
                "df_diff": df_diff,
                "p_value": p_value,
                "full_llf": ll_full,
                "reduced_llf": ll_reduced,
                "dropped_predictor_in_lrt": least_sig
            }
        except Exception as e:
            logger.error(f"Error performing LRT: {e}")
            stats = {
                "lrt_statistic": None,
                "df_diff": None,
                "p_value": None,
                "error": str(e)
            }
        
        return full_result, reduced_result, stats

    else:
        # No predictor dropped by VIF
        # Full Model: All three
        predictors = ['search_time', 'target_salience', 'fixation_count']
        formula_full = f"pupil_peak ~ {' + '.join(predictors)} + (1|subject_id)"
        logger.info(f"Fitting Full Model: {formula_full}")
        full_model = smf.mixedlm(formula_full, df, groups=df["subject_id"])
        full_result = full_model.fit()
        
        # Reduced: Remove least significant
        fixed_effects_pvals = {k: v for k, v in full_result.pvalues.items() if k != 'Intercept' and k in predictors}
        least_sig = max(fixed_effects_pvals, key=fixed_effects_pvals.get)
        reduced_predictors = [p for p in predictors if p != least_sig]
        
        formula_reduced = f"pupil_peak ~ {' + '.join(reduced_predictors)} + (1|subject_id)"
        logger.info(f"Fitting Reduced Model: {formula_reduced}")
        reduced_model = smf.mixedlm(formula_reduced, df, groups=df["subject_id"])
        reduced_result = reduced_model.fit()
        
        # LRT
        ll_full = full_result.llf
        ll_reduced = reduced_result.llf
        lrt_stat = 2 * (ll_full - ll_reduced)
        df_diff = full_result.df_model - reduced_result.df_model
        if df_diff <= 0: df_diff = 1
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(lrt_stat, df_diff)
        
        stats = {
            "lrt_statistic": lrt_stat,
            "df_diff": df_diff,
            "p_value": p_value,
            "full_llf": ll_full,
            "reduced_llf": ll_reduced,
            "dropped_predictor_in_lrt": least_sig
        }
        
        return full_result, reduced_result, stats

def extract_model_summary(
    full_result: Any, 
    reduced_result: Optional[Any], 
    stats: Optional[Dict[str, Any]],
    dropped_predictor_vif: Optional[str]
) -> pd.DataFrame:
    """
    Extract fixed effects, SEs, p-values, and LRT stats into a summary DataFrame.
    """
    rows = []
    
    # Extract full model fixed effects
    if full_result is not None:
        params = full_result.params
        stderr = full_result.bse
        pvals = full_result.pvalues
        
        for name, val in params.items():
            if name == 'Intercept':
                continue # Skip intercept for fixed effect table usually, or include? Task says "fixed-effect estimates".
            # Only include fixed effects, not random effects (Group Var)
            if not name.startswith('Group'):
                rows.append({
                    "model_type": "Full",
                    "predictor": name,
                    "estimate": val,
                    "std_error": stderr[name],
                    "p_value": pvals[name]
                })
    
    # Extract reduced model fixed effects if available
    if reduced_result is not None:
        params = reduced_result.params
        stderr = reduced_result.bse
        pvals = reduced_result.pvalues
        
        for name, val in params.items():
            if name == 'Intercept':
                continue
            if not name.startswith('Group'):
                rows.append({
                    "model_type": "Reduced",
                    "predictor": name,
                    "estimate": val,
                    "std_error": stderr[name],
                    "p_value": pvals[name]
                })
    
    # Add LRT row
    if stats:
        rows.append({
            "model_type": "LRT",
            "predictor": "Comparison",
            "estimate": stats.get("lrt_statistic"),
            "std_error": stats.get("df_diff"),
            "p_value": stats.get("p_value")
        })
    
    df_summary = pd.DataFrame(rows)
    if not df_summary.empty:
        df_summary['dropped_predictor'] = dropped_predictor_vif
    
    return df_summary

def run_lme_part3_lrt_and_output() -> pd.DataFrame:
    """
    Main entry point for T021c: Perform LRT and write model_summary.csv.
    """
    logger.info("Starting LRT Analysis (T021c)")
    
    # 1. Load Data
    df = load_processed_data()
    
    # 2. Load VIF Report to see what was dropped
    dropped_predictor_vif = load_vif_report()
    
    # 3. Perform LRT
    full_result, reduced_result, stats = perform_likelihood_ratio_test(df, dropped_predictor_vif)
    
    # 4. Extract Summary
    summary_df = extract_model_summary(full_result, reduced_result, stats, dropped_predictor_vif)
    
    # 5. Ensure output directory exists
    RESULTS_PATH.mkdir(parents=True, exist_ok=True)
    
    # 6. Write to CSV
    summary_df.to_csv(MODEL_SUMMARY_PATH, index=False)
    logger.info(f"Model summary written to {MODEL_SUMMARY_PATH}")
    
    return summary_df

def main():
    """
    CLI entry point.
    """
    try:
        result = run_lme_part3_lrt_and_output()
        print("LRT Analysis completed successfully.")
        print(result)
    except Exception as e:
        logger.error(f"LRT Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

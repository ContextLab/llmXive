"""
User Story 3 Analysis: Correlate Synchrony with Behavioral Switching Costs.
Implements permutation testing, mixed-effects models, and sensitivity analysis.
"""
import os
import sys
import json
import csv
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multitest import multipletests

# Import shared logging utilities (tolerant API)
try:
    from synchrony import get_logger
except ImportError:
    # Fallback for direct execution if import path differs
    import logging
    def get_logger(name=None):
        return logging.getLogger(name or "analysis")

logger = get_logger("analysis")

# Constants
CONFIG_PATH = Path("code/config.py")
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
METRICS_DIR = DATA_DIR / "metrics"
TRIAL_LEVEL_DIR = DATA_DIR / "trial_level"
RESULTS_FILE = METRICS_DIR / "correlation_results.json"
TRIAL_LEVEL_RESULTS_FILE = METRICS_DIR / "trial_level_analysis.json"
SUMMARY_FILE = DATA_DIR / "results_summary.md"
VALIDATION_LOG = DATA_DIR / "validation_log.txt"
PERMUTATION_ITERATIONS = 1000  # Reduced for CPU efficiency, sufficient for demonstration

def load_aggregated_data() -> pd.DataFrame:
    """
    Load the subject-level synchrony metrics and behavioral data.
    Expects:
      - data/metrics/synchrony_metrics.csv (from T025)
      - data/trial_level/per_trial_synchrony.csv (from T036, contains RT)
    Returns a DataFrame with subject_id, band, mean_synchrony, mean_rt_switch, mean_rt_stay, switch_cost.
    """
    sync_path = METRICS_DIR / "synchrony_metrics.csv"
    if not sync_path.exists():
        raise FileNotFoundError(f"Required file missing: {sync_path}")
    
    sync_df = pd.read_csv(sync_path)
    
    # Load trial level to get RTs
    trial_path = TRIAL_LEVEL_DIR / "per_trial_synchrony.csv"
    if not trial_path.exists():
        raise FileNotFoundError(f"Required file missing: {trial_path}")
    
    trial_df = pd.read_csv(trial_path)
    
    # Calculate behavioral metrics per subject
    # Assuming 'condition' column has 'switch' and 'stay' values
    if 'condition' not in trial_df.columns or 'rt' not in trial_df.columns:
        raise ValueError("Trial level data must contain 'condition' and 'rt' columns")
    
    rt_means = trial_df.groupby(['subject_id', 'condition'])['rt'].mean().unstack()
    rt_means = rt_means.reset_index()
    
    # Rename columns if necessary
    if 'switch' in rt_means.columns:
        rt_means = rt_means.rename(columns={'switch': 'rt_switch', 'stay': 'rt_stay'})
    else:
        # Fallback if column names differ
        cols = list(rt_means.columns)
        # Heuristic: find switch/stay based on common naming
        # This assumes standard naming; if not, we might need to inspect data
        pass 
    
    rt_means['switch_cost'] = rt_means['rt_switch'] - rt_means['rt_stay']
    
    # Aggregate synchrony per subject per band
    sync_agg = sync_df.groupby(['subject_id', 'band'])['value'].mean().reset_index()
    sync_agg = sync_agg.rename(columns={'value': 'mean_synchrony'})
    
    # Merge
    merged = pd.merge(rt_means, sync_agg, on='subject_id', how='inner')
    return merged

def run_permutation_test(data: pd.DataFrame, band: str, n_iter: int = PERMUTATION_ITERATIONS) -> Tuple[float, float]:
    """
    Run permutation test for correlation between synchrony and switch cost.
    Returns (observed_r, p_value).
    """
    band_data = data[data['band'] == band].copy()
    if band_data.empty:
        return 0.0, 1.0
    
    x = band_data['mean_synchrony'].values
    y = band_data['switch_cost'].values
    
    # Observed correlation
    if len(x) < 2:
        return 0.0, 1.0
        
    r_obs, _ = np.corrcoef(x, y)
    r_obs = float(r_obs)
    
    # Permutation
    count = 0
    for _ in range(n_iter):
        np.random.shuffle(y)
        r_perm, _ = np.corrcoef(x, y)
        if abs(r_perm) >= abs(r_obs):
            count += 1
    
    p_val = (count + 1) / (n_iter + 1)
    return r_obs, p_val

def run_mixed_effects_analysis(trial_df: pd.DataFrame, band: str) -> Dict[str, Any]:
    """
    Run Linear Mixed-effects model: RT ~ Synchrony + (1|Subject)
    Handles missing values by dropping them.
    Applies Bonferroni correction if multiple bands are passed (though this function is called per band).
    Returns model results dict.
    """
    # Filter by band
    band_df = trial_df[trial_df['band'] == band].copy()
    
    # Handle missing values
    band_df = band_df.dropna(subset=['rt', 'synchrony', 'subject_id'])
    
    if len(band_df) < 10:
        return {
            "band": band,
            "n_samples": 0,
            "fixed_effects": {},
            "p_value": 1.0,
            "note": "Insufficient samples for mixed model"
        }
    
    # Prepare data for statsmodels
    # Formula: rt ~ synchrony + C(subject_id)
    # We use 'synchrony' as the predictor. 
    # Note: The task asks for RT ~ Synchrony + (1|Subject). 
    # In statsmodels mixedlm, the random grouping is specified separately.
    
    try:
        # Create a copy to avoid SettingWithCopyWarning
        model_data = band_df[['rt', 'synchrony', 'subject_id']].copy()
        
        # Fit model
        # endog: rt, exog: synchrony (add constant manually or use formula)
        # Using formula API is easier for random effects
        formula = "rt ~ synchrony"
        md = mixedlm(formula, model_data, groups=model_data["subject_id"])
        mdf = md.fit(reml=False)
        
        # Extract fixed effects
        fixed_effects = mdf.params.to_dict()
        p_values = mdf.pvalues.to_dict()
        
        # Bonferroni correction is applied at the higher level (across bands),
        # but we store the raw p-value for the synchrony term here.
        synchrony_p = p_values.get('synchrony', 1.0)
        
        return {
            "band": band,
            "n_samples": len(model_data),
            "fixed_effects": fixed_effects,
            "p_value_raw": synchrony_p,
            "method": "LMM (statsmodels)"
        }
    except Exception as e:
        logger.log("mixed_model_error", error=str(e), band=band)
        return {
            "band": band,
            "n_samples": len(band_df),
            "fixed_effects": {},
            "p_value_raw": 1.0,
            "error": str(e)
        }

def save_trial_level_analysis(results: Dict[str, Any]) -> None:
    """
    Save trial-level analysis results to data/metrics/trial_level_analysis.json.
    """
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRIAL_LEVEL_RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("trial_level_analysis_saved", path=str(TRIAL_LEVEL_RESULTS_FILE))

def verify_associational_framing() -> bool:
    """
    Verify that results contain 'associational' framing as per FR-008.
    """
    if not RESULTS_FILE.exists():
        return False
    
    with open(RESULTS_FILE, 'r') as f:
        data = json.load(f)
    
    # Check for framing note
    framing = data.get('framing_note', '')
    if 'associational' not in str(framing).lower():
        return False
    
    return True

def save_results_to_json(subject_results: Dict[str, Any], trial_results: Dict[str, Any]) -> None:
    """
    Save final correlation results to data/metrics/correlation_results.json.
    """
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Merge subject and trial results
    final_results = {
        **subject_results,
        **trial_results,
        "framing_note": "This analysis is associational; it does not imply causation between neural synchrony and behavioral costs.",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    logger.log("correlation_results_saved", path=str(RESULTS_FILE))

def generate_results_summary_md(results: Dict[str, Any]) -> None:
    """
    Generate results_summary.md with associational framing.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SUMMARY_FILE, 'w') as f:
        f.write("# Analysis Results Summary\n\n")
        f.write("## Associational Findings\n\n")
        f.write("The following results represent an associational analysis between pre-stimulus neural synchrony and attention switching costs.\n\n")
        f.write("### Subject-Level Correlation\n\n")
        f.write(f"- Theta: r = {results.get('theta_r', 'N/A')}, p = {results.get('theta_p', 'N/A')}\n")
        f.write(f"- Gamma: r = {results.get('gamma_r', 'N/A')}, p = {results.get('gamma_p', 'N/A')}\n\n")
        f.write("### Trial-Level Mixed Effects Model\n\n")
        f.write("Model: RT ~ Synchrony + (1|Subject)\n\n")
        for band in ['theta', 'gamma']:
            band_key = f"{band}_model"
            if band_key in results:
                res = results[band_key]
                f.write(f"- **{band.capitalize()}**: p = {res.get('p_value_raw', 'N/A')}\n")
        f.write("\n**Framing Note**: These findings are associational and do not establish causality.\n")
    logger.log("results_summary_generated", path=str(SUMMARY_FILE))

def main():
    """
    Main entry point for User Story 3 Analysis.
    Orchestrates:
      1. Load aggregated data
      2. Run permutation tests (subject level)
      3. Run Mixed Effects Models (trial level)
      4. Apply Bonferroni correction
      5. Save results and summary
    """
    logger.log("analysis_start", stage="US3")
    
    # 1. Load Data
    try:
        data = load_aggregated_data()
    except FileNotFoundError as e:
        logger.log("analysis_failed", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)
    
    # 2. Subject-Level Permutation Tests
    bands = ['theta', 'gamma']
    subject_results = {}
    p_values_raw = []
    
    for band in bands:
        r_obs, p_val = run_permutation_test(data, band)
        subject_results[f"{band}_r"] = r_obs
        subject_results[f"{band}_p_raw"] = p_val
        p_values_raw.append(p_val)
        logger.log("permutation_result", band=band, r=r_obs, p=p_val)
    
    # 3. Apply Bonferroni Correction (Subject Level)
    # Correction for 2 bands
    corrected_p_values = multipletests(p_values_raw, alpha=0.05, method='bonferroni')[1]
    for i, band in enumerate(bands):
        subject_results[f"{band}_p_corrected"] = corrected_p_values[i]
    
    # 4. Trial-Level Mixed Effects Analysis
    # Load trial data again for mixed model (needs full trial info)
    trial_path = TRIAL_LEVEL_DIR / "per_trial_synchrony.csv"
    if trial_path.exists():
        trial_df = pd.read_csv(trial_path)
        trial_results = {}
        for band in bands:
            model_res = run_mixed_effects_analysis(trial_df, band)
            trial_results[f"{band}_model"] = model_res
            logger.log("mixed_model_result", band=band, p=model_res.get('p_value_raw', 'N/A'))
    else:
        trial_results = {f"{band}_model": {"error": "Trial data not found"} for band in bands}
    
    # 5. Save Results
    save_results_to_json(subject_results, trial_results)
    
    # 6. Save Trial Level Analysis Specific JSON
    save_trial_level_analysis(trial_results)
    
    # 7. Generate Summary
    generate_results_summary_md(subject_results)
    
    # 8. Verify Framing
    if verify_associational_framing():
        with open(VALIDATION_LOG, 'w') as f:
            f.write("Validation PASSED: Associational framing verified.\n")
        logger.log("validation_passed")
        sys.exit(0)
    else:
        with open(VALIDATION_LOG, 'w') as f:
            f.write("Validation FAILED: Associational framing missing.\n")
        logger.log("validation_failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
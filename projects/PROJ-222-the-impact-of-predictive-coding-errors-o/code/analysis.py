import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import statsmodels.formula.api as smf
import pandas as pd
from scipy.stats import norm
import pingouin as pg

def get_data_dir():
    return Path("data")

def get_processed_dir():
    return get_data_dir() / "processed"

def get_analysis_dir():
    return Path("analysis")

def get_config():
    config = {
        "MAX_TRIALS": 5000,
        "POWER_TARGET": 0.8,
        "LAPLACE_ALPHA": 1.0
    }
    return config

def load_preprocessed_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise

def check_normality(data: pd.Series) -> float:
    try:
        _, p = norm.test(data)
        return p
    except Exception as e:
        logging.error(f"Error checking normality: {e}")
        return 1.0  # Return a high p-value to indicate non-normality

def run_wilcoxon_signed_rank(data: pd.Series) -> float:
    try:
        _, p = pg.wilcoxon(data)
        return p
    except Exception as e:
        logging.error(f"Error running Wilcoxon test: {e}")
        return 1.0

def fit_lmm(df: pd.DataFrame) -> Tuple[Any, Any]:
    try:
        model = smf.mixedlm("duration_estimate ~ surprisal + sequence_length + stimulus_modality", df, groups=df["participant_id"]).fit()
        return model
    except Exception as e:
        logging.error(f"Error fitting LMM: {e}")
        return None

def check_binary_cutoffs(df: pd.DataFrame, schema_cols: List[str]) -> List[str]:
    """
    Scans the dataframe for columns that are NOT in the original schema
    but are binary (0/1). These represent researcher-introduced cutoffs.
    """
    binary_cutoffs = []
    for col in df.columns:
        if col not in schema_cols:
            # Check if column is binary (only 0 and 1)
            unique_vals = df[col].dropna().unique()
            if set(unique_vals).issubset({0, 1}):
                binary_cutoffs.append(col)
    return binary_cutoffs

def run_cutoff_sensitivity_analysis(df: pd.DataFrame, cutoff_cols: List[str]) -> Dict[str, Any]:
    """
    Performs a sensitivity sweep on identified binary cutoffs.
    Since the task implies checking if cutoffs were introduced,
    and if so, analyzing them.
    """
    results = {
        "cutoffs_found": cutoff_cols,
        "analysis_performed": False,
        "details": []
    }

    if not cutoff_cols:
        return results

    logging.info(f"Performing sensitivity analysis on cutoffs: {cutoff_cols}")

    for cutoff_col in cutoff_cols:
        # Simple sensitivity check: does the outcome differ significantly
        # between the two groups defined by the cutoff?
        try:
            group_0 = df[df[cutoff_col] == 0]["duration_estimate"]
            group_1 = df[df[cutoff_col] == 1]["duration_estimate"]

            # T-test
            stat, p_val = pg.ttest(group_0, group_1, correction=False)
            
            results["analysis_performed"] = True
            results["details"].append({
                "cutoff_column": cutoff_col,
                "test_statistic": float(stat),
                "p_value": float(p_val)
            })
        except Exception as e:
            logging.warning(f"Failed to analyze cutoff {cutoff_col}: {e}")
            results["details"].append({
                "cutoff_column": cutoff_col,
                "error": str(e)
            })

    return results

def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stream_handler)

    logger.info("Starting analysis pipeline...")

    processed_dir = get_processed_dir()
    standardized_file = processed_dir / "standardized.csv"

    try:
        df = load_preprocessed_data(standardized_file)
    except FileNotFoundError:
        logger.error(f"Standardized data not found at {standardized_file}. Run preprocessing first.")
        sys.exit(1)

    # Check for missing covariates
    if not all(col in df.columns for col in ["sequence_length", "stimulus_modality"]):
        logger.error("Missing required covariates (sequence_length or stimulus_modality).")
        sys.exit(1)

    # Fit LMM
    try:
        model = fit_lmm(df)
        if model is None:
            logger.error("LMM fitting failed.")
            sys.exit(1)
        
        results = {
            "coef_surprisal": float(model.params["surprisal"]),
            "pval_surprisal": float(model.pvalues["surprisal"]),
            "convergence_status": bool(model.converged)
        }
        
        logger.info(f"LMM results: {results}")
        
    except Exception as e:
        logger.error(f"Error during LMM fitting: {e}")
        sys.exit(1)

    # Multiple comparison correction
    needs_correction = True  # Assuming multiple tests are performed (as per T023a logic)
    
    if needs_correction:
        # Benjamini-Hochberg correction
        p_values = [results["pval_surprisal"]]
        adjusted_pvalues, _ = pg.multipletests(p_values, method="fdr_bh")
        results["adjusted_pvalues"] = [float(p) for p in adjusted_pvalues]
        results["correction_applied"] = True
    else:
        results["adjusted_pvalues"] = None
        results["correction_applied"] = False

    # T025c: Cutoff Sensitivity Analysis
    # Define schema columns to compare against
    schema_cols = [
        "duration_estimate", "stimulus_sequence", "participant_id", 
        "surprisal", "sequence_length", "stimulus_modality"
    ]
    
    binary_cutoffs = check_binary_cutoffs(df, schema_cols)
    cutoff_results = run_cutoff_sensitivity_analysis(df, binary_cutoffs)
    
    if not binary_cutoffs:
        logger.info("No new binary cutoffs found. Skipping sensitivity analysis.")
        results["cutoff_sensitivity_status"] = "skipped"
        results["cutoff_sensitivity_skipped"] = True
    else:
        logger.info("New binary cutoffs detected. Sensitivity analysis performed.")
        results["cutoff_sensitivity_status"] = "analyzed"
        results["cutoff_sensitivity_skipped"] = False
        results["cutoff_analysis_details"] = cutoff_results["details"]

    # Write results to JSON file
    analysis_dir = get_analysis_dir()
    results_file = analysis_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Analysis pipeline completed successfully. Results saved to {results_file}")

if __name__ == "__main__":
    main()
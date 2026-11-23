import argparse
import logging
import sys
import csv
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

try:
    import pingouin as pg
except ImportError:
    pg = None

from config import set_seeds
from logger import get_logger

logger = get_logger(__name__)

def load_p300_data(filepath: Path):
    """
    Load P300 measures from CSV into a pandas DataFrame.
    Expected columns include:
      - subject_id
      - condition (or validation_type)
      - p300_amplitude
      - social_anxiety_score
    Additional columns are ignored.
    """
    logger.info(f"Loading P300 data from {filepath}")
    if not filepath.exists():
        raise FileNotFoundError(f"P300 data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Normalise column names
    df = df.rename(columns=lambda x: x.strip().lower())

    # Required columns
    required = {"subject_id", "condition", "p300_amplitude", "social_anxiety_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in P300 data: {missing}")

    # Ensure correct dtypes
    df["p300_amplitude"] = pd.to_numeric(df["p300_amplitude"], errors="coerce")
    df["social_anxiety_score"] = pd.to_numeric(df["social_anxiety_score"], errors="coerce")
    df["subject_id"] = df["subject_id"].astype(str)
    df["condition"] = df["condition"].astype(str)

    # Drop rows with NaNs in critical columns
    before = len(df)
    df = df.dropna(subset=["p300_amplitude", "social_anxiety_score", "condition", "subject_id"])
    after = len(df)
    if after < before:
        logger.warning(f"Dropped {before - after} rows due to missing values.")

    # Create a numeric validation_type column for modeling
    df["validation_type"] = pd.Categorical(df["condition"]).codes
    return df

def fit_linear_mixed_model(df: pd.DataFrame):
    """
    Fit a Linear Mixed-Effects Model:
    p300_amplitude ~ validation_type * social_anxiety_score + (1|subject_id)
    Returns the fitted model object.
    """
    formula = "p300_amplitude ~ validation_type * social_anxiety_score"
    logger.info(f"Fitting mixed-effects model with formula: {formula}")

    try:
        model = smf.mixedlm(formula, df, groups=df["subject_id"])
        result = model.fit(reml=False)  # Use ML for likelihood-based BF later if needed
        logger.info("Model fitting succeeded.")
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def calculate_effect_sizes(model_result):
    """
    Calculate Cohen's d for each fixed effect as estimate / std_error.
    Returns a dict mapping term name to Cohen's d.
    """
    estimates = model_result.fe_params
    std_err = model_result.bse_fe
    effect_sizes = {}
    for term in estimates.index:
        if std_err[term] != 0:
            d = estimates[term] / std_err[term]
        else:
            d = np.nan
        effect_sizes[term] = d
    return effect_sizes

def calculate_bayes_factor(df: pd.DataFrame, model_result):
    """
    Calculate Bayes Factor for the interaction term using pingouin if available.
    Returns a dict mapping term name to Bayes Factor (or np.nan if not computable).
    """
    bfs = {}
    interaction_term = "validation_type:social_anxiety_score"
    if pg is None:
        logger.warning("pingouin not installed – Bayes Factor will be set to NaN.")
        bfs[interaction_term] = np.nan
        return bfs

    # Build a design matrix column for the interaction
    if "validation_type" not in df.columns:
        logger.error("validation_type column missing for Bayes Factor calculation.")
        bfs[interaction_term] = np.nan
        return bfs

    # Ensure validation_type is numeric (0/1)
    df["validation_type_num"] = pd.to_numeric(df["validation_type"], errors="coerce")
    df["interaction"] = df["validation_type_num"] * df["social_anxiety_score"]

    try:
        bf_res = pg.bayesfactor(data=df,
                                x="interaction",
                                y="p300_amplitude")
        bfs[interaction_term] = bf_res["BF10"].iloc[0]
    except Exception as e:
        logger.warning(f"Bayes Factor calculation failed: {e}")
        bfs[interaction_term] = np.nan
    return bfs

def generate_model_summary(model_result, effect_sizes, bayes_factors, output_path: Path):
    """
    Write a CSV file with columns:
    term, estimate, std_error, p_value, holm_p_value, cohen_d, bayes_factor
    """
    logger.info(f"Generating model summary at {output_path}")

    # Fixed effects summary
    summary_df = pd.DataFrame({
        "term": model_result.fe_params.index,
        "estimate": model_result.fe_params.values,
        "std_error": model_result.bse_fe.values,
        "p_value": model_result.pvalues.values
    })

    # Holm-Bonferroni correction across all fixed effects
    corrected = multipletests(summary_df["p_value"], method="holm")
    summary_df["holm_p_value"] = corrected[1]

    # Effect sizes
    summary_df["cohen_d"] = summary_df["term"].map(effect_sizes)

    # Bayes factors (only interaction term expected)
    summary_df["bayes_factor"] = summary_df["term"].map(bayes_factors).fillna("N/A")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_df.to_csv(output_path, index=False, float_format="%.4f")
    logger.info(f"Model summary CSV written to {output_path}")

def run_analyze_phase():
    """
    Executes the full analysis phase:
    - Checks for negative finding or QC failure and aborts if present.
    - Loads P300 data.
    - Fits the LMM.
    - Computes effect sizes and Bayes Factor.
    - Writes model_summary.csv.
    Returns exit code (0 on success, 1 on error).
    """
    logger = get_logger()

    negative_finding_report = Path("data/results/negative_finding_report_v1.pdf")
    qc_failures_log = Path("data/results/qc_failures.log")

    if negative_finding_report.exists() or qc_failures_log.exists():
        logger.info("Negative finding or QC failure detected – skipping statistical modeling.")
        return 0

    p300_path = Path("data/processed/p300_measures.csv")
    if not p300_path.exists():
        logger.error(f"P300 measures file not found at {p300_path}")
        return 1

    try:
        df = load_p300_data(p300_path)
    except Exception as e:
        logger.error(f"Failed to load P300 data: {e}")
        return 1

    # Fit model
    try:
        model_res = fit_linear_mixed_model(df)
    except Exception:
        return 1

    # Effect sizes
    effect_sizes = calculate_effect_sizes(model_res)

    # Bayes Factor
    bayes_factors = calculate_bayes_factor(df, model_res)

    # Write summary
    summary_path = Path("data/results/model_summary.csv")
    generate_model_summary(model_res, effect_sizes, bayes_factors, summary_path)

    return 0

def main():
    parser = argparse.ArgumentParser(description="Statistical analysis of P300 data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    set_seeds(args.seed)

    logger = get_logger()
    logger.info("Starting analysis phase.")
    exit_code = run_analyze_phase()
    logger.info(f"Analysis phase completed with exit code {exit_code}.")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())

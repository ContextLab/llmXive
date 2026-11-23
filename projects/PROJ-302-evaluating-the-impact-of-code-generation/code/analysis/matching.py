import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def calculate_smd(treatment: pd.Series, control: pd.Series) -> float:
    """
    Calculate Standardized Mean Difference (SMD) for a single variable.
    SMD = (mean_treatment - mean_control) / pooled_std
    """
    mean_t = treatment.mean()
    mean_c = control.mean()
    var_t = treatment.var(ddof=1)
    var_c = control.var(ddof=1)
    n_t = len(treatment)
    n_c = len(control)

    if n_t + n_c < 2:
        return 0.0

    pooled_var = ((n_t - 1) * var_t + (n_c - 1) * var_c) / (n_t + n_c - 2)
    if pooled_var <= 0:
        return 0.0

    pooled_std = np.sqrt(pooled_var)
    smd = (mean_t - mean_c) / pooled_std
    return smd

def estimate_propensity_scores(df: pd.DataFrame, covariates: List[str], treatment_col: str = 'author_type') -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    Treatment is 'llm' vs 'human'.
    """
    df = df.copy()
    # Ensure binary treatment
    df['treatment'] = (df[treatment_col] == 'llm').astype(int)

    X = df[covariates].dropna()
    y = df.loc[X.index, 'treatment']

    if X.empty or y.empty:
        logger.warning("No valid data for propensity score estimation.")
        return df

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)

    df.loc[X.index, 'propensity_score'] = model.predict_proba(X_scaled)[:, 1]
    return df

def perform_matching(df: pd.DataFrame, propensity_col: str = 'propensity_score', ratio: int = 1) -> pd.DataFrame:
    """
    Perform nearest neighbor matching without replacement.
    """
    df = df.copy()
    treated = df[df['treatment'] == 1].copy()
    control = df[df['treatment'] == 0].copy()

    if treated.empty or control.empty:
        logger.warning("No treated or control units found.")
        return pd.DataFrame()

    matched_indices = []
    used_control_indices = set()

    for _, t_row in treated.iterrows():
        t_score = t_row[propensity_col]
        available = control[~control.index.isin(used_control_indices)]
        if available.empty:
            break

        distances = np.abs(available[propensity_col] - t_score)
        best_match_idx = distances.idxmin()
        matched_indices.append((t_row.name, best_match_idx))
        used_control_indices.add(best_match_idx)

    if not matched_indices:
        return pd.DataFrame()

    t_indices = [i[0] for i in matched_indices]
    c_indices = [i[1] for i in matched_indices]

    matched_treated = df.loc[t_indices].copy()
    matched_treated['match_group'] = range(len(matched_treated))
    matched_control = df.loc[c_indices].copy()
    matched_control['match_group'] = range(len(matched_control))

    matched_treated['matched'] = True
    matched_control['matched'] = True

    return pd.concat([matched_treated, matched_control])

def check_balance(df_matched: pd.DataFrame, covariates: List[str], treatment_col: str = 'author_type') -> Dict[str, float]:
    """
    Check balance by calculating SMD for each covariate after matching.
    """
    df = df_matched.copy()
    df['treatment'] = (df[treatment_col] == 'llm').astype(int)

    smd_values = {}
    for col in covariates:
        if col not in df.columns:
            continue
        treated_vals = df[df['treatment'] == 1][col]
        control_vals = df[df['treatment'] == 0][col]
        smd = calculate_smd(treated_vals, control_vals)
        smd_values[col] = smd

    return smd_values

def generate_matching_failure_report(smd_values: Dict[str, float], retry_count: int, output_path: str) -> None:
    """
    Generate a JSON report for matching failure and save it.
    """
    report = {
        "status": "failed",
        "reason": "SMD threshold exceeded after retries",
        "max_smd": max(abs(v) for v in smd_values.values()) if smd_values else 0.0,
        "smd_values": smd_values,
        "retry_count": retry_count,
        "threshold": 0.1,
        "timestamp": pd.Timestamp.now().isoformat()
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.error(f"Matching failure report generated at {output_path}")

def run_propensity_matching_with_retry(
    df: pd.DataFrame,
    covariates: List[str],
    treatment_col: str = 'author_type',
    max_retries: int = 3
) -> Tuple[Optional[pd.DataFrame], Dict[str, float], int]:
    """
    Run propensity matching with retry logic on interaction terms.
    Returns (matched_df, smd_values, retry_count).
    If matching fails after all retries, returns (None, smd_values, max_retries).
    """
    logger.info(f"Starting propensity matching with covariates: {covariates}")

    # Initial attempt
    df_with_scores = estimate_propensity_scores(df, covariates, treatment_col)
    if 'propensity_score' not in df_with_scores.columns:
        return None, {}, 0

    matched_df = perform_matching(df_with_scores)
    if matched_df.empty:
        return None, {}, 0

    smd_values = check_balance(matched_df, covariates, treatment_col)
    max_smd = max(abs(v) for v in smd_values.values()) if smd_values else 0.0

    if max_smd <= 0.1:
        return matched_df, smd_values, 0

    logger.warning(f"Initial matching failed: Max SMD = {max_smd:.4f} > 0.1. Starting retries.")

    interaction_terms = [
        ['file_size', 'complexity_score'],
        ['complexity_score', 'activity_level'],
        ['file_size', 'activity_level']
    ]

    for i in range(min(max_retries, len(interaction_terms))):
        logger.info(f"Retry {i+1}: Adding interaction term {interaction_terms[i]}")
        term_1, term_2 = interaction_terms[i]
        if term_1 in df.columns and term_2 in df.columns:
            new_covariates = covariates + [f"{term_1}_{term_2}"]
            df_with_scores = estimate_propensity_scores(df, new_covariates, treatment_col)
            if 'propensity_score' not in df_with_scores.columns:
                continue

            matched_df = perform_matching(df_with_scores)
            if matched_df.empty:
                continue

            smd_values = check_balance(matched_df, new_covariates, treatment_col)
            max_smd = max(abs(v) for v in smd_values.values()) if smd_values else 0.0

            if max_smd <= 0.1:
                logger.info(f"Matching successful on retry {i+1}. Max SMD = {max_smd:.4f}")
                return matched_df, smd_values, i + 1

    logger.error("Matching failed after all retries.")
    return None, smd_values, max_retries

def run_propensity_matching(
    df: pd.DataFrame,
    covariates: List[str],
    treatment_col: str = 'author_type',
    output_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Main entry point for propensity matching.
    Handles retries and failure reporting.
    """
    matched_df, smd_values, retry_count = run_propensity_matching_with_retry(
        df, covariates, treatment_col
    )

    if matched_df is not None:
        logger.info("Matching completed successfully.")
        return matched_df

    # Matching failed
    failure_report_path = output_path or "data/processed/matching_failure_report.json"
    generate_matching_failure_report(smd_values, retry_count, failure_report_path)

    logger.error("HALTING PIPELINE: Matching failed to achieve balance (SMD > 0.1) after retries.")
    sys.exit(1)

def main():
    """
    Main execution function for matching module.
    Expects input from command line or config.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Run Propensity Score Matching')
    parser.add_argument('--input', type=str, required=True, help='Path to input parquet file')
    parser.add_argument('--output', type=str, required=True, help='Path to output parquet file')
    parser.add_argument('--covariates', type=str, nargs='+', default=['file_size', 'complexity_score', 'activity_level'])
    parser.add_argument('--treatment_col', type=str, default='author_type')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading data from {args.input}")
    df = pd.read_parquet(args.input)

    logger.info(f"Running matching with covariates: {args.covariates}")
    matched_df = run_propensity_matching(
        df,
        covariates=args.covariates,
        treatment_col=args.treatment_col,
        output_path=None # Failure report path is hardcoded in function if needed
    )

    if matched_df is not None:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        matched_df.to_parquet(args.output)
        logger.info(f"Matching results saved to {args.output}")

if __name__ == '__main__':
    main()
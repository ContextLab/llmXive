"""
Generalized Linear Mixed Model (GLMM) analysis for AdaPlanBench extension.

This module fits a binomial GLMM to test the interaction between the number of
constraints and the agent architecture (Dual-Track vs. Monolithic) on task success.
"""
import argparse
import json
import os
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.base.model import ConvergenceWarning
import warnings

# Suppress convergence warnings for cleaner logs if the model fits but warns
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Import paths relative to code/
# Note: We assume this script is run from the project root or code/ is in sys.path
# The execution environment sets up sys.path correctly.
try:
    from config import Paths
except ImportError:
    # Fallback for direct execution without config import if needed, though config is standard
    class Paths:
        DATA_PROCESSED = Path("data/processed")

def load_execution_traces(input_path: str) -> pd.DataFrame:
    """
    Load the execution traces CSV.

    Expected columns:
    - task_id: Unique identifier
    - architecture: 'dual_track' or 'monolithic'
    - constraint_count: Integer count of constraints
    - success: Boolean or 0/1 indicating task success
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Execution traces file not found: {input_path}")

    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['task_id', 'architecture', 'constraint_count', 'success']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    # Ensure success is numeric 0/1
    if df['success'].dtype == 'object':
        df['success'] = df['success'].map({True: 1, False: 0, 'True': 1, 'False': 0}).astype(int)
    else:
        df['success'] = df['success'].astype(int)

    # Ensure architecture is categorical
    df['architecture'] = df['architecture'].astype(str)

    return df

def prepare_data_for_glmm(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Prepare data for GLMM: encode categorical variables and create interaction term.

    Returns:
        df_processed: DataFrame ready for model fitting
        stats: Dictionary of basic data statistics
    """
    df_processed = df.copy()

    # Encode architecture: 0 = monolithic, 1 = dual_track (or vice versa, consistent with hypothesis)
    # Let's map: monolithic -> 0, dual_track -> 1
    arch_map = {'monolithic': 0, 'dual_track': 1}
    # Handle potential case variations
    df_processed['architecture_encoded'] = df_processed['architecture'].str.lower().map(arch_map)

    # Fill any NaNs if unexpected architectures exist (should not happen if data is clean)
    if df_processed['architecture_encoded'].isna().any():
        unique_archs = df_processed['architecture'].unique()
        raise ValueError(f"Unknown architecture values found: {unique_archs}")

    # Create interaction term: constraint_count * architecture
    df_processed['interaction'] = df_processed['constraint_count'] * df_processed['architecture_encoded']

    stats = {
        "total_samples": len(df_processed),
        "monolithic_count": int((df_processed['architecture_encoded'] == 0).sum()),
        "dual_track_count": int((df_processed['architecture_encoded'] == 1).sum()),
        "mean_constraints": float(df_processed['constraint_count'].mean()),
        "success_rate_overall": float(df_processed['success'].mean())
    }

    return df_processed, stats

def fit_glmm(df_processed: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a Generalized Linear Mixed Model (using GEE as an approximation for random effects
    in statsmodels, or GLM with fixed effects if random effects are not strictly required
    by the specific stats version, but GEE is preferred for clustered data like tasks).

    Formula: success ~ constraint_count + architecture_encoded + constraint_count:architecture_encoded
    """
    # Define the formula
    formula = "success ~ constraint_count + architecture_encoded + constraint_count:architecture_encoded"

    # Group by task_id if we have multiple runs per task?
    # The execution traces usually have one row per (task, agent) run.
    # If we treat 'task_id' as the cluster for GEE (assuming multiple observations per task if run multiple times,
    # or simply using GEE for robust standard errors on the population average).
    # However, if each task is run exactly once per architecture, we don't have repeated measures per task_id.
    # In that case, a standard GLM (Logistic Regression) is appropriate.
    # Let's check for repeated task_ids.
    n_unique_tasks = df_processed['task_id'].nunique()
    n_rows = len(df_processed)

    result_data = {}
    convergence_status = True
    p_value_interaction = None
    effect_size_interaction = None

    if n_unique_tasks < n_rows:
        # Repeated measures: Use GEE
        groups = df_processed['task_id']
        model = GEE.from_formula(
            formula,
            groups=groups,
            data=df_processed,
            family=sm.families.Binomial(),
            cov_struct=Exchangeable()
        )
    else:
        # Independent observations: Use GLM
        model = GLM.from_formula(
            formula,
            data=df_processed,
            family=sm.families.Binomial()
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.fit()
        convergence_status = result.converged
    except Exception as e:
        # If fitting fails, return failure status
        return {
            "fixed_effects": {},
            "interaction_p_value": None,
            "interaction_effect_size": None,
            "convergence_status": False,
            "error": str(e)
        }

    # Extract coefficients
    params = result.params
    # The interaction term name in the formula is 'constraint_count:architecture_encoded'
    # statsmodels might format it as 'constraint_count:architecture_encoded[T.1]' or similar
    # We need to find the coefficient for the interaction.
    interaction_term = None
    for term in params.index:
        if 'constraint_count:architecture_encoded' in term:
            interaction_term = term
            break

    if interaction_term:
        p_value_interaction = result.pvalues[interaction_term]
        effect_size_interaction = params[interaction_term]
    else:
        # Fallback if term name is slightly different
        # Check for any term containing both
        for term in params.index:
            if 'constraint_count' in term and 'architecture' in term:
                p_value_interaction = result.pvalues[term]
                effect_size_interaction = params[term]
                break

    fixed_effects = {}
    for term in params.index:
        fixed_effects[term] = {
            "estimate": float(params[term]),
            "std_error": float(result.bse[term]),
            "p_value": float(result.pvalues[term])
        }

    return {
        "fixed_effects": fixed_effects,
        "interaction_p_value": float(p_value_interaction) if p_value_interaction is not None else None,
        "interaction_effect_size": float(effect_size_interaction) if effect_size_interaction is not None else None,
        "convergence_status": bool(convergence_status)
    }

def calculate_effect_sizes(result_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate additional effect size metrics if needed (e.g., Odds Ratio).
    """
    effects = result_data.get("fixed_effects", {})
    odds_ratios = {}

    for term, stats in effects.items():
        estimate = stats.get("estimate", 0)
        # Odds ratio = exp(coefficient)
        try:
            odds_ratios[term] = math.exp(estimate)
        except OverflowError:
            odds_ratios[term] = float('inf') if estimate > 0 else 0.0

    return odds_ratios

def run_statistical_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Orchestrate the full GLMM analysis pipeline.
    """
    df_processed, data_stats = prepare_data_for_glmm(df)

    model_results = fit_glmm(df_processed)

    if not model_results.get("convergence_status", False):
        # Log warning but continue if we have partial results
        pass

    effect_sizes = calculate_effect_sizes(model_results)

    return {
        "data_summary": data_stats,
        "model_results": model_results,
        "odds_ratios": effect_sizes,
        "formula": "success ~ constraint_count + architecture_encoded + constraint_count:architecture_encoded"
    }

def main():
    parser = argparse.ArgumentParser(description="Fit GLMM to execution traces")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to execution_traces.csv")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to output JSON results")
    args = parser.parse_args()

    print(f"Loading execution traces from {args.input}...")
    try:
        df = load_execution_traces(args.input)
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print(f"Loaded {len(df)} records.")
    print("Running GLMM analysis...")

    try:
        results = run_statistical_analysis(df)
    except Exception as e:
        print(f"Error running analysis: {e}")
        sys.exit(1)

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing results to {args.output}...")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print("Analysis complete.")
    print(f"Interaction p-value: {results['model_results'].get('interaction_p_value')}")
    print(f"Interaction effect size: {results['model_results'].get('interaction_effect_size')}")
    print(f"Convergence: {results['model_results'].get('convergence_status')}")

if __name__ == "__main__":
    main()

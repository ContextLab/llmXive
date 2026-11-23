"""
GLMM Analysis Module for AdaPlanBench Extension.

This module implements a Generalized Linear Mixed Model (GLMM) with a binomial
link function to test the interaction between the number of constraints and the
agent architecture (monolithic vs. dual-track).

It addresses the core hypothesis: Does explicit constraint tracking (dual-track)
mitigate performance degradation as the number of constraints increases?

Dependencies:
  - statsmodels (for GLMM)
  - pandas
  - numpy

Output:
  - Writes statistical results (p-values, coefficients, convergence status) to JSON.
"""

import argparse
import json
import os
import sys
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Try to import statsmodels; if missing, provide a clear error
try:
    import statsmodels.api as sm
    from statsmodels.genmod.generalized_linear_model import GLM
    from statsmodels.genmod.generalized_estimating_equations import GEE
    from statsmodels.genmod.cov_struct import Exchangeable
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# Constants
DATA_DIR = Path("data/processed")
EXECUTION_TRACES_PATH = DATA_DIR / "execution_traces.csv"
RESULTS_OUTPUT_PATH = DATA_DIR / "statistical-results.json"

# Column names expected in execution_traces.csv
COL_TASK_ID = "task_id"
COL_ARCHITECTURE = "architecture"
COL_CONSTRAINT_COUNT = "constraint_count"
COL_VIOLATION_BOOLEAN = "violation_boolean"
COL_VIOLATION_REASON = "violation_reason"
COL_VIOLATION_STATUS = "violation_status"
COL_FINAL_SCORE = "final_score"

# Filter out 'implicit_unverified' as per FR-009
FILTERED_VIOLATION_STATUS = "implicit_unverified"


def load_execution_traces(input_path: str) -> pd.DataFrame:
    """
    Load the execution traces CSV.
    Validates that the file exists and contains required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Execution traces file not found: {input_path}")

    df = pd.read_csv(path)

    required_cols = [COL_TASK_ID, COL_ARCHITECTURE, COL_CONSTRAINT_COUNT, COL_VIOLATION_BOOLEAN, COL_FINAL_SCORE]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")

    # Filter out rows where violation_status is 'implicit_unverified'
    # This is critical for the primary analysis as per FR-009
    if COL_VIOLATION_STATUS in df.columns:
        df = df[df[COL_VIOLATION_STATUS] != FILTERED_VIOLATION_STATUS]
    else:
        # If column doesn't exist, assume no filtering needed (legacy data)
        pass

    return df


def prepare_data_for_glmm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the DataFrame for GLMM analysis.
    - Encode architecture as a dummy variable (0: monolithic, 1: dual-track)
    - Ensure constraint_count is numeric
    - Ensure violation_boolean is numeric (0/1)
    """
    df = df.copy()

    # Encode architecture
    # We want to test: Dual-Track vs Monolithic.
    # Let's set Monolithic as reference (0) and Dual-Track as 1.
    if COL_ARCHITECTURE in df.columns:
        df['arch_encoded'] = df[COL_ARCHITECTURE].map({
            'monolithic': 0,
            'dual_track': 1
        })
    else:
        raise ValueError(f"Column '{COL_ARCHITECTURE}' not found in dataframe.")

    # Ensure numeric types
    df[COL_CONSTRAINT_COUNT] = pd.to_numeric(df[COL_CONSTRAINT_COUNT], errors='coerce')
    df[COL_VIOLATION_BOOLEAN] = pd.to_numeric(df[COL_VIOLATION_BOOLEAN], errors='coerce')
    df['arch_encoded'] = pd.to_numeric(df['arch_encoded'], errors='coerce')

    # Drop rows with NaN in critical columns
    df = df.dropna(subset=[COL_CONSTRAINT_COUNT, COL_VIOLATION_BOOLEAN, 'arch_encoded'])

    return df


def fit_glmm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a GLMM (or GEE as a robust approximation if mixed models are too heavy)
    to test the interaction between constraint_count and architecture.

    Model:
      Logit(P(violation)) = beta0 + beta1*ConstraintCount + beta2*Architecture + beta3*(ConstraintCount * Architecture)

    We use a binomial family with logit link.
    Since we have repeated measures? (No, each row is a task execution).
    However, tasks might be grouped by difficulty or original dataset ID.
    If we assume independence, a standard GLM with interaction is sufficient.
    If we assume task_id is a random effect, we need MixedLM.

    Given the constraints of typical execution environments and the nature of
    the data (one row per task execution), we will use GEE with an exchangeable
    correlation structure if we group by a hypothetical 'task_group' (e.g., task_id).
    But since task_id is unique per row in this flattened view, GEE/MixedLM
    reduces to GLM unless there are repeated measures per task_id.

    Wait, the data is one row per task execution. If we ran multiple agents on the same task,
    we have repeated measures.
    Let's assume the input df has multiple rows per task_id (one for monolithic, one for dual_track).
    We can use task_id as the cluster for GEE.

    If task_id is unique per row (no pairing), then GEE/MixedLM is effectively GLM.
    We will attempt GEE with task_id as cluster to be safe, falling back to GLM if needed.
    """
    if not HAS_STATSMODELS:
        return {
            "error": "statsmodels is not installed. Please install it via requirements.txt.",
            "converged": False
        }

    # Check for repeated measures
    unique_tasks = df[COL_TASK_ID].nunique()
    total_rows = len(df)

    if unique_tasks == total_rows:
        # No repeated measures per task_id. Use GLM.
        model_type = "GLM"
        # Formula: violation ~ constraint_count * architecture
        formula = f"{COL_VIOLATION_BOOLEAN} ~ {COL_CONSTRAINT_COUNT} * arch_encoded"
        model = GLM(
            df[COL_VIOLATION_BOOLEAN],
            sm.add_constant(sm.tools.factorize(df[COL_CONSTRAINT_COUNT].astype(str))[0]), # Simplified for interaction
            family=sm.families.Binomial()
        )
        # Actually, let's build the design matrix manually for interaction to be precise
        # X = [1, count, arch, count*arch]
        X = df[[COL_CONSTRAINT_COUNT, 'arch_encoded']].copy()
        X['intercept'] = 1
        X['interaction'] = X[COL_CONSTRAINT_COUNT] * X['arch_encoded']
        X = X[['intercept', COL_CONSTRAINT_COUNT, 'arch_encoded', 'interaction']]

        model = GLM(
            df[COL_VIOLATION_BOOLEAN],
            X,
            family=sm.families.Binomial()
        )
        result = model.fit()
    else:
        # Repeated measures exist. Use GEE with task_id as cluster.
        model_type = "GEE"
        formula = f"{COL_VIOLATION_BOOLEAN} ~ {COL_CONSTRAINT_COUNT} * arch_encoded"
        # GEE requires a groups column
        gee_model = GEE(
            df[COL_VIOLATION_BOOLEAN],
            sm.add_constant(df[[COL_CONSTRAINT_COUNT, 'arch_encoded']]), # This is tricky with interaction in formula string for GEE
            groups=df[COL_TASK_ID],
            family=sm.families.Binomial(),
            cov_struct=Exchangeable()
        )
        # GEE formula handling is complex, let's stick to the manual design matrix approach if possible
        # Or use the formula API if available.
        # Let's try the formula API for GEE which is supported in newer statsmodels
        try:
            gee_model = GEE.from_formula(
                formula,
                groups=df[COL_TASK_ID],
                data=df,
                family=sm.families.Binomial(),
                cov_struct=Exchangeable()
            )
            result = gee_model.fit()
        except Exception:
            # Fallback to GLM if GEE fails (e.g., convergence issues or version mismatch)
            model_type = "GLM (Fallback)"
            X = df[[COL_CONSTRAINT_COUNT, 'arch_encoded']].copy()
            X['intercept'] = 1
            X['interaction'] = X[COL_CONSTRAINT_COUNT] * X['arch_encoded']
            X = X[['intercept', COL_CONSTRAINT_COUNT, 'arch_encoded', 'interaction']]
            model = GLM(df[COL_VIOLATION_BOOLEAN], X, family=sm.families.Binomial())
            result = model.fit()

    # Extract results
    params = result.params
    pvalues = result.pvalues
    converged = result.converged if hasattr(result, 'converged') else True

    # Map parameter names to our variables
    # Expected: const, constraint_count, arch_encoded, constraint_count:arch_encoded
    # We need to find the interaction term p-value specifically
    interaction_key = None
    for key in params.index:
        if 'interaction' in key.lower() or ('*' in key and COL_CONSTRAINT_COUNT in key and 'arch' in key):
            interaction_key = key
            break
    
    # If manual matrix used, keys are 'intercept', 'constraint_count', 'arch_encoded', 'interaction'
    if interaction_key is None and 'interaction' in params.index:
        interaction_key = 'interaction'

    interaction_pvalue = None
    interaction_coef = None
    if interaction_key and interaction_key in params.index:
        interaction_pvalue = float(pvalues[interaction_key])
        interaction_coef = float(params[interaction_key])

    return {
        "model_type": model_type,
        "converged": bool(converged),
        "coefficients": {k: float(v) for k, v in params.items()},
        "p_values": {k: float(v) for k, v in pvalues.items()},
        "interaction_p_value": interaction_pvalue,
        "interaction_coefficient": interaction_coef,
        "sample_size": int(len(df)),
        "unique_tasks": int(unique_tasks)
    }


def calculate_effect_sizes(df: pd.DataFrame, results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate basic effect sizes (e.g., Cohen's d for the main effect of architecture
    at a fixed constraint count, or odds ratios from the GLM).
    For now, we return the Odds Ratio for the architecture main effect.
    """
    coefs = results.get("coefficients", {})
    # Odds ratio = exp(coef)
    odds_ratios = {}
    for k, v in coefs.items():
        try:
            odds_ratios[k] = math.exp(v)
        except (OverflowError, ValueError):
            odds_ratios[k] = None
    
    return {
        "odds_ratios": odds_ratios
    }


def run_statistical_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main entry point for the statistical analysis.
    1. Load data.
    2. Prepare data.
    3. Fit GLMM.
    4. Calculate effect sizes.
    5. Save results.
    """
    print(f"Running GLMM analysis on {input_path}...")
    
    try:
        df_raw = load_execution_traces(input_path)
        print(f"Loaded {len(df_raw)} rows after filtering implicit_unverified.")
        
        if len(df_raw) == 0:
            raise ValueError("No data remaining after filtering. Cannot run GLMM.")

        df_prep = prepare_data_for_glmm(df_raw)
        print(f"Prepared {len(df_prep)} rows for GLMM.")

        glmm_results = fit_glmm(df_prep)
        effect_sizes = calculate_effect_sizes(df_prep, glmm_results)

        final_report = {
            "input_file": input_path,
            "timestamp": "N/A", # Can add datetime if needed
            "sample_size": glmm_results.get("sample_size", 0),
            "unique_tasks": glmm_results.get("unique_tasks", 0),
            "model_fit": {
                "converged": glmm_results.get("converged", False),
                "model_type": glmm_results.get("model_type", "Unknown")
            },
            "interaction_effect": {
                "p_value": glmm_results.get("interaction_p_value"),
                "coefficient": glmm_results.get("interaction_coefficient"),
                "interpretation": "Significant p-value (<0.05) indicates that the effect of constraints on violations differs by architecture."
            },
            "main_effects": {
                "coefficients": glmm_results.get("coefficients", {}),
                "p_values": glmm_results.get("p_values", {}),
                "odds_ratios": effect_sizes.get("odds_ratios", {})
            }
        }

        # Write to JSON
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        print(f"Statistical results written to {output_path}")
        return final_report

    except Exception as e:
        error_report = {
            "error": str(e),
            "success": False
        }
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        raise


def main():
    parser = argparse.ArgumentParser(description="Run GLMM analysis on execution traces.")
    parser.add_argument("--input", type=str, default=str(EXECUTION_TRACES_PATH),
                        help="Path to the execution traces CSV (default: data/processed/execution_traces.csv)")
    parser.add_argument("--output", type=str, default=str(RESULTS_OUTPUT_PATH),
                        help="Path to output JSON results (default: data/processed/statistical-results.json)")
    
    args = parser.parse_args()

    if not HAS_STATSMODELS:
        print("ERROR: statsmodels is required but not installed.")
        print("Please install it: pip install statsmodels")
        sys.exit(1)

    run_statistical_analysis(args.input, args.output)


if __name__ == "__main__":
    main()
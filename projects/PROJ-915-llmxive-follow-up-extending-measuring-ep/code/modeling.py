import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests
from statsmodels.discrete.discrete_model import Logit
from statsmodels.tools import add_constant

from config import get_config

def load_prepared_data() -> pd.DataFrame:
    """Load labeled responses for modeling."""
    file_path = Path("data/interim/labeled_responses.csv")
    if not file_path.exists():
        raise FileNotFoundError("Labeled responses file not found.")
    return pd.read_csv(file_path)

def prepare_model_a_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for Model A: Adherent vs Non-Adherent."""
    # Exclude rows with undefined ratios
    df = df[df["is_undefined_ratio"] == False]
    df = df[df["adherence_label"] != 2]  # Exclude refusals
    df["target"] = (df["adherence_label"] == 1).astype(int)
    return df

def prepare_model_b_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for Model B: Refusal vs Non-Refusal."""
    df = df[df["is_undefined_ratio"] == False]
    df["target"] = (df["adherence_label"] == 2).astype(int)
    return df

def detect_perfect_separation(df: pd.DataFrame, target_col: str, features: List[str]) -> bool:
    """Detect perfect separation in logistic regression."""
    try:
        X = df[features].dropna()
        y = df.loc[X.index, target_col]
        if len(y.unique()) < 2:
            return True
        # Simple check: if any feature perfectly predicts target
        for col in features:
            if col in X.columns:
                grouped = y.groupby(X[col]).mean()
                if grouped.min() == 0 and grouped.max() == 1:
                    return True
        return False
    except Exception:
        return False

def run_logistic_regression(df: pd.DataFrame, features: List[str], target_col: str) -> Dict[str, Any]:
    """Run logistic regression."""
    X = df[features].dropna()
    y = df.loc[X.index, target_col]
    X = add_constant(X)
    
    model = Logit(y, X)
    result = model.fit(disp=False)
    return {
        "coefficients": result.params.to_dict(),
        "pvalues": result.pvalues.to_dict(),
        "converged": result.converged
    }

def run_firth_regression(df: pd.DataFrame, features: List[str], target_col: str) -> Dict[str, Any]:
    """Run Firth's penalized logistic regression (placeholder)."""
    # Placeholder for firth-logistic implementation
    logging.warning("Firth regression not fully implemented; using standard logistic.")
    return run_logistic_regression(df, features, target_col)

def log_convergence(result: Dict[str, Any]) -> None:
    """Log convergence status."""
    if not result["converged"]:
        logging.warning("Logistic regression did not converge.")

def apply_holm_bonferroni(pvalues: List[float]) -> List[float]:
    """Apply Holm-Bonferroni correction."""
    _, p_adj, _, _ = multipletests(pvalues, method="holm")
    return p_adj.tolist()

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save regression results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame([results])
    df.to_csv(output_path, index=False)

def run_modeling_pipeline() -> None:
    """Main modeling pipeline."""
    df = load_prepared_data()
    
    # Model A
    df_a = prepare_model_a_data(df)
    features_a = ["modal_verb_count", "citation_count", "imperative_declarative_ratio"]
    features_a = [f for f in features_a if f in df_a.columns]
    
    if detect_perfect_separation(df_a, "target", features_a):
        logging.warning("Perfect separation detected in Model A. Using Firth regression.")
        result_a = run_firth_regression(df_a, features_a, "target")
    else:
        result_a = run_logistic_regression(df_a, features_a, "target")
    
    log_convergence(result_a)
    result_a["p_adj"] = apply_holm_bonferroni(list(result_a["pvalues"].values()))
    
    # Model B
    df_b = prepare_model_b_data(df)
    features_b = ["modal_verb_count", "citation_count"]
    features_b = [f for f in features_b if f in df_b.columns]
    
    if detect_perfect_separation(df_b, "target", features_b):
        logging.warning("Perfect separation detected in Model B. Using Firth regression.")
        result_b = run_firth_regression(df_b, features_b, "target")
    else:
        result_b = run_logistic_regression(df_b, features_b, "target")
    
    log_convergence(result_b)
    result_b["p_adj"] = apply_holm_bonferroni(list(result_b["pvalues"].values()))
    
    # Save results
    save_results(result_a, Path("data/results/regression_results_model_a.csv"))
    save_results(result_b, Path("data/results/regression_results_model_b.csv"))
    
    logging.info("Modeling pipeline completed.")

def main():
    """Entry point for modeling script."""
    run_modeling_pipeline()

if __name__ == "__main__":
    main()
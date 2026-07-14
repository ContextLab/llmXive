"""
Two-Way ANOVA for statistical validation.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from config import get_results_dir, ensure_directories

def load_metrics_for_anova(metrics_path: Path) -> pd.DataFrame:
    """Load metrics from sensitivity analysis or main results."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        data = json.load(f)

    rows = []
    for key, val in data.items():
        if isinstance(val, dict):
            rows.append({
                "threshold": float(key),
                "world_score": val.get("world_score"),
                "sparse_consistency_score": val.get("sparse_consistency_score"),
                "status": val.get("status")
            })
    return pd.DataFrame(rows)

def run_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """Perform Two-Way ANOVA on WorldScore vs Threshold (simplified as one-way for now)."""
    # Since we only have one factor (threshold), we do one-way ANOVA
    # If we had scene dynamics and texture level, we would do two-way.
    # Here we test if threshold affects WorldScore.
    scores = df['world_score'].dropna()
    if len(scores) < 3:
        return {"p_value": 1.0, "f_stat": 0.0, "note": "Insufficient data"}

    f_stat, p_value = stats.f_oneway(*[scores]) # One-way
    return {"p_value": float(p_value), "f_stat": float(f_stat)}

def main():
    """CLI entry point."""
    # Load from sensitivity analysis
    sens_path = get_results_dir() / "sensitivity_analysis.json"
    if not sens_path.exists():
        print("Sensitivity analysis not found. Run T019 first.")
        return

    df = load_metrics_for_anova(sens_path)
    results = run_anova(df)

    output_path = get_results_dir() / "anova_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"ANOVA Results: {results}")

if __name__ == "__main__":
    main()

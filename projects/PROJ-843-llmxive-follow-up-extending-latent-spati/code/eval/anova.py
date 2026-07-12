"""
Implementation of Task T018: Two-Way ANOVA for US3.

Performs Two-Way ANOVA on metrics vs. (Scene Dynamics, Texture Level).
Outputs p-value for interaction effects (significance threshold p < 0.05).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import project config
from config import get_results_dir
from eval.metrics import load_npy_safe

def load_metrics_for_anova() -> Optional[pd.DataFrame]:
    """
    Loads metrics from data/results/metrics.json (produced by T017)
    and structures them for ANOVA analysis.

    Expected structure in metrics.json:
    {
      "world_score": [values per sequence],
      "sparse_consistency": [values per sequence],
      "metadata": [
        {"sequence_id": "seq_001", "stratum": "Static-High", ...},
        ...
      ]
    }
    """
    metrics_path = get_results_dir() / "metrics.json"
    if not metrics_path.exists():
        print(f"Error: {metrics_path} not found. Run T017 first.")
        return None

    with open(metrics_path, 'r') as f:
        data = json.load(f)

    # We expect a list of results or a dict with lists
    # Based on T017, it likely outputs a list of dicts or a structured dict.
    # We assume the structure allows extracting values and metadata.
    
    if "results" in data:
        results_list = data["results"]
    elif "world_score" in data and "sparse_consistency" in data:
        # Fallback if flattened
        results_list = []
        num_seqs = len(data["world_score"])
        for i in range(num_seqs):
            results_list.append({
                "world_score": data["world_score"][i],
                "sparse_consistency": data["sparse_consistency"][i],
                "stratum": data.get("metadata", [{}]*num_seqs)[i].get("stratum", "Unknown")
            })
    else:
        # Try to interpret as a list directly if the file format varies
        results_list = data.get("results", data) if isinstance(data, list) else [data]

    df = pd.DataFrame(results_list)
    
    # Ensure we have the necessary columns
    required_cols = ["world_score", "sparse_consistency", "stratum"]
    if not all(col in df.columns for col in required_cols):
        # Attempt to parse stratum from sequence_id if missing, or raise error
        print(f"Error: Missing required columns in metrics.json. Found: {df.columns.tolist()}")
        return None

    # Parse stratum into factors: Scene Dynamics (Static, Slow, Fast) and Texture Level (High, Low)
    def parse_stratum(stratum_str):
        # Expected format: "Dynamics-Texture" e.g., "Static-High", "Fast-Low"
        parts = stratum_str.split("-")
        if len(parts) == 2:
            return parts[0], parts[1]
        return "Unknown", "Unknown"

    df['dynamics'], df['texture'] = zip(*df['stratum'].apply(parse_stratum))
    
    # Filter out any rows with invalid parsing to ensure clean ANOVA
    df = df[(df['dynamics'] != "Unknown") & (df['texture'] != "Unknown")]
    
    if len(df) == 0:
        print("Error: No valid data rows found for ANOVA after filtering.")
        return None

    return df

def run_anova(df: pd.DataFrame, metric: str = "world_score") -> Dict[str, Any]:
    """
    Runs Two-Way ANOVA on the specified metric.
    
    Args:
        df: DataFrame with columns 'metric', 'dynamics', 'texture'
        metric: Name of the metric column to analyze (e.g., "world_score")
        
    Returns:
        Dictionary containing ANOVA table and specific p-values.
    """
    formula = f"{metric} ~ C(dynamics) * C(texture)"
    model = ols(formula, data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    # Extract p-values
    p_dynamics = anova_table.loc["C(dynamics)", "PR(>F)"]
    p_texture = anova_table.loc["C(texture)", "PR(>F)"]
    p_interaction = anova_table.loc["C(dynamics):C(texture)", "PR(>F)"] if "C(dynamics):C(texture)" in anova_table.index else np.nan
    
    return {
        "metric": metric,
        "anova_table": anova_table.to_dict(),
        "p_dynamics": p_dynamics,
        "p_texture": p_texture,
        "p_interaction": p_interaction,
        "interaction_significant": p_interaction < 0.05 if not np.isnan(p_interaction) else False
    }

def main():
    """
    Main entry point for T018.
    Loads metrics, runs ANOVA for both WorldScore and Sparse-Consistency,
    and saves results to data/results/anova_results.json.
    """
    print("Starting T018: Two-Way ANOVA Analysis")
    
    df = load_metrics_for_anova()
    if df is None:
        print("Failed to load metrics data. Aborting.")
        sys.exit(1)

    results = {
        "analysis_type": "Two-Way ANOVA",
        "factors": ["Scene Dynamics", "Texture Level"],
        "significance_threshold": 0.05,
        "samples_analyzed": len(df)
    }

    metrics_to_analyze = ["world_score", "sparse_consistency"]
    
    for metric in metrics_to_analyze:
        if metric not in df.columns:
            print(f"Skipping {metric}: column not found.")
            continue
        
        print(f"Running ANOVA for {metric}...")
        try:
            anova_result = run_anova(df, metric)
            results[metric] = anova_result
        except Exception as e:
            print(f"Error running ANOVA for {metric}: {e}")
            results[metric] = {"error": str(e)}

    # Save results
    output_path = get_results_dir() / "anova_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"ANOVA results saved to {output_path}")
    
    # Print summary to stdout
    print("\n--- ANOVA Summary ---")
    for metric in metrics_to_analyze:
        if metric in results and "p_interaction" in results[metric]:
            p_val = results[metric]["p_interaction"]
            sig = "YES" if results[metric].get("interaction_significant") else "NO"
            print(f"{metric}: Interaction p-value = {p_val:.4f} (Significant: {sig})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
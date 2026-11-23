"""
Two-Way ANOVA for Metric Analysis (T018)

Performs Two-Way ANOVA on metrics vs (Scene Dynamics, Texture Level).
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import warnings

# Local imports
from config import get_results_dir, ensure_directories
from utils.seeds import set_global_seed
from utils.memory_monitor import MemoryMonitor
from scipy import stats

RESULTS_FILE = "anova_results.json"

def load_metrics_for_anova(metrics_path: Path) -> pd.DataFrame:
    """
    Load metrics from the metrics.json file and prepare for ANOVA.
    
    Expected format: List of records with 'scenario', 'world_score', 'sparse_consistency_score', etc.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    # Ensure data is a list
    if isinstance(data, dict):
        data = [data]
    
    df = pd.DataFrame(data)
    
    # Filter out rows with missing scores
    valid_cols = ['world_score', 'sparse_consistency_score']
    for col in valid_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in metrics file")
        df = df[df[col].notna()]
    
    return df

def run_anova(df: pd.DataFrame, metric_col: str = "world_score") -> Dict[str, Any]:
    """
    Perform Two-Way ANOVA on the specified metric.
    
    Factors: Scene Dynamics (Static/Slow/Fast), Texture Level (High/Low)
    Returns ANOVA table and p-values.
    """
    # Check for required columns
    required_cols = ['scenario', metric_col]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found")
    
    # Extract factors from scenario string (e.g., "Static-High")
    # Assume format: "{Dynamics}-{Texture}"
    df['dynamics'] = df['scenario'].str.extract(r'([^-]+)-')
    df['texture'] = df['scenario'].str.extract(r'-([^-]+)')
    
    # Drop rows with missing factors
    df = df.dropna(subset=['dynamics', 'texture'])
    
    if len(df) < 4:
        raise ValueError("Insufficient data for ANOVA (need at least 4 groups)")
    
    # Perform Two-Way ANOVA
    # Using statsmodels for proper interaction term
    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        
        model = ols(f"{metric_col} ~ C(dynamics) * C(texture)", data=df).fit()
        anova_table = anova_lm(model, typ=2)
        
        # Extract p-values
        interaction_p = None
        dynamics_p = None
        texture_p = None
        
        # Find interaction term
        for idx, row in anova_table.iterrows():
            if 'dynamics' in str(idx) and 'texture' in str(idx):
                interaction_p = row['PR(>F)']
            elif 'dynamics' in str(idx):
                dynamics_p = row['PR(>F)']
            elif 'texture' in str(idx):
                texture_p = row['PR(>F)']
        
        return {
            "anova_table": anova_table.to_dict(),
            "interaction_p_value": interaction_p,
            "dynamics_p_value": dynamics_p,
            "texture_p_value": texture_p,
            "significant_interaction": interaction_p is not None and interaction_p < 0.05,
            "df": len(df)
        }
        
    except ImportError:
        # Fallback to scipy if statsmodels not available
        # This is a simplified version without interaction
        print("Warning: statsmodels not available. Using simplified scipy ANOVA.")
        grouped = df.groupby(['dynamics', 'texture'])[metric_col]
        
        # Extract groups
        groups = [group for name, group in grouped]
        
        if len(groups) < 2:
            raise ValueError("Need at least 2 groups for ANOVA")
        
        f_stat, p_val = stats.f_oneway(*groups)
        
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "method": "scipy_f_oneway",
            "df": len(df)
        }

def main():
    """Main entry point for ANOVA analysis."""
    set_global_seed(42)
    
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    
    metrics_path = results_dir / "metrics.json"
    output_path = results_dir / RESULTS_FILE
    
    try:
        # Load data
        df = load_metrics_for_anova(metrics_path)
        print(f"Loaded {len(df)} valid records for ANOVA")
        
        # Run ANOVA for both primary metrics
        results = {}
        
        for metric in ["world_score", "sparse_consistency_score"]:
            if metric in df.columns:
                print(f"\nRunning ANOVA for {metric}...")
                try:
                    anova_result = run_anova(df, metric_col=metric)
                    results[metric] = anova_result
                    print(f"  Interaction p-value: {anova_result.get('interaction_p_value')}")
                except Exception as e:
                    print(f"  Error running ANOVA for {metric}: {e}")
                    results[metric] = {"error": str(e)}
            else:
                print(f"  Skipping {metric}: column not found")
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nANOVA results saved to {output_path}")
        
        # Print summary
        print("\n--- ANOVA Summary ---")
        for metric, res in results.items():
            if "error" in res:
                print(f"{metric}: ERROR - {res['error']}")
            else:
                p = res.get("interaction_p_value")
                sig = res.get("significant_interaction", False)
                print(f"{metric}: Interaction p={p:.4f} (Significant: {sig})")
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that metrics.json exists in data/results/ before running ANOVA.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

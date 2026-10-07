"""
Repeated Measures ANOVA analysis script.
"""
import os
import sys
import json
import argparse
import random
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.helpers import get_project_root

def get_project_root() -> Path:
    """Get project root."""
    return Path(__file__).resolve().parent.parent.parent

def get_cleaned_csv_path() -> Path:
    """Get path to cleaned CSV."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_anova_results_path() -> Path:
    """Get path for ANOVA results JSON."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def load_wide_data(input_path: str | Path) -> list[dict]:
    """Load wide data from CSV."""
    import csv
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def calculate_partial_eta_squared(ss_effect: float, ss_error: float) -> float:
    """Calculate partial eta squared."""
    if ss_error == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)

def run_repeated_measures_anova(data: list[dict]) -> dict:
    """
    Run Repeated Measures ANOVA.
    Note: Since pingouin might not be installed in all environments or we need
    a pure numpy implementation for the "real" calculation without heavy deps,
    we will implement a simplified version or use statsmodels if available.
    However, the spec mentions pingouin. We will try to import it, and if not,
    use a fallback calculation or raise a clear error.
    
    For this implementation, we assume the data is in wide format with columns:
    participant_id, professional_credibility, minimalist_credibility, ...
    """
    try:
        import pingouin as pg
        import pandas as pd
        
        df = pd.DataFrame(data)
        
        # We need to melt the data to long format for pingouin
        # Identify stimulus columns
        stimulus_cols = [c for c in df.columns if c.endswith("_credibility")]
        if not stimulus_cols:
            raise ValueError("No credibility columns found in data.")
        
        # Melt
        id_vars = ["participant_id"]
        # Keep other metadata if needed, but for ANOVA we need long format
        df_long = df.melt(id_vars=id_vars, value_vars=stimulus_cols, 
                          var_name="condition", value_name="score")
        
        # Extract condition name (e.g., "professional_credibility" -> "professional")
        df_long["condition"] = df_long["condition"].str.replace("_credibility", "")
        
        # Run ANOVA
        # Formula: Score ~ Condition + Error(Participant/Condition)
        # pingouin.rm_anova(dv='score', within='condition', subject='participant_id', data=df_long)
        
        # Check if data is balanced
        if not df_long.groupby(["participant_id", "condition"]).size().eq(1).all():
            # Unbalanced, might need mixed model, but for simple ANOVA we proceed with available
            pass

        aov = pg.rm_anova(dv='score', within='condition', subject='participant_id', data=df_long, detailed=True)
        
        if aov.empty:
            return {
                "f_statistic": 0.0,
                "p_value": 1.0,
                "eta_squared": 0.0,
                "degrees_of_freedom": [0, 0],
                "error": "ANOVA result empty"
            }

        row = aov.iloc[0]
        f_stat = float(row['F'])
        p_val = float(row['p-unc'])
        
        # Calculate eta squared if not present
        # pingouin returns np2 (partial eta squared) usually
        eta_sq = float(row['np2']) if 'np2' in row else calculate_partial_eta_squared(
            float(row['SS_between']), float(row['SS_error'])
        )
        
        df_num = int(row['DFn'])
        df_den = int(row['DFd'])

        return {
            "f_statistic": f_stat,
            "p_value": p_val,
            "eta_squared": eta_sq,
            "degrees_of_freedom": [df_num, df_den],
            "method": "pingouin.rm_anova"
        }

    except ImportError:
        # Fallback: Simple calculation or raise error
        # Since the task requires real analysis, we cannot fake it.
        # If pingouin is missing, we raise an error.
        raise RuntimeError("pingouin library is required for ANOVA. Install it via pip.")

def run_conditional_pairwise_tests(data: list[dict], anova_results: dict) -> dict:
    """Run pairwise tests only if ANOVA is significant."""
    if anova_results.get("p_value", 1.0) >= 0.05:
        return {"skipped": True, "reason": "ANOVA not significant"}

    try:
        import pingouin as pg
        import pandas as pd

        df = pd.DataFrame(data)
        stimulus_cols = [c for c in df.columns if c.endswith("_credibility")]
        df_long = df.melt(id_vars=["participant_id"], value_vars=stimulus_cols,
                          var_name="condition", value_name="score")
        df_long["condition"] = df_long["condition"].str.replace("_credibility", "")

        # Bonferroni correction
        n_comparisons = len(stimulus_cols) * (len(stimulus_cols) - 1) / 2
        bonf_alpha = 0.05 / n_comparisons

        pairwise = pg.pairwise_ttests(dv='score', within='condition', 
                                      subject='participant_id', data=df_long,
                                      padjust='bonf')
        
        results = []
        for _, row in pairwise.iterrows():
            results.append({
                "comparison": f"{row['A']} vs {row['B']}",
                "p_value": float(row['p-unc']),
                "p_adjusted": float(row['p-bonf']) if 'p-bonf' in row else float(row['p-unc']),
                "cohen_d": float(row['Cohens-d']) if 'Cohens-d' in row else None,
                "significant": float(row['p-unc']) < 0.05,
                "bonferroni_alpha": bonf_alpha
            })

        return {
            "skipped": False,
            "pairwise_comparisons": results,
            "bonferroni_alpha": bonf_alpha,
            "num_comparisons": int(n_comparisons)
        }

    except ImportError:
        raise RuntimeError("pingouin library is required for pairwise tests.")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Repeated Measures ANOVA")
    parser.add_argument("--input", required=True, help="Path to clean data CSV")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Ensure output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {input_path}...")
    data = load_wide_data(input_path)
    print(f"Loaded {len(data)} participants.")

    if not data:
        # Handle empty data
        result = {
            "f_statistic": 0.0,
            "p_value": 1.0,
            "eta_squared": 0.0,
            "degrees_of_freedom": [0, 0],
            "error": "No data to analyze"
        }
    else:
        print("Running ANOVA...")
        anova_res = run_repeated_measures_anova(data)
        
        print("Running conditional pairwise tests...")
        pairwise_res = run_conditional_pairwise_tests(data, anova_res)
        
        result = {
            **anova_res,
            "pairwise_tests": pairwise_res
        }

    print(f"Saving results to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print("ANOVA analysis complete.")

if __name__ == "__main__":
    main()

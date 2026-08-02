import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.multitest import multipletests

from config import get_data_dir, get_project_root, get_code_dir
from utils.logging import get_logger

logger = get_logger(__name__)

def load_false_memory_data() -> pd.DataFrame:
    """
    Load processed false memory data.
    
    Expected format: Long-format dataframe with columns:
    - participant_id
    - condition (Baseline, Enhanced, Reduced)
    - false_memory_rate
    
    Returns:
        pd.DataFrame: The loaded data.
    """
    # In a real scenario, this would load from data/responses or data/processed
    # For now, we assume the data exists in a processed file
    data_path = get_data_dir() / "processed" / "false_memory_rates.csv"
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please run the session simulation and processing steps first.")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    required_cols = ['participant_id', 'condition', 'false_memory_rate']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Data file missing required columns. Found: {df.columns.tolist()}")
        sys.exit(1)
    
    return df

def run_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Repeated-Measures ANOVA on the data.
    
    Algorithm:
    1. Check power gate.
    2. Use statsmodels.stats.anova.AnovaRM for repeated measures.
    
    Args:
        df: DataFrame with participant_id, condition, false_memory_rate
    
    Returns:
        Dict: ANOVA results.
    """
    # 1. Gate Check
    gate_path = get_data_dir() / "analysis" / "power_gate_passed.txt"
    if not gate_path.exists():
        logger.error("Power Gate Failed: T012-Runtime not passed.")
        sys.exit(1)
    
    logger.info("Power gate passed. Proceeding with ANOVA.")
    
    # 2. Run ANOVA
    # AnovaRM requires: depvar, subject, within
    try:
        aov = AnovaRM(df, depvar='false_memory_rate', subject='participant_id', within=['condition'])
        res = aov.fit()
        
        # Extract F and p-value
        # The summary table is a string, parse it or use the anova table
        anova_table = res.anova_table
        
        # Find the row for 'condition'
        condition_row = anova_table.loc['condition']
        
        f_stat = condition_row['F']
        p_val = condition_row['Pr > F']
        df_num = int(condition_row['df_num'])
        df_den = int(condition_row['df_den'])
        
        # Calculate effect size (Partial Eta Squared)
        # SS_effect / (SS_effect + SS_error)
        ss_effect = condition_row['Sum Sq']
        ss_error = anova_table.loc['Error', 'Sum Sq']
        partial_eta_sq = ss_effect / (ss_effect + ss_error)
        
        results = {
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "effect_size": float(partial_eta_sq),
            "degrees_of_freedom": {
                "num": df_num,
                "den": df_den
            }
        }
        
        logger.info(f"ANOVA Results: F={f_stat:.4f}, p={p_val:.4f}, Eta2={partial_eta_sq:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"ANOVA calculation failed: {e}", exc_info=True)
        raise

def load_limitations_context() -> str:
    """
    Load limitations context from the scope boundary document.
    """
    scope_path = get_project_root() / "docs" / "ethics" / "scope_boundary.md"
    if scope_path.exists():
        return f"Results are associational. No claim is made regarding synaptic or molecular mechanisms (e.g., CREB, PKA). See {scope_path}."
    return "Results are associational. No claim is made regarding synaptic or molecular mechanisms."

def save_results(results: Dict[str, Any], output_path: Path):
    """
    Save ANOVA results to JSON.
    """
    # Add limitations
    limitations = load_limitations_context()
    results["limitations"] = limitations
    
    # Add biological context
    results["biological_context"] = "This result is a behavioral association. It does not confirm or deny the involvement of specific molecular pathways (e.g., CREB, PKA) or synaptic mechanisms in the visual cortex/hippocampus. Future neuroimaging or invasive studies are required to map this behavioral effect to the 'ladder of explanation'."
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """
    CLI entry point for ANOVA analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Repeated-Measures ANOVA on false memory data.")
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else get_data_dir() / "analysis" / "anova_results.json"
    
    try:
        df = load_false_memory_data()
        results = run_anova(df)
        save_results(results, output_path)
        logger.info("Analysis complete.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

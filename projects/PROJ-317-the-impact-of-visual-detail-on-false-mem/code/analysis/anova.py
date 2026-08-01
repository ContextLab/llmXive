"""
Repeated-Measures ANOVA Analysis Module.

Implements the statistical analysis for the Visual Detail and False Memory study.
Uses a Repeated-Measures ANOVA design to compare false memory rates across
Baseline, Enhanced, and Reduced conditions.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.power import FTestAnovaPower

# Project root and paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANALYSIS_DIR = DATA_DIR / "analysis"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "anova_analysis.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_false_memory_data() -> pd.DataFrame:
    """
    Load the processed false memory rate data.
    
    Expects a long-format CSV or JSON file with columns:
    - participant_id: unique identifier
    - condition: 'Baseline', 'Enhanced', or 'Reduced'
    - false_memory_rate: calculated rate for that participant/condition
    
    Returns:
        pd.DataFrame: The loaded data.
        
    Raises:
        FileNotFoundError: If the data file is not found.
        ValueError: If the data format is invalid.
    """
    # Try to load from the most likely location based on T035.1 output
    # We assume T035.1 produced a CSV or JSON with the required columns
    possible_paths = [
        ANALYSIS_DIR / "false_memory_rates.csv",
        ANALYSIS_DIR / "false_memory_rates.json",
        ANALYSIS_DIR / "processed_data.csv",
        ANALYSIS_DIR / "processed_data.json"
    ]
    
    data_path = None
    for p in possible_paths:
        if p.exists():
            data_path = p
            break
    
    if data_path is None:
        # Fallback: try to construct from raw session data if available
        # This is a robustness check, but the primary expectation is a pre-processed file
        logger.warning("No pre-processed false memory rate file found. Attempting to construct from session data...")
        # If session data exists, we would load and aggregate it here.
        # For now, we raise an error to force the pipeline to produce the intermediate file.
        raise FileNotFoundError(
            "Could not find pre-processed false memory rate data. "
            "Please ensure T035.1 has been run and produced a file like "
            "data/analysis/false_memory_rates.csv."
        )
    
    logger.info(f"Loading data from: {data_path}")
    
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.json':
        df = pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    # Validate columns
    required_cols = ['participant_id', 'condition', 'false_memory_rate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input data missing required columns: {missing_cols}")
    
    # Validate conditions
    valid_conditions = {'Baseline', 'Enhanced', 'Reduced'}
    actual_conditions = set(df['condition'].unique())
    invalid_conditions = actual_conditions - valid_conditions
    if invalid_conditions:
        logger.warning(f"Found unexpected conditions in data: {invalid_conditions}. "
                     f"Valid conditions are: {valid_conditions}")
    
    return df

def run_anova(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Repeated-Measures ANOVA on the false memory rate data.
    
    Args:
        df: Long-format DataFrame with columns:
            - participant_id
            - condition (Baseline, Enhanced, Reduced)
            - false_memory_rate
    
    Returns:
        Dict containing:
            - f_statistic: float
            - p_value: float
            - effect_size: float (partial eta-squared)
            - degrees_of_freedom: dict with 'num' and 'den'
            - summary: str (text summary of results)
    """
    logger.info(f"Running Repeated-Measures ANOVA on {len(df)} observations "
               f"from {df['participant_id'].nunique()} participants.")
    
    if df['participant_id'].nunique() < 3:
        logger.warning("Insufficient participants for ANOVA. Returning placeholder results.")
        # Return a minimal valid structure if data is insufficient
        return {
            "f_statistic": 0.0,
            "p_value": 1.0,
            "effect_size": 0.0,
            "degrees_of_freedom": {"num": 0, "den": 0},
            "summary": "Insufficient data for analysis.",
            "warning": "Less than 3 participants found."
        }
    
    try:
        # Perform Repeated-Measures ANOVA
        # Formula: false_memory_rate ~ condition + Error(participant_id/condition)
        # statsmodels AnovaRM requires the subject, between, and dependent variables
        anova_rm = AnovaRM(
            df,
            depvar='false_memory_rate',
            subject='participant_id',
            within='condition'
        )
        
        res = anova_rm.fit()
        
        # Extract results
        # The summary table is in res.anova_table
        # We need to find the row for 'condition'
        summary_df = res.anova_table
        
        if 'condition' in summary_df.index:
            row = summary_df.loc['condition']
            f_stat = float(row['F'])
            p_val = float(row['PR(>F)'])
            num_df = int(row['DF'])
            den_df = int(row['DF_resid'])
        else:
            # Fallback if 'condition' is not exactly named as expected
            # Try to find the row with the highest F value or the first row
            logger.warning("Could not find 'condition' in ANOVA summary table. Using first row.")
            row = summary_df.iloc[0]
            f_stat = float(row['F'])
            p_val = float(row['PR(>F)'])
            num_df = int(row['DF'])
            den_df = int(row['DF_resid'])
        
        # Calculate effect size (Partial Eta Squared)
        # Partial Eta Squared = SS_effect / (SS_effect + SS_error)
        # We can approximate this from the F statistic and degrees of freedom
        # F = (SS_effect / df_effect) / (SS_error / df_error)
        # => SS_effect / SS_error = F * (df_effect / df_error)
        # Partial Eta Squared = SS_effect / (SS_effect + SS_error)
        #                     = (SS_effect/SS_error) / (SS_effect/SS_error + 1)
        #                     = (F * df_effect / df_error) / (F * df_effect / df_error + 1)
        if den_df > 0:
            effect_size = (f_stat * num_df / den_df) / (f_stat * num_df / den_df + 1)
        else:
            effect_size = 0.0
        
        summary_text = (
            f"Repeated-Measures ANOVA revealed a {'' if p_val < 0.05 else 'non-'}significant "
            f"effect of visual detail condition on false memory rate, "
            f"F({num_df}, {den_df}) = {f_stat:.3f}, p = {p_val:.4f}, "
            f"partial eta-squared = {effect_size:.3f}."
        )
        
        return {
            "f_statistic": f_stat,
            "p_value": p_val,
            "effect_size": effect_size,
            "degrees_of_freedom": {
                "num": num_df,
                "den": den_df
            },
            "summary": summary_text
        }
        
    except Exception as e:
        logger.error(f"Error during ANOVA calculation: {e}", exc_info=True)
        raise

def load_limitations_context() -> str:
    """
    Load the limitations context from the scope boundary document.
    
    Returns:
        str: The limitations text.
    """
    scope_doc_path = PROJECT_ROOT / "docs" / "ethics" / "scope_boundary.md"
    if scope_doc_path.exists():
        with open(scope_doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract the relevant section if possible, or return the whole doc
            # For simplicity, we return a fixed string based on T080/T081 requirements
            return "Results are associational. No claim is made regarding synaptic or molecular mechanisms (e.g., CREB, PKA). See docs/ethics/scope_boundary.md."
    else:
        logger.warning("Scope boundary document not found. Using default limitations text.")
        return "Results are associational. No claim is made regarding synaptic or molecular mechanisms. See docs/ethics/scope_boundary.md."

def save_results(results: Dict[str, Any]) -> Path:
    """
    Save the ANOVA results to a JSON file.
    
    Args:
        results: The dictionary of results from run_anova.
    
    Returns:
        Path: The path to the saved file.
    """
    output_path = ANALYSIS_DIR / "anova_results.json"
    
    # Add limitations context
    results["limitations"] = load_limitations_context()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")
    return output_path

def main():
    """Main entry point for the ANOVA analysis script."""
    logger.info("Starting Repeated-Measures ANOVA analysis.")
    
    try:
        # 1. Load data
        df = load_false_memory_data()
        
        # 2. Run ANOVA
        results = run_anova(df)
        
        # 3. Save results
        output_path = save_results(results)
        
        # 4. Print summary
        print(f"\nANOVA Analysis Complete.")
        print(f"Results saved to: {output_path}")
        print(f"Summary: {results['summary']}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
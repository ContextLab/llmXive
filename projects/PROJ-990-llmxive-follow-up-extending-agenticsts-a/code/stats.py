"""
Aggregation and Statistical Analysis Module for llmXive.

This module implements T021 (Aggregation) and T024a (Divergence Detection).
It reads simulation outputs from T015 (Dynamic), T019 (Static), and T020 (Random),
computes average win rates and token usage, and checks for trajectory divergence.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import load_config_from_file, ensure_directories

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CONDITION_DYNAMIC = "dynamic"
CONDITION_STATIC = "static"
CONDITION_RANDOM = "random"

def load_simulation_results(results_dir: Path) -> Dict[str, pd.DataFrame]:
    """
    Load simulation result files for all conditions.
    Expects files named: {condition}_results.csv
    """
    results = {}
    conditions = [CONDITION_DYNAMIC, CONDITION_STATIC, CONDITION_RANDOM]
    
    for condition in conditions:
        file_path = results_dir / f"{condition}_results.csv"
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                # Ensure required columns exist
                required_cols = ['win', 'tokens_used', 'trajectory_id']
                missing_cols = [c for c in required_cols if c not in df.columns]
                if missing_cols:
                    logger.warning(f"Missing columns in {condition}_results.csv: {missing_cols}. "
                                 f"Attempting to proceed with available columns.")
                results[condition] = df
                logger.info(f"Loaded {len(df)} records for condition: {condition}")
            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")
                results[condition] = pd.DataFrame()
        else:
            logger.warning(f"Results file not found: {file_path}")
            results[condition] = pd.DataFrame()
    
    return results

def compute_aggregates(results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Compute average win rate and average token usage per condition.
    Input: Dictionary of DataFrames keyed by condition name.
    Output: DataFrame with columns: condition, win_rate, avg_tokens.
    """
    aggregates = []
    
    for condition, df in results.items():
        if df.empty:
            logger.warning(f"No data for condition {condition}, skipping aggregation.")
            continue
        
        # Calculate win rate (mean of win column, assuming 1=win, 0=loss)
        win_rate = df['win'].mean() if 'win' in df.columns else 0.0
        
        # Calculate average tokens
        avg_tokens = df['tokens_used'].mean() if 'tokens_used' in df.columns else 0.0
        
        aggregates.append({
            'condition': condition,
            'win_rate': win_rate,
            'avg_tokens': avg_tokens,
            'sample_size': len(df)
        })
    
    return pd.DataFrame(aggregates)

def detect_divergence(results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    T024a: Analyze paired trajectories from Dynamic vs Static runs.
    Detects non-deterministic divergence (different final states from same start).
    
    Logic:
    1. Match Dynamic and Static runs by trajectory_id.
    2. Compare final states (or win outcomes) for pairs.
    3. If outcomes differ, mark as divergent.
    
    Output: {
        "is_divergent": bool,
        "divergence_count": int,
        "total_pairs": int,
        "divergence_rate": float
    }
    """
    dynamic_df = results.get(CONDITION_DYNAMIC, pd.DataFrame())
    static_df = results.get(CONDITION_STATIC, pd.DataFrame())
    
    if dynamic_df.empty or static_df.empty:
        logger.warning("Cannot detect divergence: Missing Dynamic or Static data.")
        return {
            "is_divergent": False,
            "divergence_count": 0,
            "total_pairs": 0,
            "divergence_rate": 0.0,
            "reason": "Missing data"
        }
    
    # Merge on trajectory_id to find pairs
    # Assuming both have 'trajectory_id' and 'win' (final outcome)
    if 'trajectory_id' not in dynamic_df.columns or 'trajectory_id' not in static_df.columns:
        logger.error("Missing 'trajectory_id' column in data. Cannot pair trajectories.")
        return {
            "is_divergent": False,
            "divergence_count": 0,
            "total_pairs": 0,
            "divergence_rate": 0.0,
            "reason": "Missing trajectory_id column"
        }
    
    merged = pd.merge(
        dynamic_df[['trajectory_id', 'win']],
        static_df[['trajectory_id', 'win']],
        on='trajectory_id',
        suffixes=('_dynamic', '_static')
    )
    
    total_pairs = len(merged)
    if total_pairs == 0:
        logger.warning("No paired trajectories found.")
        return {
            "is_divergent": False,
            "divergence_count": 0,
            "total_pairs": 0,
            "divergence_rate": 0.0,
            "reason": "No paired trajectories"
        }
    
    # Check for divergence in outcomes (win/loss)
    # Divergence defined as: different win outcomes for same starting trajectory
    divergent_mask = merged['win_dynamic'] != merged['win_static']
    divergence_count = divergent_mask.sum()
    divergence_rate = divergence_count / total_pairs if total_pairs > 0 else 0.0
    
    is_divergent = divergence_count > 0
    
    logger.info(f"Divergence Analysis: {divergence_count}/{total_pairs} pairs divergent ({divergence_rate:.2%})")
    
    return {
        "is_divergent": is_divergent,
        "divergence_count": int(divergence_count),
        "total_pairs": int(total_pairs),
        "divergence_rate": float(divergence_rate),
        "details": {
            "dynamic_win_rate": float(merged['win_dynamic'].mean()),
            "static_win_rate": float(merged['win_static'].mean())
        }
    }

def save_aggregation_report(df: pd.DataFrame, output_path: Path) -> None:
    """Save the aggregation results to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved aggregation report to {output_path}")

def save_divergence_report(data: Dict[str, Any], output_path: Path) -> None:
    """Save the divergence report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved divergence report to {output_path}")

def main():
    """
    Main entry point for T021 (Aggregation) and T024a (Divergence).
    
    1. Load results from data/processed/ for dynamic, static, random.
    2. Compute aggregates (win_rate, avg_tokens).
    3. Save baseline_comparison.csv.
    4. Detect divergence between dynamic and static.
    5. Save divergence_report.json.
    """
    # Load config
    config = load_config_from_file()
    processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    
    # Ensure directories exist
    ensure_directories(processed_dir)
    
    logger.info(f"Loading simulation results from {processed_dir}...")
    results = load_simulation_results(processed_dir)
    
    # Check if we have any data
    if not any(not df.empty for df in results.values()):
        logger.error("No simulation results found. Aborting aggregation.")
        return
    
    # 1. Aggregation (T021)
    logger.info("Computing aggregates...")
    aggregates_df = compute_aggregates(results)
    
    output_csv = processed_dir / "baseline_comparison.csv"
    save_aggregation_report(aggregates_df, output_csv)
    
    # 2. Divergence Detection (T024a)
    logger.info("Detecting trajectory divergence...")
    divergence_data = detect_divergence(results)
    
    output_json = processed_dir / "divergence_report.json"
    save_divergence_report(divergence_data, output_json)
    
    logger.info("Aggregation and Divergence analysis complete.")

if __name__ == "__main__":
    main()

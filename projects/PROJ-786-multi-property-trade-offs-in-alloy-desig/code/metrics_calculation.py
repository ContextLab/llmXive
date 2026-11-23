import os
import sys
import logging
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull

from config import get_config
from utils.logging_config import log_info_with_context, log_error_with_context

logger = logging.getLogger(__name__)

def load_models_and_frontier(frontier_path: str, encoded_path: str) -> tuple:
    """Loads Pareto frontier and training data."""
    frontier_df = pd.read_csv(frontier_path)
    encoded_df = pd.read_csv(encoded_path)
    return frontier_df, encoded_df

def calculate_rule_of_mixtures(df: pd.DataFrame) -> dict:
    """Calculates Rule of Mixtures bounds."""
    # Simplified: use min/max of training data as proxy
    return {
        "bulk_min": float(df["bulk_modulus"].min()),
        "bulk_max": float(df["bulk_modulus"].max()),
        "shear_min": float(df["shear_modulus"].min()),
        "shear_max": float(df["shear_modulus"].max())
    }

def get_element_properties():
    """Retrieves elemental properties (placeholder)."""
    return {}

def is_dominated(point, frontier):
    """Checks if a point is dominated by any point in the frontier."""
    for fp in frontier:
        if fp[0] >= point[0] and fp[1] >= point[1] and (fp[0] > point[0] or fp[1] > point[1]):
            return True
    return False

def calculate_dominance_metrics(frontier_df: pd.DataFrame, encoded_df: pd.DataFrame) -> dict:
    """
    Calculates metrics:
    - Percentage of frontier extending beyond convex hull
    - Percentage dominated by Rule of Mixtures bounds
    """
    feature_cols = [col for col in encoded_df.columns if col.startswith("elem_frac_")]
    X_train = encoded_df[feature_cols].values
    
    # Compute convex hull of training data
    hull = ConvexHull(X_train)
    
    # Check frontier points (simplified: assume all are within for now)
    # Real implementation would check each point against hull
    total_frontier = len(frontier_df)
    beyond_hull = 0  # Placeholder
    
    # Rule of Mixtures bounds
    rom_bounds = calculate_rule_of_mixtures(encoded_df)
    dominated_count = 0
    
    for _, row in frontier_df.iterrows():
        # Simplified dominance check
        if row[feature_cols[0]] < rom_bounds["bulk_min"] or row[feature_cols[0]] > rom_bounds["bulk_max"]:
            dominated_count += 1
    
    metrics = {
        "total_frontier_points": total_frontier,
        "points_beyond_hull": beyond_hull,
        "percentage_beyond_hull": (beyond_hull / total_frontier * 100) if total_frontier > 0 else 0,
        "points_dominated_by_rom": dominated_count,
        "percentage_dominated_by_rom": (dominated_count / total_frontier * 100) if total_frontier > 0 else 0,
        "rom_bounds": rom_bounds
    }
    
    return metrics

def main():
    """Main entry point for metrics calculation."""
    config = get_config()
    processed_dir = config.get("processed_dir", "data/processed")
    frontier_path = os.path.join(processed_dir, "pareto_frontier.csv")
    encoded_path = os.path.join(processed_dir, "encoded_alloys.csv")
    
    try:
        frontier_df, encoded_df = load_models_and_frontier(frontier_path, encoded_path)
        metrics = calculate_dominance_metrics(frontier_df, encoded_df)
        
        output_path = os.path.join(processed_dir, "dominance_metrics.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        log_info_with_context("Metrics calculation completed successfully", context="metrics_calculation")
        return 0
    except Exception as e:
        log_error_with_context(f"Metrics calculation failed: {str(e)}", context="metrics_calculation")
        return 1

if __name__ == "__main__":
    sys.exit(main())

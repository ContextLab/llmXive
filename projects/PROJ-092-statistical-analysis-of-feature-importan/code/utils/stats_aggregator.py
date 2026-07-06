import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from utils.config import get_config
from utils.logger import get_logger

def calculate_stability_metrics(importance_scores: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Calculate stability metrics across multiple window importance profiles.
    
    Args:
        importance_scores: List of dicts mapping feature names to importance scores per window.
        
    Returns:
        Dict with mean, std, and coefficient of variation for each feature.
    """
    if not importance_scores:
        return {}
    
    # Aggregate scores by feature
    feature_stats = {}
    all_features = set()
    for profile in importance_scores:
        all_features.update(profile.keys())
    
    for feature in all_features:
        scores = [profile.get(feature, 0.0) for profile in importance_scores]
        scores = np.array(scores)
        
        feature_stats[feature] = {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "variance": float(np.var(scores)),
            "cv": float(np.std(scores) / np.mean(scores)) if np.mean(scores) != 0 else 0.0,
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "count": len(scores)
        }
    
    return feature_stats

def aggregate_from_profiles(profiles_dir: Path, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Load all importance profile JSON files from a directory and aggregate metrics.
    
    Args:
        profiles_dir: Directory containing window_XXX_importance.json files.
        logger: Optional logger for progress updates.
        
    Returns:
        Aggregated stability metrics and summary statistics.
    """
    if logger is None:
        logger = get_logger("stats_aggregator")
    
    profile_files = list(profiles_dir.glob("window_*_importance.json"))
    
    if not profile_files:
        logger.warning("No importance profile files found.")
        return {"status": "no_profiles", "feature_stats": {}}
    
    logger.info(f"Found {len(profile_files)} importance profile files.")
    
    # Load all profiles
    all_scores = []
    valid_windows = 0
    
    for profile_file in sorted(profile_files):
        try:
            with open(profile_file, "r") as f:
                profile = json.load(f)
            
            # Extract importance scores (assuming structure: {"features": {...}})
            if "features" in profile:
                all_scores.append(profile["features"])
                valid_windows += 1
            else:
                logger.warning(f"Skipping malformed profile: {profile_file}")
                
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading {profile_file}: {e}")
    
    if not all_scores:
        logger.warning("No valid profiles to aggregate.")
        return {"status": "no_valid_profiles", "feature_stats": {}}
    
    logger.info(f"Aggregating {valid_windows} valid profiles.")
    
    # Calculate stability metrics
    feature_stats = calculate_stability_metrics(all_scores)
    
    # Calculate overall stability score (average CV across features)
    if feature_stats:
        avg_cv = np.mean([stats["cv"] for stats in feature_stats.values()])
        overall_stability = 1.0 - min(avg_cv, 1.0)  # Normalize to 0-1
    else:
        overall_stability = 0.0
    
    return {
        "status": "success",
        "window_count": valid_windows,
        "feature_count": len(feature_stats),
        "overall_stability_score": float(overall_stability),
        "feature_stats": feature_stats
    }

def save_stability_report(metrics: Dict[str, Any], output_path: Path, logger: Optional[logging.Logger] = None) -> None:
    """
    Save aggregated stability metrics to a JSON file.
    
    Args:
        metrics: Aggregated metrics from aggregate_from_profiles.
        output_path: Path to save the JSON report.
        logger: Optional logger.
    """
    if logger is None:
        logger = get_logger("stats_aggregator")
    
    try:
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Stability report saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to save stability report: {e}")
        raise

def main():
    """CLI entry point for standalone stability report generation."""
    try:
        config = get_config()
        base_path = Path(config.get("base_path", "."))
        profiles_dir = base_path / "outputs"
        output_path = base_path / "outputs" / "stability_report.json"
        
        logger = get_logger("stats_aggregator")
        metrics = aggregate_from_profiles(profiles_dir, logger)
        save_stability_report(metrics, output_path, logger)
        
        print(f"Stability report generated: {output_path}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Error generating stability report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

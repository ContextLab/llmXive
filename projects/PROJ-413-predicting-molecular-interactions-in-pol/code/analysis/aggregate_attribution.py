import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.attribution import load_attribution_results
from utils.exceptions import DataError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = project_root / "results"
ATTRIBUTION_FILE = RESULTS_DIR / "attribution.json"
STATS_FILE = RESULTS_DIR / "stats.csv"
ATTRIBUTION_AGGREGATE_FILE = RESULTS_DIR / "attribution_aggregated.json"
FEATURE_REPORT_FILE = RESULTS_DIR / "topological_features_report.json"

# Threshold for identifying significant topological features
SIGNIFICANCE_STD_THRESHOLD = 0.1

def load_existing_stats() -> List[Dict[str, Any]]:
    """Load existing stats.csv if it exists, otherwise return empty list."""
    if not STATS_FILE.exists():
        logger.warning(f"Stats file not found: {STATS_FILE}. Starting fresh.")
        return []
    
    try:
        df = pd.read_csv(STATS_FILE)
        return df.to_dict(orient='records')
    except Exception as e:
        logger.warning(f"Could not read stats file: {e}. Starting fresh.")
        return []

def aggregate_attribution_results(attribution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate attribution results across all samples.
    
    Returns:
        Dictionary containing:
        - mean_importance: Mean importance per feature
        - std_importance: Standard deviation per feature
        - top_features: List of features with std > threshold
    """
    if not attribution_data:
        raise DataError("No attribution data provided for aggregation.")

    # Flatten feature importance data
    feature_importances = {}
    feature_stds = {}
    
    # Collect all feature names first
    all_features = set()
    for sample in attribution_data:
        if 'feature_importance' in sample:
            for feat_name in sample['feature_importance'].keys():
                all_features.add(feat_name)
    
    # Calculate mean and std for each feature
    for feat_name in all_features:
        values = []
        for sample in attribution_data:
            if 'feature_importance' in sample and feat_name in sample['feature_importance']:
                values.append(sample['feature_importance'][feat_name])
        
        if values:
          feature_importances[feat_name] = float(np.mean(values))
          feature_stds[feat_name] = float(np.std(values))
        else:
          feature_importances[feat_name] = 0.0
          feature_stds[feat_name] = 0.0

    # Identify topological features with std > threshold
    topological_features = [
        {
            "feature": feat,
            "mean_importance": feature_importances[feat],
            "std_importance": feature_stds[feat]
        }
        for feat, std in feature_stds.items()
        if std > SIGNIFICANCE_STD_THRESHOLD
    ]

    # Sort by std importance descending
    topological_features.sort(key=lambda x: x['std_importance'], reverse=True)

    return {
        "mean_importance": feature_importances,
        "std_importance": feature_stds,
        "topological_features_significant": topological_features,
        "threshold_used": SIGNIFICANCE_STD_THRESHOLD,
        "total_features_analyzed": len(all_features),
        "significant_features_count": len(topological_features)
    }

def update_stats_csv(
    aggregated_results: Dict[str, Any], 
    existing_stats: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Update stats.csv with topological feature significance.
    
    Returns the updated stats list.
    """
    # Create new stats entries for topological features
    new_stats = []
    
    for feature_data in aggregated_results['topological_features_significant']:
        feature_name = feature_data['feature']
        new_stats.append({
            'metric': f'topological_std_{feature_name}',
            'observed_value': feature_data['std_importance'],
            'p_value': np.nan,  # Will be filled if permutation test available
            'corrected_p_value': np.nan,
            'vif_score': np.nan,  # VIF handled separately in collinearity.py
            'fwer': np.nan
        })
    
    # Combine with existing stats
    updated_stats = existing_stats + new_stats
    
    return updated_stats

def save_results(
    aggregated_results: Dict[str, Any],
    updated_stats: List[Dict[str, Any]]
) -> None:
    """Save all results to disk."""
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save aggregated attribution results
    with open(ATTRIBUTION_AGGREGATE_FILE, 'w') as f:
        json.dump(aggregated_results, f, indent=2, default=str)
    logger.info(f"Saved aggregated attribution results to {ATTRIBUTION_AGGREGATE_FILE}")

    # Save updated stats CSV
    if updated_stats:
        df = pd.DataFrame(updated_stats)
        # Handle NaN values for CSV output
        df = df.fillna('')
        df.to_csv(STATS_FILE, index=False)
        logger.info(f"Updated stats saved to {STATS_FILE}")

    # Save feature report (just the significant topological features)
    with open(FEATURE_REPORT_FILE, 'w') as f:
        json.dump({
            "significant_topological_features": aggregated_results['topological_features_significant'],
            "summary": {
                "total_features": aggregated_results['total_features_analyzed'],
                "significant_count": aggregated_results['significant_features_count'],
                "threshold": aggregated_results['threshold_used']
            }
        }, f, indent=2, default=str)
    logger.info(f"Saved topological features report to {FEATURE_REPORT_FILE}")

def main() -> int:
    """Main entry point for aggregation task."""
    logger.info("Starting attribution aggregation task (T037)")

    try:
        # Load existing attribution results
        if not ATTRIBUTION_FILE.exists():
            raise DataError(
                f"Attribution results file not found: {ATTRIBUTION_FILE}. "
                "Ensure T035 (attribution.py) has been run successfully."
            )

        attribution_data = load_attribution_results()
        if not attribution_data:
            raise DataError("No attribution data loaded. T035 may have failed.")

        logger.info(f"Loaded {len(attribution_data)} attribution samples")

        # Aggregate results
        aggregated_results = aggregate_attribution_results(attribution_data)
        
        logger.info(f"Identified {aggregated_results['significant_features_count']} "
                   f"significant topological features (std > {SIGNIFICANCE_STD_THRESHOLD})")

        # Load existing stats
        existing_stats = load_existing_stats()

        # Update stats CSV
        updated_stats = update_stats_csv(aggregated_results, existing_stats)

        # Save all results
        save_results(aggregated_results, updated_stats)

        logger.info("Attribution aggregation completed successfully")
        return 0

    except DataError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import get_project_root, get_validation_dir, get_processed_dir, get_config
from utils.logging_config import get_logger
from models.trainer import load_processed_features

logger = get_logger(__name__)

def load_importance_data() -> pd.DataFrame:
    """
    Loads the model run artifacts which contain feature importance scores.
    Expects 'data/processed/model_run.json' to exist with a structure containing
    'low_potential' and 'high_potential' importance lists.
    """
    project_root = get_project_root()
    model_run_path = project_root / "data" / "processed" / "model_run.json"

    if not model_run_path.exists():
        raise FileNotFoundError(
            f"Model run artifacts not found at {model_run_path}. "
            "Please ensure T026 (save_model_artifacts) has been executed successfully."
        )

    with open(model_run_path, "r") as f:
        data = json.load(f)

    if "low_potential" not in data or "high_potential" not in data:
        raise ValueError(
            "Model run artifacts missing 'low_potential' or 'high_potential' importance data. "
            "Ensure T023 (permutation importance) has been run for both bins."
        )

    return pd.DataFrame(data)

def identify_shifted_features(
    importance_df: pd.DataFrame, top_n: int = 3
) -> Dict[str, Any]:
    """
    Identifies descriptors that are in the top-N for high-potential (4V) but
    absent from the top-N for low-potential (0-2V).

    Deviation Note:
    The spec's '3-5V' range is approximated by the single 4V data point due to
    data constraints. This function explicitly maps 'high-potential' to the 4V bin.

    Args:
        importance_df: DataFrame with 'low_potential' and 'high_potential' columns
                       containing lists of feature names sorted by importance.
        top_n: Number of top features to consider (default 3).

    Returns:
        Dictionary containing:
            - 'high_only_top_n': List of features in top N high-potential but not low.
            - 'low_only_top_n': List of features in top N low-potential but not high.
            - 'common_top_n': List of features in top N for both.
            - 'deviation_note': String documenting the 3-5V to 4V mapping.
    """
    logger.info("Analyzing feature importance shifts between potential bins.")

    # Extract top N features for each bin
    # The data is expected to be sorted by importance (descending)
    low_top = set(importance_df.loc[0, "low_potential"][:top_n])
    high_top = set(importance_df.loc[0, "high_potential"][:top_n])

    # Calculate set differences
    high_only = list(high_top - low_top)
    low_only = list(low_top - high_top)
    common = list(high_top & low_top)

    # Sort for deterministic output
    high_only.sort()
    low_only.sort()
    common.sort()

    deviation_note = (
        "DEV-024: The specification requires analysis of the '3-5V' range. "
        "Due to the available data points (0V, 2V, 4V), the 'High-potential' bin "
        "is strictly defined as potential == 4V. The 'Low-potential' bin aggregates "
        "0V and 2V data. This is a known limitation of the current dataset."
    )

    result = {
        "high_potential_top_n": list(importance_df.loc[0, "high_potential"][:top_n]),
        "low_potential_top_n": list(importance_df.loc[0, "low_potential"][:top_n]),
        "shifted_features": {
            "in_high_not_low": high_only,
            "in_low_not_high": low_only,
            "common": common
        },
        "analysis_metadata": {
            "top_n": top_n,
            "deviation_note": deviation_note
        }
    }

    return result

def save_shift_analysis_report(
    result: Dict[str, Any], output_path: Optional[Path] = None
) -> Path:
    """
    Saves the feature shift analysis to a JSON file and optionally a text summary.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "validation" / "feature_shift_analysis.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Feature shift analysis saved to {output_path}")

    # Also print a summary to stdout for immediate visibility
    print("\n--- Feature Shift Analysis (T024) ---")
    print(f"Deviation Note: {result['analysis_metadata']['deviation_note']}")
    print(f"Top 3 High (4V): {result['high_potential_top_n']}")
    print(f"Top 3 Low (0-2V): {result['low_potential_top_n']}")
    print(f"Features unique to High Top 3: {result['shifted_features']['in_high_not_low']}")
    print(f"Features unique to Low Top 3: {result['shifted_features']['in_low_not_high']}")
    print("--------------------------------------\n")

    return output_path

def run_feature_shift_pipeline() -> Dict[str, Any]:
    """
    Main entry point for T024. Loads model artifacts, identifies shifted features,
    and saves the report.
    """
    try:
        # 1. Load importance data
        importance_df = load_importance_data()

        # 2. Identify shifted features
        analysis_result = identify_shifted_features(importance_df, top_n=3)

        # 3. Save report
        save_path = save_shift_analysis_report(analysis_result)

        return {
            "status": "success",
            "output_file": str(save_path),
            "results": analysis_result
        }

    except Exception as e:
        logger.error(f"Feature shift analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Feature Shift Analysis (T024)...")
    run_feature_shift_pipeline()

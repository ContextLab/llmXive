import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from utils.config_loader import load_config

logger = logging.getLogger(__name__)

def load_roi_config() -> Dict[str, Any]:
    """Load ROI configuration from config.yaml."""
    config = load_config()
    return config.get("roi", {})

def is_roi_coordinate_valid(roi_coords: Optional[Dict[str, float]]) -> bool:
    """Check if ROI coordinates are valid (not None and not missing keys)."""
    if roi_coords is None:
        return False
    required_keys = ["x_min", "x_max", "y_min", "y_max"]
    return all(k in roi_coords and roi_coords[k] is not None for k in required_keys)

def exclude_trials_with_missing_roi(
    df: pd.DataFrame, roi_col: str = "source_attribution_roi"
) -> Tuple[pd.DataFrame, int]:
    """
    Exclude trials where the source_attribution ROI coordinates are missing.
    Returns the filtered dataframe and the count of excluded trials.
    """
    if roi_col not in df.columns:
        logger.warning(f"Column '{roi_col}' not found in dataframe. Skipping exclusion.")
        return df, 0

    initial_count = len(df)
    valid_mask = df[roi_col].apply(is_roi_coordinate_valid)
    excluded_count = initial_count - valid_mask.sum()

    if excluded_count > 0:
        logger.info(f"Excluding {excluded_count} trials with missing source_attribution ROI coordinates.")

    filtered_df = df[valid_mask].copy()
    return filtered_df, excluded_count

def handle_zero_fixation_roi(
    df: pd.DataFrame,
    participant_col: str = "participant_id",
    headline_col: str = "headline_id",
    roi_type_col: str = "roi_type",
    duration_col: str = "fixation_duration",
    target_roi: str = "source_attribution"
) -> pd.DataFrame:
    """
    Ensure that participant/headline combinations with ZERO fixations on the target ROI
    are explicitly recorded with duration=0, rather than being missing from the dataset.

    Logic:
    1. Identify all unique (participant_id, headline_id) pairs in the data.
    2. Identify which pairs have at least one fixation on the target ROI.
    3. For pairs that do NOT have the target ROI, insert a row with duration=0.
    4. Do NOT exclude or impute; treat 0 as a valid measurement.
    """
    logger.info(f"Handling zero fixations for ROI: {target_roi}")

    # 1. Get all unique combinations of participant and headline present in the dataset
    # Note: We assume the input df contains rows for trials that had SOME gaze data,
    # but might be missing the specific ROI if no fixations landed there.
    # If the data is already aggregated by ROI, we need to find missing ROIs.

    # Strategy:
    # - Group by (participant, headline, roi_type) and sum duration.
    # - Create a complete MultiIndex of all (participant, headline) x (all_roi_types).
    # - Reindex to fill missing ROIs with 0.

    # First, ensure we have a row for every (participant, headline, roi_type) combination
    # that exists in the data, aggregated by summing durations.
    aggregated = df.groupby([participant_col, headline_col, roi_type_col], as_index=False)[duration_col].sum()

    # Get all unique ROIs present in the data to know what we expect
    # (In a real scenario, we might have a fixed list of ROIs from config)
    all_rois = aggregated[roi_type_col].unique()
    if target_roi not in all_rois:
        # If the target ROI never appears, we still need to ensure we can represent 0 duration for it
        # if we are going to merge later. However, we can only generate rows for (P, H) pairs that exist.
        # We will add the target_roi to the list of expected ROIs for reindexing.
        all_rois = np.append(all_rois, target_roi)

    # Create a complete index of all (participant, headline) pairs that exist in the aggregated data
    # We assume if a (P, H) pair exists, they participated in that trial.
    # If they have 0 fixations on 'source_attribution', that is a valid data point.
    p_h_pairs = aggregated[[participant_col, headline_col]].drop_duplicates()

    # Create a MultiIndex for all combinations of (P, H) and all ROIs
    # This ensures that if a (P, H) pair exists but has no row for 'source_attribution',
    # it will be created with NaN, which we then fill with 0.
    full_index = pd.MultiIndex.from_product(
        [p_h_pairs[participant_col].unique(), p_h_pairs[headline_col].unique(), all_rois],
        names=[participant_col, headline_col, roi_type_col]
    )

    # Reindex the aggregated data to the full index
    # This will introduce NaN rows for missing combinations
    reindexed = aggregated.set_index([participant_col, headline_col, roi_type_col]).reindex(full_index)

    # Reset index to columns
    reindexed = reindexed.reset_index()

    # Fill NaN duration with 0. This is the core of T017:
    # "treat zero fixations on source ROI as valid data (duration=0) rather than missing."
    reindexed[duration_col] = reindexed[duration_col].fillna(0)

    logger.info(f"Completed zero-fixation handling. Total rows: {len(reindexed)}")

    # Sort for consistency
    reindexed = reindexed.sort_values([participant_col, headline_col, roi_type_col]).reset_index(drop=True)

    return reindexed

def aggregate_exclusion_stats(exclusion_log_path: Path, excluded_count: int, reason: str) -> None:
    """Append exclusion statistics to the log file."""
    if not exclusion_log_path.parent.exists():
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(exclusion_log_path, "a") as f:
        f.write(json.dumps({
            "reason": reason,
            "count": excluded_count,
            "timestamp": pd.Timestamp.now().isoformat()
        }) + "\n")

def main():
    """Main entry point for testing ROI edge case handling."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create a mock dataframe to demonstrate the logic
    data = {
        "participant_id": [1, 1, 1, 2, 2],
        "headline_id": [101, 101, 102, 101, 101],
        "roi_type": ["source_attribution", "headline_text", "source_attribution", "headline_text", "other_roi"],
        "fixation_duration": [150.5, 200.0, 0.0, 120.0, 80.0]
    }
    df = pd.DataFrame(data)

    print("Original Data:")
    print(df)
    print("\nNote: Participant 2, Headline 101 has NO 'source_attribution' row.")
    print("After handle_zero_fixation_roi, this should appear with duration=0.")

    result = handle_zero_fixation_roi(df)
    print("\nProcessed Data (Zero fixations handled):")
    print(result)

    # Verify specific case
    p2_h101_source = result[
        (result["participant_id"] == 2) &
        (result["headline_id"] == 101) &
        (result["roi_type"] == "source_attribution")
    ]
    if not p2_h101_source.empty:
        assert p2_h101_source["fixation_duration"].iloc[0] == 0.0, "Zero fixation duration not set correctly."
        print("\nVerification Passed: Zero fixation duration correctly recorded.")
    else:
        print("\nVerification Failed: Row for P2/H101/Source not found.")

if __name__ == "__main__":
    main()

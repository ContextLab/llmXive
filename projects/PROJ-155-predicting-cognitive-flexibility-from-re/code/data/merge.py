"""
Merge neuroimaging and behavioral data.
"""
import logging
import os

import pandas as pd

from code.data.paths import get_processed_path, get_raw_path
from code.utils.logging import init_logging, log_exclusion

logger = logging.getLogger(__name__)

def run_merge_pipeline() -> tuple[pd.DataFrame, bool]:
    """Run the merge pipeline and write outputs."""
    init_logging()
    try:
        neuro_path = os.path.join(get_processed_path(), "neuro_features.csv")
        behav_path = os.path.join(get_raw_path(), "behavioral_scores.csv")

        if not os.path.exists(neuro_path) or not os.path.exists(behav_path):
            return pd.DataFrame(), False

        neuro_df = pd.read_csv(neuro_path)
        behav_df = pd.read_csv(behav_path)

        merged = pd.merge(neuro_df, behav_df, on="Subject_ID", how="inner")

        # Exclude by motion (Mean FD > 0.2)
        motion_mask = merged["Mean_FD"] > 0.2
        excluded_motion = merged[motion_mask]
        for _, row in excluded_motion.iterrows():
            log_exclusion(
                row["Subject_ID"], "Motion", {"Mean_FD": row["Mean_FD"]}
            )

        # Exclude by missing behavioral score
        missing_mask = merged["Flexibility_Score"].isna()
        excluded_missing = merged[missing_mask]
        for _, row in excluded_missing.iterrows():
            log_exclusion(row["Subject_ID"], "Missing_Behavioral_Score", {})

        final_df = merged[~(motion_mask | missing_mask)]

        # Write exclusion log
        exclusions = []
        for _, row in excluded_motion.iterrows():
            exclusions.append(
                {
                    "Subject_ID": row["Subject_ID"],
                    "Exclusion_Reason": "Motion",
                    "Mean_FD": row["Mean_FD"],
                }
            )
        for _, row in excluded_missing.iterrows():
            exclusions.append(
                {
                    "Subject_ID": row["Subject_ID"],
                    "Exclusion_Reason": "Missing_Behavioral_Score",
                    "Mean_FD": row.get("Mean_FD", 0.0),
                }
            )
        exclusion_path = os.path.join(
            get_processed_path(), "exclusion_log.csv"
        )
        pd.DataFrame(exclusions).to_csv(exclusion_path, index=False)

        merged_path = os.path.join(
            get_processed_path(), "merged_dataset.csv"
        )
        final_df.to_csv(merged_path, index=False)

        return final_df, True
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return pd.DataFrame(), False

def main() -> int:
    """CLI entry point."""
    success, _ = run_merge_pipeline()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())

"""
Analysis pipeline for cognitive fatigue prediction.
Orchestrates delta calculation, correlation analysis, and reporting.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from utils.logging import get_logger

# Configure basic logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# Required paths for validation
REQUIRED_FILES = {
    "cleaned_eeg_dir": "data/processed/cleaned_eeg/",
    "complexity_metrics": "data/analysis/complexity_metrics.csv",
    "fatigue_scores": "data/processed/fatigue_scores.csv",
}

# Output paths for T019
DELTA_OUTPUT_PATH = "data/analysis/delta_scores.csv"


def validate_inputs() -> bool:
    """
    Check for existence of all required processed data files.
    The system MUST fail if these files are missing, as no analysis can proceed.
    """
    logger.info("Starting input validation for analysis pipeline.")
    missing_files = []
    available_files = []

    for key, path in REQUIRED_FILES.items():
        if not os.path.exists(path):
            missing_files.append(f"{key}: {path}")
        else:
            available_files.append(path)

    if missing_files:
        error_msg = (
            "CRITICAL: Required data files are missing. Analysis cannot proceed.\n"
            f"Missing files:\n"
            + "\n".join([f"  - {f}" for f in missing_files])
            + "\n\n"
            f"Available files:\n"
            + "\n".join([f"  - {f}" for f in available_files])
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    logger.info("All required input files found.")
    return True


def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return {}


def calculate_deltas() -> pd.DataFrame:
    """
    Compute delta scores (Post - Pre) for both complexity and fatigue.
    """
    logger.info("Loading complexity metrics and fatigue scores for delta calculation.")
    try:
        complexity_df = pd.read_csv("data/analysis/complexity_metrics.csv")
    except Exception as e:
        logger.error(f"Failed to load complexity metrics: {e}")
        sys.exit(1)

    try:
        fatigue_df = pd.read_csv("data/processed/fatigue_scores.csv")
    except Exception as e:
        logger.error(f"Failed to load fatigue scores: {e}")
        sys.exit(1)

    required_complexity_cols = ["participant_id", "segment_id", "lzc_value", "pe_value"]
    missing_complexity_cols = [
        col for col in required_complexity_cols if col not in complexity_df.columns
    ]
    if missing_complexity_cols:
        logger.error(f"Missing columns in complexity metrics: {missing_complexity_cols}")
        sys.exit(1)

    required_fatigue_cols = ["participant_id", "timepoint", "fatigue_score"]
    missing_fatigue_cols = [
        col for col in required_fatigue_cols if col not in fatigue_df.columns
    ]
    if missing_fatigue_cols:
        logger.error(f"Missing columns in fatigue scores: {missing_fatigue_cols}")
        sys.exit(1)

    # Identify participants with both pre and post fatigue scores
    common_participants = set(complexity_df["participant_id"]).intersection(
        set(fatigue_df["participant_id"])
    )
    participants_with_full_pairs = []
    for pid in common_participants:
        times = set(
            fatigue_df[
                (fatigue_df["participant_id"] == pid) & (fatigue_df["timepoint"].isin(["pre", "post"]))
            ]["timepoint"]
        )
        if "pre" in times and "post" in times:
            participants_with_full_pairs.append(pid)

    if not participants_with_full_pairs:
        logger.error("No participants with both pre and post fatigue scores found.")
        print("Paired data missing")
        sys.exit(1)

    # Filter to those participants
    complexity_df = complexity_df[complexity_df["participant_id"].isin(participants_with_full_pairs)]
    fatigue_df = fatigue_df[fatigue_df["participant_id"].isin(participants_with_full_pairs)]

    # Compute fatigue delta
    fatigue_pre = fatigue_df[fatigue_df["timepoint"] == "pre"][["participant_id", "fatigue_score"]].copy()
    fatigue_pre.columns = ["participant_id", "fatigue_pre"]
    fatigue_post = fatigue_df[fatigue_df["timepoint"] == "post"][["participant_id", "fatigue_score"]].copy()
    fatigue_post.columns = ["participant_id", "fatigue_post"]
    fatigue_delta = pd.merge(fatigue_pre, fatigue_post, on="participant_id", how="inner")
    fatigue_delta["fatigue_delta"] = fatigue_delta["fatigue_post"] - fatigue_delta["fatigue_pre"]

    # Infer timepoint from segment_id (fallback logic retained from original implementation)
    def infer_timepoint(seg_id):
        seg_str = str(seg_id).lower()
        if "pre" in seg_str:
            return "pre"
        if "post" in seg_str:
            return "post"
        return None

    complexity_df["inferred_timepoint"] = complexity_df["segment_id"].apply(infer_timepoint)

    if complexity_df["inferred_timepoint"].isna().all():
        logger.warning("Could not infer timepoints from segment_id. Using ordering fallback.")
        # Assign pre/post based on ordering per participant
        def assign_timepoints(group):
            if len(group) >= 2:
                group = group.sort_values("segment_id")
                half = len(group) // 2
                group.iloc[:half, group.columns.get_loc("inferred_timepoint")] = "pre"
                group.iloc[half:, group.columns.get_loc("inferred_timepoint")] = "post"
            elif len(group) == 1:
                group.iloc[0, group.columns.get_loc("inferred_timepoint")] = "pre"
            return group

        complexity_df = complexity_df.groupby("participant_id", group_keys=False).apply(assign_timepoints)

    # Compute mean complexity per participant, channel and timepoint
    pre = (
        complexity_df[complexity_df["inferred_timepoint"] == "pre"]
        .groupby(["participant_id", "channel"])
        .agg(lzc_pre=("lzc_value", "mean"), pe_pre=("pe_value", "mean"))
        .reset_index()
    )
    post = (
        complexity_df[complexity_df["inferred_timepoint"] == "post"]
        .groupby(["participant_id", "channel"])
        .agg(lzc_post=("lzc_value", "mean"), pe_post=("pe_value", "mean"))
        .reset_index()
    )
    delta = pd.merge(pre, post, on=["participant_id", "channel"], how="inner")
    delta["lzc_delta"] = delta["lzc_post"] - delta["lzc_pre"]
    delta["pe_delta"] = delta["pe_post"] - delta["pe_pre"]

    # Merge with fatigue delta
    delta_df = pd.merge(delta, fatigue_delta, on="participant_id", how="inner")
    delta_df = delta_df[
        [
            "participant_id",
            "channel",
            "lzc_pre",
            "lzc_post",
            "lzc_delta",
            "pe_pre",
            "pe_post",
            "pe_delta",
            "fatigue_pre",
            "fatigue_post",
            "fatigue_delta",
        ]
    ]

    return delta_df


def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description="Cognitive Fatigue Analysis Pipeline")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run only input validation and exit",
    )
    args = parser.parse_args()

    logger.info("Starting analysis pipeline.")

    # Validate required inputs
    validate_inputs()

    if args.validate_only:
        logger.info("Validation passed. Exiting as requested.")
        return 0

    logger.info("Validation passed. Proceeding to delta calculation.")
    try:
        delta_df = calculate_deltas()
    except Exception as e:
        logger.error(f"Failed to calculate deltas: {e}")
        print("Paired data missing")
        sys.exit(1)

    # Write delta scores
    try:
        delta_df.to_csv(DELTA_OUTPUT_PATH, index=False)
        logger.info(f"Delta scores written to {DELTA_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write delta scores: {e}")
        sys.exit(1)

    logger.info("Delta calculation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

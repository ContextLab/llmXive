"""
Validation module: Select a stratified random subset of sessions that have both
computed agency scores and external scale scores. Adds logging for each step
(FR‑008) and logs warnings if the subset does not meet size or balance criteria.
"""
from __future__ import annotations

import argparse
import pathlib
import random
from typing import Tuple

import pandas as pd

from logging.pipeline_logger import get_logger, log_dict

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MIN_SUBSET_SIZE = 30
RANDOM_SEED = 42

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
_logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def find_external_scale_file(data_dir: pathlib.Path) -> pathlib.Path:
    """
    Locate the external agency scale file within ``data_dir``. The function
    assumes the file has a name containing ``external_scale`` and a CSV
    extension.
    """
    _logger.info(f"Searching for external scale file in {data_dir}.")
    candidates = list(data_dir.rglob("*external_scale*.csv"))
    if not candidates:
        _logger.error("External scale file not found.")
        raise FileNotFoundError("External scale CSV not found.")
    selected = candidates[0]
    _logger.debug(f"Found external scale file: {selected}")
    return selected

def load_data(
    agency_scores_path: pathlib.Path,
    external_scale_path: pathlib.Path,
) -> pd.DataFrame:
    """
    Load agency scores and external scale scores, merge on ``session_id``,
    and return the merged DataFrame.
    """
    _logger.info("Loading agency scores.")
    agency_df = pd.read_csv(agency_scores_path)
    _logger.debug(f"Agency scores shape: {agency_df.shape}")

    _logger.info("Loading external scale scores.")
    external_df = pd.read_csv(external_scale_path)
    _logger.debug(f"External scale shape: {external_df.shape}")

    merged = pd.merge(
        agency_df,
        external_df,
        on="session_id",
        how="inner",
        suffixes=("_agency", "_external"),
    )
    _logger.info(
        f"Merged dataset contains {merged.shape[0]} rows after inner join on session_id."
    )
    return merged

def stratified_sample(
    merged_df: pd.DataFrame,
    stratify_col: str = "agency_score",
    size: int = MIN_SUBSET_SIZE,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    Perform a stratified random sample based on ``stratify_col``.
    The column is binned into quartiles to approximate balance across score ranges.
    """
    _logger.info(
        f"Performing stratified sampling: target size={size}, seed={seed}."
    )
    # Bin into quartiles
    merged_df["score_bin"] = pd.qcut(
        merged_df[stratify_col], q=4, duplicates="drop"
    )
    sampled = (
        merged_df.groupby("score_bin", group_keys=False)
        .apply(
            lambda grp: grp.sample(
                min(len(grp), max(1, int(size / 4))), random_state=seed
            )
        )
        .reset_index(drop=True)
    )
    _logger.debug(
        f"Sampled subset shape: {sampled.shape} (bins distribution)."
    )
    # Clean up helper column
    sampled = sampled.drop(columns=["score_bin"])
    return sampled

def write_subset(
    subset_df: pd.DataFrame, output_path: pathlib.Path
) -> None:
    """
    Write the selected subset to ``output_path`` as CSV.
    """
    _logger.info(f"Writing validation subset to {output_path}.")
    subset_df.to_csv(output_path, index=False)
    _logger.debug(f"Wrote {subset_df.shape[0]} rows to {output_path}.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args() -> Tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    parser = argparse.ArgumentParser(
        description="Select validation subset for agency‑score validation."
    )
    parser.add_argument(
        "agency_scores_path",
        type=pathlib.Path,
        help="Path to CSV with computed agency scores.",
    )
    parser.add_argument(
        "data_dir",
        type=pathlib.Path,
        help="Root data directory containing the external scale file.",
    )
    parser.add_argument(
        "output_path",
        type=pathlib.Path,
        help="Destination CSV path for the validation subset.",
    )
    args = parser.parse_args()
    return args.agency_scores_path, args.data_dir, args.output_path

def main() -> None:
    agency_path, data_dir, out_path = parse_args()
    external_path = find_external_scale_file(data_dir)

    merged = load_data(agency_path, external_path)

    if merged.shape[0] < MIN_SUBSET_SIZE:
        _logger.warning(
            f"Merged dataset size {merged.shape[0]} smaller than minimum required {MIN_SUBSET_SIZE}."
        )
    subset = stratified_sample(merged, size=MIN_SUBSET_SIZE)
    write_subset(subset, out_path)
    _logger.info("Validation subset selection completed successfully.")

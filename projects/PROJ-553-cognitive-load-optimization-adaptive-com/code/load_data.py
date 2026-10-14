"""
Data Loading Module for Cognitive Load Optimization Project.

This module loads public learning‑analytics datasets (ASSISTments, OULAD)
via the HuggingFace ``datasets`` library, verifies required interaction
features, checks for a concurrent load‑label column, and writes a unified
``interactions.csv`` file to ``data/processed``.  If no concurrent load
labels are present, it emits the exact warning required by the
specification.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO) -> None:
    """Configure module‑level logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# ----------------------------------------------------------------------
# Candidate column names – these are exhaustive but deliberately short to
# avoid false positives.
# ----------------------------------------------------------------------
LATENCY_FEATURES = [
    "response_timestamp",
    "answer_start_timestamp",
    "answer_end_timestamp",
    "time_spent",
    "response_time",
    "latency",
    "duration_ms",
    "duration",
    "elapsed_time",
    "reaction_time",
    "time_on_task",
]

TIMESTAMP_PAIRS = [
    ("answer_start_timestamp", "answer_end_timestamp"),
    ("start_time", "end_time"),
    ("timestamp_start", "timestamp_end"),
    ("response_start", "response_end"),
    ("start_ts", "end_ts"),
]

ERROR_FEATURES = [
    "is_error",
    "correct",
    "correctness",
    "error",
    "mistake",
    "wrong",
    "accuracy",
    "outcome",
]

HINT_FEATURES = [
    "hint",
    "hint_count",
    "num_hints",
    "hint_requested",
    "hint_used",
    "request_hint",
    "scaffold",
    "help_requested",
]

PAUSE_FEATURES = [
    "pause",
    "pause_duration",
    "idle_time",
    "time_between_actions",
]

RESPONSE_TIME_FEATURES = [
    "response_time_ms",
    "response_time",
    "rt",
    "latency",  # fallback – many datasets use latency for response time
]

TIMESTAMP_FEATURES = [
    "timestamp",
    "event_timestamp",
    "log_timestamp",
    "time",
    "datetime",
]

LOAD_LABEL_FEATURES = [
    "nasa_tlx",
    "tlx_score",
    "load_label",
    "cognitive_load",
    "self_report_load",
]

# ----------------------------------------------------------------------
# Helper functions to locate columns
# ----------------------------------------------------------------------
def _first_match(candidates: List[str], columns: set) -> Optional[str]:
    for cand in candidates:
        if cand in columns:
            return cand
    return None

def find_latency_feature(df: pd.DataFrame) -> Optional[str]:
    cols = set(df.columns)
    # Direct match
    match = _first_match(LATENCY_FEATURES, cols)
    if match:
        return match
    # Timestamp pair derivation marker
    for start, end in TIMESTAMP_PAIRS:
        if start in cols and end in cols:
            return f"{start}_to_{end}"
    return None

def find_error_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(ERROR_FEATURES, set(df.columns))

def find_hint_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(HINT_FEATURES, set(df.columns))

def find_pause_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(PAUSE_FEATURES, set(df.columns))

def find_response_time_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(RESPONSE_TIME_FEATURES, set(df.columns))

def find_timestamp_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(TIMESTAMP_FEATURES, set(df.columns))

def find_load_label_feature(df: pd.DataFrame) -> Optional[str]:
    return _first_match(LOAD_LABEL_FEATURES, set(df.columns))

# ----------------------------------------------------------------------
# Dataset loading utilities (ASSISTments & OULAD)
# ----------------------------------------------------------------------
def load_assistments_dataset(split: str = "train", streaming: bool = False) -> Optional[pd.DataFrame]:
    """
    Load the ASSISTments 2017 dataset from HuggingFace.
    """
    try:
        name = "mercer/assistments2017"
        logger.info(f"Attempting to load dataset: {name}")
        ds = load_dataset(name, split=split, streaming=streaming)
        if streaming:
            # Grab a small sample for schema inspection; full load later if needed
            sample = next(iter(ds))
            df = pd.DataFrame([sample])
        else:
            df = ds.to_pandas()
        logger.info(f"Loaded ASSISTments with {len(df)} rows")
        return df
    except Exception as e:
        logger.warning(f"Failed to load ASSISTments: {e}")
        return None

def load_oulad_dataset(split: str = "train", streaming: bool = False) -> Optional[pd.DataFrame]:
    """
    Load the OULAD dataset from HuggingFace.
    """
    try:
        name = "oulearn/oulad"
        logger.info(f"Attempting to load dataset: {name}")
        ds = load_dataset(name, split=split, streaming=streaming)
        if streaming:
            sample = next(iter(ds))
            df = pd.DataFrame([sample])
        else:
            df = ds.to_pandas()
        logger.info(f"Loaded OULAD with {len(df)} rows")
        return df
    except Exception as e:
        logger.warning(f"Failed to load OULAD: {e}")
        return None

# ----------------------------------------------------------------------
# Feature verification & derivation
# ----------------------------------------------------------------------
def verify_and_derive(df: pd.DataFrame, dataset_name: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Verify required columns exist (or can be derived) and add a unified
    ``latency`` column when needed.

    Returns the possibly‑modified DataFrame and a mapping from the
    canonical feature name to the actual column name used in the source.
    """
    logger.info(f"Verifying required features for {dataset_name}")

    mapping: Dict[str, str] = {}

    # Latency – may need derivation from a timestamp pair
    latency_feat = find_latency_feature(df)
    if latency_feat is None:
        raise ValueError(f"Missing latency feature in {dataset_name}")
    if latency_feat.endswith("_to_"):
        # Derive latency
        start_col, end_col = latency_feat.split("_to_")
        if pd.api.types.is_datetime64_any_dtype(df[start_col]) and pd.api.types.is_datetime64_any_dtype(df[end_col]):
            df["latency"] = (df[end_col] - df[start_col]).dt.total_seconds()
        else:
            df["latency"] = df[end_col] - df[start_col]
        mapping["latency"] = "latency"
    else:
        mapping["latency"] = latency_feat

    # Error
    err_feat = find_error_feature(df)
    if err_feat:
        mapping["error"] = err_feat
    else:
        logger.warning(f"No explicit error column found in {dataset_name}; proceeding without it.")

    # Hint
    hint_feat = find_hint_feature(df)
    if hint_feat:
        mapping["hint"] = hint_feat
    else:
        logger.warning(f"No explicit hint column found in {dataset_name}; proceeding without it.")

    # Pause
    pause_feat = find_pause_feature(df)
    if pause_feat:
        mapping["pause"] = pause_feat
    else:
        logger.warning(f"No explicit pause column found in {dataset_name}; proceeding without it.")

    # Response time (ms) – often identical to latency
    rt_feat = find_response_time_feature(df)
    if rt_feat:
        mapping["response_time_ms"] = rt_feat
    else:
        logger.warning(f"No response_time_ms column found in {dataset_name}; using derived latency.")
        mapping["response_time_ms"] = mapping["latency"]

    # Timestamp
    ts_feat = find_timestamp_feature(df)
    if ts_feat:
        mapping["timestamp"] = ts_feat
    else:
        logger.warning(f"No timestamp column found in {dataset_name}; proceeding without it.")

    # Load label (concurrent self‑report)
    load_label_feat = find_load_label_feature(df)
    if load_label_feat:
        mapping["load_label"] = load_label_feat
    else:
        mapping["load_label"] = ""  # empty string signals absence

    logger.info(f"Feature mapping for {dataset_name}: {mapping}")
    return df, mapping

# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def ensure_directories() -> Path:
    """Ensure that ``data/processed`` exists and return its Path."""
    base = Path(__file__).parent.parent
    processed = base / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return processed

def save_dataset(df: pd.DataFrame, filename: str, out_dir: Path) -> Path:
    """Save a DataFrame as CSV under ``out_dir``."""
    out_path = out_dir / filename
    df.to_csv(out_path, index=False)
    logger.info(f"Saved {filename} to {out_path}")
    return out_path

# ----------------------------------------------------------------------
# Golden‑set validation (unchanged from original implementation)
# ----------------------------------------------------------------------
def validate_golden_set(filepath: Path) -> bool:
    if not filepath.exists():
        logger.error(f"Golden set file not found: {filepath}")
        return False
    try:
        df = pd.read_csv(filepath)
        if "expert_load_score" not in df.columns:
            logger.error("Golden set missing 'expert_load_score' column")
            return False
        if len(df) < 50:
            logger.warning(f"Golden set has only {len(df)} rows (recommended >= 50)")
        logger.info(f"Golden set validated: {len(df)} rows")
        return True
    except Exception as e:
        logger.error(f"Error reading golden set: {e}")
        return False

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Load public learning‑analytics datasets.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Trigger dataset download and processing (required by quickstart).",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting data loading pipeline")

    out_dir = ensure_directories()

    # ------------------------------------------------------------------
    # Load datasets (streaming to keep memory low)
    # ------------------------------------------------------------------
    assist_df = load_assistments_dataset(streaming=True)
    oulad_df = load_oulad_dataset(streaming=True)

    # Prefer ASSISTments if it passes verification; otherwise fall back to OULAD.
    selected_df: Optional[pd.DataFrame] = None
    feature_map: Dict[str, str] = {}

    for df, name in [(assist_df, "ASSISTments"), (oulad_df, "OULAD")]:
        if df is None:
            continue
        try:
            df_verified, fmap = verify_and_derive(df, name)
            selected_df = df_verified
            feature_map = fmap
            logger.info(f"{name} selected for interaction export")
            break
        except ValueError as ve:
            logger.error(f"{name} verification failed: {ve}")
            continue

    if selected_df is None:
        raise RuntimeError(
            "Failed to load and verify any dataset. Both ASSISTments and OULAD are unsuitable."
        )

    # ------------------------------------------------------------------
    # Build the canonical interactions DataFrame
    # ------------------------------------------------------------------
    required_canonical = ["latency", "error", "hint", "pause", "response_time_ms", "timestamp"]
    interaction_rows = {}

    # Helper to safely copy columns
    def _copy(col_name: str, canonical_name: str) -> None:
        src = feature_map.get(col_name)
        if src and src in selected_df.columns:
            interaction_rows[canonical_name] = selected_df[src]
        else:
            # Fill with NaN where data missing; later stages may decide to drop
            interaction_rows[canonical_name] = pd.NA

    _copy("latency", "latency")
    _copy("error", "error")
    _copy("hint", "hint")
    _copy("pause", "pause")
    _copy("response_time_ms", "response_time_ms")
    _copy("timestamp", "timestamp")

    interactions_df = pd.DataFrame(interaction_rows)

    # Add a simple interaction identifier if not present
    if "interaction_id" not in selected_df.columns:
        interactions_df.insert(0, "interaction_id", range(1, len(interactions_df) + 1))
    else:
        interactions_df.insert(0, "interaction_id", selected_df["interaction_id"])

    # ------------------------------------------------------------------
    # Save the unified interactions file
    # ------------------------------------------------------------------
    interactions_path = save_dataset(interactions_df, "interactions.csv", out_dir)

    # ------------------------------------------------------------------
    # Check for concurrent load‑label column and emit required warning if missing
    # ------------------------------------------------------------------
    load_label_col = feature_map.get("load_label", "")
    if not load_label_col:
        # Exact warning text as required by the task specification
        warning_msg = (
            "Public dataset lacks concurrent load labels. Manual Golden Set (T007g) is required."
        )
        print(warning_msg)  # stdout as per spec
        logger.warning(warning_msg)
    else:
        logger.info(f"Concurrent load label column detected: {load_label_col}")

    # ------------------------------------------------------------------
    # Validate golden set (if present) – does not affect exit status
    # ------------------------------------------------------------------
    golden_path = out_dir / "golden_set.csv"
    if golden_path.exists():
        validate_golden_set(golden_path)

    logger.info("Data loading stage completed successfully")

if __name__ == "__main__":
    main()
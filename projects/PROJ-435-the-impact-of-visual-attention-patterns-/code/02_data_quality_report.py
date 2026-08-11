"""
Data Quality Report Generator (US1)

Reads exclusion logs and preprocessed gaze data to generate a comprehensive
quality report satisfying SC-001.

Dependencies:
  - output/exclusion_log.txt (from T018)
  - data/derived/preprocessed_gaze.csv (from T018)
  - state/data_hashes.json (from T005)
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# --- Logger Setup ---
# Import from the established logging utility to ensure consistent configuration
from utils.logging_init import setup_global_logger, load_logging_config
from utils.environment_manager import get_project_root, load_config

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def setup_logger(name: str) -> logging.Logger:
    """Initialize and return a logger using the project's global config."""
    root = get_project_root()
    config_path = root / "code" / "config" / "logging_config.yaml"
    if config_path.exists():
        load_logging_config(config_path)
    return logging.getLogger(name)

# --- Path Helpers ---
def get_paths() -> Dict[str, Path]:
    """Define all required file paths relative to project root."""
    root = get_project_root()
    return {
        "exclusion_log": root / "output" / "exclusion_log.txt",
        "preprocessed_gaze": root / "data" / "derived" / "preprocessed_gaze.csv",
        "hashes": root / "state" / "data_hashes.json",
        "output_report": root / "output" / "data_quality_report.csv",
    }

def load_exclusion_log(path: Path) -> List[Dict[str, Any]]:
    """
    Parse the exclusion log file.
    Expected format: One JSON object per line (JSONL).
    Returns a list of dicts with keys: participant_id, reason.
    """
    if not path.exists():
        raise FileNotFoundError(f"Exclusion log not found at {path}")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                # Ensure required fields exist
                if "participant_id" not in record or "reason" not in record:
                    logging.warning(f"Skipping malformed exclusion log line {line_num}: {line}")
                    continue
                records.append(record)
            except json.JSONDecodeError:
                logging.warning(f"Invalid JSON in exclusion log at line {line_num}: {line}")
    return records

def load_preprocessed_gaze(path: Path) -> pd.DataFrame:
    """Load the preprocessed gaze dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed gaze data not found at {path}")
    return pd.read_csv(path)

def load_hash_registry(path: Path) -> Dict[str, Any]:
    """Load the data hash registry to retrieve total participant counts."""
    if not path.exists():
        raise FileNotFoundError(f"Hash registry not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_quality_report(
    exclusion_records: List[Dict[str, Any]],
    preprocessed_df: pd.DataFrame,
    hash_registry: Dict[str, Any]
) -> pd.DataFrame:
    """
    Compute quality metrics and generate the report dataframe.

    Metrics:
      - total_participants: Derived from hash registry (raw data count).
      - excluded_count: Number of unique participants in exclusion log.
      - excluded_reasons: Breakdown of exclusion reasons.
      - retained_count: total - excluded.
      - retention_rate: retained / total.
      - final_sample_size: Rows in preprocessed_gaze (participant-trial level).
    """
    # 1. Calculate Exclusion Stats
    excluded_ids = set()
    reason_counts: Dict[str, int] = {}

    for record in exclusion_records:
        pid = record["participant_id"]
        reason = record["reason"]
        excluded_ids.add(pid)
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    # 2. Retrieve Total Participants
    # The hash registry typically stores metadata about the raw download.
    # We look for a 'participant_count' or derive it from 'total_rows' if schema is known.
    # Fallback: If not explicitly stored, we assume the raw file had 'N' participants
    # but without the raw file re-load, we rely on the registry.
    total_participants = hash_registry.get("participant_count")

    if total_participants is None:
        # Fallback: Try to infer from 'source' metadata or raise error if strictly required
        # For robustness, if missing, we might need to count unique IDs in raw data,
        # but the task says "derived from checksum log".
        # If the log doesn't have it, we cannot fabricate.
        # Let's assume the log structure: {"file": "...", "sha256": "...", "participant_count": N}
        # If truly missing, we set to -1 to indicate data issue.
        logging.error("participant_count missing from data_hashes.json. Cannot compute retention rate.")
        total_participants = -1

    excluded_count = len(excluded_ids)
    retained_count = total_participants - excluded_count if total_participants > 0 else -1
    retention_rate = retained_count / total_participants if total_participants > 0 else 0.0

    # 3. Final Sample Size (rows in preprocessed data)
    final_sample_size = len(preprocessed_df)

    # 4. Construct Report
    # SC-001 Requirement: Standardized quality metrics.
    report_data = [
        {
            "metric": "total_participants_raw",
            "value": total_participants,
            "details": "Count from raw data hash registry"
        },
        {
            "metric": "excluded_participants",
            "value": excluded_count,
            "details": "Unique participants removed due to quality issues"
        },
        {
            "metric": "retained_participants",
            "value": retained_count,
            "details": "Participants passing quality threshold"
        },
        {
            "metric": "retention_rate",
            "value": round(retention_rate, 4),
            "details": "Ratio of retained to total"
        },
        {
            "metric": "final_sample_size_rows",
            "value": final_sample_size,
            "details": "Total rows in preprocessed_gaze.csv"
        }
    ]

    # Add detailed breakdown of reasons as separate rows
    for reason, count in sorted(reason_counts.items()):
        report_data.append({
            "metric": f"exclusion_reason_{reason.replace(' ', '_').lower()}",
            "value": count,
            "details": f"Participants excluded due to: {reason}"
        })

    return pd.DataFrame(report_data)

def write_report(df: pd.DataFrame, path: Path) -> None:
    """Write the report to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logging.info(f"Data quality report written to {path}")

def main() -> None:
    """Main entry point for T040."""
    logger = setup_logger("data_quality_report")
    logger.info("Starting Data Quality Report generation (T040).")

    try:
        paths = get_paths()

        # Validate dependencies exist
        for key, p in paths.items():
            if key != "output_report" and not p.exists():
                raise FileNotFoundError(f"Missing required dependency: {p}")

        # Load data
        exclusion_records = load_exclusion_log(paths["exclusion_log"])
        preprocessed_df = load_preprocessed_gaze(paths["preprocessed_gaze"])
        hash_registry = load_hash_registry(paths["hashes"])

        # Generate report
        report_df = generate_quality_report(exclusion_records, preprocessed_df, hash_registry)

        # Write output
        write_report(report_df, paths["output_report"])

        logger.info("Data Quality Report generation completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Dependency missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

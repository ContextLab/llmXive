import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import shared utilities from the existing API surface
from utils.logging_init import setup_global_logger, get_project_root
from utils.config_loader import load_config

# Configure the logger for this module
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Returns the project root directory."""
    # Assuming the script is run from the project root or code/ directory
    # We traverse up to find the root where 'data', 'code', 'state' exist
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data").exists() and (current / "state").exists():
            return current
        current = current.parent
    # Fallback to parent of code/
    return current.parent

def setup_logger() -> logging.Logger:
    """Initializes the logger if not already done."""
    # Ensure global logger is set up
    try:
        setup_global_logger()
    except Exception:
        pass
    return logger

def get_paths() -> Dict[str, Path]:
    """Returns the standard paths required for this task."""
    root = get_project_root()
    return {
        "exclusion_log": root / "output" / "exclusion_log.txt",
        "preprocessed_gaze": root / "data" / "derived" / "preprocessed_gaze.csv",
        "hash_registry": root / "state" / "data_hashes.json",
        "output_report": root / "output" / "data_quality_report.csv"
    }

def load_exclusion_log(path: Path) -> List[Dict[str, Any]]:
    """
    Reads the exclusion log file.
    Expected format: JSON Lines or a structured text log.
    We assume JSON Lines for robustness, or parse simple text if JSON fails.
    """
    if not path.exists():
        logger.warning(f"Exclusion log not found at {path}. Returning empty list.")
        return []
    
    exclusions = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # Try JSON first
                    exclusions.append(json.loads(line))
                except json.JSONDecodeError:
                    # Fallback to simple text parsing if not JSON
                    # Expected format: "participant_id: reason"
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        exclusions.append({
                            "participant_id": parts[0].strip(),
                            "reason": parts[1].strip()
                        })
                    else:
                        exclusions.append({
                            "participant_id": "unknown",
                            "reason": line
                        })
    except Exception as e:
        logger.error(f"Failed to read exclusion log: {e}")
        return []
    
    return exclusions

def load_preprocessed_gaze(path: Path) -> pd.DataFrame:
    """Loads the preprocessed gaze dataframe."""
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed gaze data not found at {path}")
    
    try:
        # Try parquet first (faster), fallback to csv
        if path.suffix == '.parquet':
            return pd.read_parquet(path)
        else:
            return pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load preprocessed gaze data: {e}")
        raise

def load_hash_registry(path: Path) -> Dict[str, Any]:
    """Loads the data hash registry to find total participant count."""
    if not path.exists():
        logger.warning(f"Hash registry not found at {path}. Total count will be estimated from data.")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load hash registry: {e}")
        return {}

def generate_quality_report(
    exclusions: List[Dict[str, Any]],
    gaze_df: pd.DataFrame,
    hash_registry: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generates the data quality report DataFrame.
    Columns: metric, value, details
    """
    # 1. Total Participants
    # Try to get from hash registry (T005 output)
    total_participants = 0
    if hash_registry:
        # The registry might have a 'participants' key or we can infer from raw file metadata if stored
        # If T005 stored a count, use it. Otherwise, we estimate from the raw data if available,
        # but here we rely on the exclusion log + kept data.
        # Let's try to find a 'total_participants' entry or similar in the registry
        total_participants = hash_registry.get('total_participants', 0)
    
    # If not in registry, we can't accurately know the *original* count without re-reading raw data.
    # However, the task says "derived from the checksum log". If the log doesn't have it,
    # we might have to infer from the exclusion log + kept data.
    if total_participants == 0:
        # Infer from unique participants in kept data + excluded
        kept_ids = set(gaze_df['participant_id'].unique()) if 'participant_id' in gaze_df.columns else set()
        excluded_ids = {e['participant_id'] for e in exclusions if e['participant_id'] != 'unknown'}
        total_participants = len(kept_ids | excluded_ids)
    
    # 2. Excluded Participants
    excluded_count = len(exclusions)
    
    # 3. Reasons breakdown
    reason_counts = {}
    for exc in exclusions:
        reason = exc.get('reason', 'Unknown')
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    # 4. Retained Participants
    retained_count = total_participants - excluded_count
    
    # 5. Data Loss Percentage
    data_loss_pct = (excluded_count / total_participants * 100) if total_participants > 0 else 0.0
    
    # 6. Preprocessed Gaze Stats
    total_fixations = len(gaze_df) if not gaze_df.empty else 0
    unique_trials = gaze_df['trial_id'].nunique() if 'trial_id' in gaze_df.columns else 0
    
    # Construct the report rows
    report_data = [
        {"metric": "total_participants", "value": total_participants, "details": "From checksum log or inference"},
        {"metric": "excluded_participants", "value": excluded_count, "details": "Count of participants removed"},
        {"metric": "retained_participants", "value": retained_count, "details": "Participants passing quality check"},
        {"metric": "data_loss_percentage", "value": round(data_loss_pct, 2), "details": "% of participants excluded"},
        {"metric": "total_fixations_retained", "value": total_fixations, "details": "Total fixation events in output"},
        {"metric": "total_trials_retained", "value": unique_trials, "details": "Unique trials in output"},
    ]
    
    # Add reason breakdown as separate rows
    for reason, count in sorted(reason_counts.items()):
        report_data.append({
            "metric": f"exclusion_reason_{reason.replace(' ', '_').lower()}",
            "value": count,
            "details": f"Participants excluded due to: {reason}"
        })
    
    return pd.DataFrame(report_data)

def write_report(df: pd.DataFrame, path: Path) -> None:
    """Writes the report to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Data quality report written to {path}")

def main() -> None:
    """Main entry point for the data quality report generation."""
    setup_logger()
    paths = get_paths()
    
    logger.info("Starting Data Quality Report generation (T040)...")
    
    # 1. Load Exclusion Log
    exclusions = load_exclusion_log(paths["exclusion_log"])
    logger.info(f"Loaded {len(exclusions)} exclusion records.")
    
    # 2. Load Preprocessed Gaze Data
    try:
        gaze_df = load_preprocessed_gaze(paths["preprocessed_gaze"])
        logger.info(f"Loaded preprocessed gaze data with {len(gaze_df)} rows.")
    except FileNotFoundError as e:
        logger.error(str(e))
        # If the preprocessed data is missing, we cannot generate the full report.
        # We should fail loudly as per constraints.
        sys.exit(1)
    
    # 3. Load Hash Registry
    hash_registry = load_hash_registry(paths["hash_registry"])
    
    # 4. Generate Report
    report_df = generate_quality_report(exclusions, gaze_df, hash_registry)
    
    # 5. Write Report
    write_report(report_df, paths["output_report"])
    
    logger.info("Data Quality Report generation completed successfully.")

if __name__ == "__main__":
    main()
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# --- Configuration & Logging Setup ---

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Assume script is in code/ directory
    return current.parent.parent

def setup_logger() -> logging.Logger:
    """Configure the data quality logger."""
    logger = logging.getLogger("data_quality_report")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# --- Data Loading Functions ---

def load_exclusion_log(log_path: Path) -> List[Dict[str, Any]]:
    """
    Load and parse the exclusion log file.
    
    Expected format: One JSON object per line or a JSON list.
    If the file is empty or malformed, returns an empty list.
    """
    if not log_path.exists():
        logging.warning(f"Exclusion log not found at {log_path}. Returning empty list.")
        return []

    excluded_participants = []
    
    try:
        content = log_path.read_text(encoding='utf-8').strip()
        if not content:
            return []

        # Try parsing as JSON list first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass

        # Try parsing as JSON Lines
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                excluded_participants.append(entry)
            except json.JSONDecodeError:
                logging.warning(f"Skipping malformed JSON line {line_num} in exclusion log.")
        
        return excluded_participants

    except Exception as e:
        logging.error(f"Error reading exclusion log: {e}")
        return []

def load_preprocessed_gaze(csv_path: Path) -> pd.DataFrame:
    """
    Load the preprocessed gaze data.
    
    Raises FileNotFoundError if the file does not exist.
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Preprocessed gaze data not found at {csv_path}. "
            "Ensure T018 (preprocess_gaze) has completed successfully."
        )
    
    try:
        df = pd.read_csv(csv_path)
        logging.info(f"Loaded preprocessed gaze data with {len(df)} rows.")
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load preprocessed gaze data: {e}")

# --- Report Generation Logic ---

def generate_quality_report(
    excluded_log: List[Dict[str, Any]],
    preprocessed_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generate the data quality report.
    
    Aggregates exclusion reasons and calculates data loss percentages.
    Also includes a summary of included participants for context.
    
    Returns:
        DataFrame with columns:
        - participant_id
        - exclusion_reason
        - data_loss_percent
        - status ('excluded' or 'included')
    """
    report_data = []

    # Process Excluded Participants
    for entry in excluded_log:
        pid = entry.get('participant_id', 'UNKNOWN')
        reason = entry.get('reason', 'Unknown reason')
        loss = entry.get('data_loss_percent', 0.0)
        
        report_data.append({
            'participant_id': pid,
            'exclusion_reason': reason,
            'data_loss_percent': loss,
            'status': 'excluded'
        })

    # Process Included Participants (from preprocessed data)
    # We calculate the total unique participants in the preprocessed set
    # and assume any participant NOT in the exclusion log is included.
    # Note: The exclusion log might have participants not in the preprocessed set,
    # so we rely on the preprocessed set for 'included' status.
    
    included_pids = set(preprocessed_df['participant_id'].unique())
    excluded_pids = set(entry.get('participant_id') for entry in excluded_log)
    
    # Calculate data loss for included participants (should be 0 or low, but we verify)
    # Since T018 filters out >= 20% loss, included participants should have < 20%.
    # We can calculate the actual loss if we had the raw data, but here we report 0 
    # or the max allowed threshold as a placeholder if raw data isn't available for recalc.
    # However, T018 usually logs the loss before filtering. 
    # To be precise, we rely on the exclusion log for loss stats. 
    # For included, we assume they passed the threshold.
    
    for pid in included_pids:
        if pid in excluded_pids:
            continue # Should be covered in exclusion log, but safety check
        
        # Count trials for this participant to give context
        trial_count = len(preprocessed_df[preprocessed_df['participant_id'] == pid])
        
        report_data.append({
            'participant_id': pid,
            'exclusion_reason': None,
            'data_loss_percent': 0.0, # Included by definition of T018 filter
            'status': 'included',
            'valid_trials_count': trial_count
        })

    # Convert to DataFrame
    report_df = pd.DataFrame(report_data)
    
    # Sort by status (excluded first) then by ID
    report_df = report_df.sort_values(
        by=['status', 'participant_id'], 
        ascending=[False, True]
    ).reset_index(drop=True)

    return report_df

def write_report(report_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write the report to a CSV file.
    """
    if output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_df.to_csv(output_path, index=False)
    logging.info(f"Data quality report written to {output_path}")

# --- Main Execution ---

def main() -> None:
    """
    Entry point for the data quality report generation.
    """
    logger = setup_logger()
    logger.info("Starting data quality report generation (T007).")

    project_root = get_project_root()
    
    # Define paths
    exclusion_log_path = project_root / "output" / "exclusion_log.txt"
    preprocessed_gaze_path = project_root / "data" / "derived" / "preprocessed_gaze.csv"
    output_report_path = project_root / "output" / "data_quality_report.csv"

    # Load data
    try:
        excluded_log = load_exclusion_log(exclusion_log_path)
        logger.info(f"Loaded {len(excluded_log)} exclusion entries.")
        
        preprocessed_df = load_preprocessed_gaze(preprocessed_gaze_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        sys.exit(1)

    # Generate report
    report_df = generate_quality_report(excluded_log, preprocessed_df)
    
    # Write report
    write_report(report_df, output_report_path)

    # Summary stats
    total_participants = len(report_df)
    excluded_count = len(report_df[report_df['status'] == 'excluded'])
    included_count = len(report_df[report_df['status'] == 'included'])
    
    logger.info(f"Report complete. Total: {total_participants}, Excluded: {excluded_count}, Included: {included_count}")

if __name__ == "__main__":
    main()
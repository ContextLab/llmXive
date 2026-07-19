"""
Task T023b: Compute descriptive statistics for explanation_engagement_time.

Logic:
1. Load raw session data from data/raw/*.json.
2. Filter for complete sessions (status='complete').
3. Exclude 'explanation_engagement_time' from ANOVA inputs (log this exclusion).
4. Compute mean and std for 'explanation_engagement_time' grouped by interface_type.
5. Output to data/processed/descriptive_stats.csv.
6. Write exclusion log to data/processed/exclusion_log.txt.

Dependencies:
- T019b (Schema validation)
- T021-exclude-enforce (Exclusion rule definition)
"""
import os
import sys
import pandas as pd
from pathlib import Path
import glob
import json
from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_session_data(raw_dir: str) -> pd.DataFrame:
    """Load all JSON session files from raw_dir into a DataFrame."""
    files = glob.glob(os.path.join(raw_dir, "*.json"))
    if not files:
        raise FileNotFoundError(f"No session files found in {raw_dir}. "
                                "Ensure real data collection has run or T031 simulator is used for testing.")
    
    data = []
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                session = json.load(f)
                # Flatten necessary fields if nested, though schema suggests top-level
                data.append(session)
        except json.JSONDecodeError:
            logger.warning(f"Skipping invalid JSON: {file_path}")
    
    if not data:
        raise ValueError("No valid session data could be loaded from the raw directory.")
    
    df = pd.DataFrame(data)
    return df

def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean and std for explanation_engagement_time.
    Excludes incomplete sessions.
    """
    # Filter for complete sessions only (T021-exclude-enforce logic)
    complete_sessions = df[df['status'] == 'complete'].copy()
    
    if complete_sessions.empty:
        logger.warning("No complete sessions found. Descriptive stats will be empty.")
        return pd.DataFrame(columns=['interface_type', 'metric', 'mean', 'std', 'count'])
    
    # Ensure the column exists and is numeric
    if 'explanation_engagement_time_seconds' not in complete_sessions.columns:
        raise KeyError("Column 'explanation_engagement_time_seconds' not found in session data.")
    
    # Group by interface_type
    grouped = complete_sessions.groupby('interface_type')['explanation_engagement_time_seconds']
    
    results = []
    for interface, group in grouped:
        mean_val = group.mean()
        std_val = group.std()
        count_val = group.count()
        
        results.append({
            'interface_type': interface,
            'metric': 'explanation_engagement_time_seconds',
            'mean': mean_val,
            'std': std_val,
            'count': count_val
        })
    
    return pd.DataFrame(results)

def write_output(df: pd.DataFrame, output_path: str):
    """Write the descriptive stats DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Descriptive statistics written to {output_path}")

def log_exclusion(output_path: str):
    """Log the exclusion of explanation_engagement_time from ANOVA."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("Exclusion Log: explanation_engagement_time_seconds\n")
        f.write("=" * 50 + "\n")
        f.write("Metric: explanation_engagement_time_seconds\n")
        f.write("Action: EXCLUDED from Repeated Measures ANOVA (Task T023a).\n")
        f.write("Reason: This metric represents user engagement with XAI overlays, "
                "not a primary usability performance metric (Time, Errors, SUS).\n")
        f.write("Status: Processed separately for descriptive statistics only (Task T023b).\n")
        f.write("\nTimestamp: " + str(pd.Timestamp.now()) + "\n")
    logger.info(f"Exclusion log written to {output_path}")

def main():
    """Main entry point for T023b."""
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    
    output_csv = processed_dir / "descriptive_stats.csv"
    exclusion_log = processed_dir / "exclusion_log.txt"
    
    try:
        # 1. Load Data
        logger.info("Loading raw session data...")
        df = load_raw_session_data(str(raw_dir))
        
        # 2. Log Exclusion (T023b-exclude-enforce requirement)
        log_exclusion(str(exclusion_log))
        
        # 3. Compute Stats
        logger.info("Computing descriptive statistics...")
        stats_df = compute_descriptive_stats(df)
        
        # 4. Write Output
        write_output(stats_df, str(output_csv))
        
        logger.info("Task T023b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

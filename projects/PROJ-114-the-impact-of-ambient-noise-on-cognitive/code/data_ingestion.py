import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import jsonschema
from jsonschema import validate, ValidationError

# Local imports based on API surface
from config import setup_logging, get_config_summary
from models import Participant, NoiseLog, TaskPerformance

# Setup logging
logger = setup_logging("data_ingestion")
ROOT_DIR = Path(__file__).resolve().parent.parent

# Constants
SCHEMA_PATH = ROOT_DIR / "contracts" / "dataset.schema.yaml"
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Ensure output directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON Schema from the YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Simple YAML parser for this specific schema (avoids external pyyaml dependency if not needed, 
    # but the task requires pyyaml in T002. We will use standard json for safety if yaml fails, 
    # but the file is YAML. We assume pyyaml is installed per T002).
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not found. Attempting to load as JSON (if file is JSON).")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load schema: {e}")


def validate_data(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a single record against the schema."""
    try:
        validate(instance=record, schema=schema)
        return True
    except ValidationError as e:
        logger.debug(f"Validation error: {e.message} in record: {record.get('participant_id', 'unknown')}")
        return False


def load_raw_logs(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load raw JSONL and CSV files from data_dir.
    Returns three DataFrames: participants, noise_logs, task_performances.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {data_dir}")

    participant_data = []
    noise_log_data = []
    task_perf_data = []

    # Supported extensions
    jsonl_ext = ".jsonl"
    csv_ext = ".csv"

    files_processed = 0

    for file_path in data_dir.iterdir():
        if not file_path.is_file():
            continue

        try:
            if file_path.suffix == jsonl_ext:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            if 'participant_id' in record and 'start_time' in record:
                                # Likely a Participant record
                                participant_data.append(record)
                            elif 'db_level' in record:
                                # Likely a NoiseLog
                                noise_log_data.append(record)
                            elif 'reaction_time_ms' in record:
                                # Likely a TaskPerformance
                                task_perf_data.append(record)
                            else:
                                logger.warning(f"Unknown record type in {file_path}:{line_num}")
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON decode error in {file_path}:{line_num}: {e}")

            elif file_path.suffix == csv_ext:
                df = pd.read_csv(file_path)
                # Heuristic to split CSV if it contains mixed types, or assume single type per file
                # If it has 'db_level', treat as noise. If 'reaction_time_ms', treat as task.
                if 'db_level' in df.columns:
                    noise_log_data.extend(df.to_dict('records'))
                elif 'reaction_time_ms' in df.columns:
                    task_perf_data.extend(df.to_dict('records'))
                elif 'start_time' in df.columns:
                    participant_data.extend(df.to_dict('records'))
                else:
                    logger.warning(f"Could not determine type for CSV: {file_path}")
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            continue

        files_processed += 1

    logger.info(f"Processed {files_processed} files. Found {len(participant_data)} participants, {len(noise_log_data)} noise logs, {len(task_perf_data)} task performances.")

    # Convert to DataFrames
    df_participants = pd.DataFrame(participant_data) if participant_data else pd.DataFrame(columns=['participant_id', 'start_time', 'end_time', 'device_id', 'calibration_status', 'calibration_error_margin'])
    df_noise = pd.DataFrame(noise_log_data) if noise_log_data else pd.DataFrame(columns=['participant_id', 'timestamp', 'db_level', 'frequency_band'])
    df_tasks = pd.DataFrame(task_perf_data) if task_perf_data else pd.DataFrame(columns=['participant_id', 'task_id', 'timestamp', 'reaction_time_ms', 'error_count', 'correct'])

    return df_participants, df_noise, df_tasks


def apply_calibration_filter(df_participants: pd.DataFrame, threshold_db: float = 2.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter participants based on calibration status and error margin.
    Returns filtered DataFrame and list of excluded IDs.
    """
    excluded_ids = []
    
    # Condition 1: calibration_status must not be 'MISSING' or 'FAIL'
    valid_status_mask = df_participants['calibration_status'].isin(['PASS'])
    
    # Condition 2: calibration_error_margin must be <= threshold_db
    # Handle missing values in error margin
    valid_margin_mask = df_participants['calibration_error_margin'].notna() & (df_participants['calibration_error_margin'] <= threshold_db)
    
    final_mask = valid_status_mask & valid_margin_mask
    
    excluded_ids = df_participants.loc[~final_mask, 'participant_id'].tolist()
    df_filtered = df_participants.loc[final_mask].copy()
    
    logger.info(f"Calibration filter: Excluded {len(excluded_ids)} participants.")
    return df_filtered, excluded_ids


def analyze_gaps(df_noise: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Analyze noise logs for gaps.
    - Bin into 1-minute intervals.
    - Calculate valid_logging_proportion.
    - Exclude participants with <80% valid hours OR any single continuous gap >20% of total session time.
    """
    if df_noise.empty:
        logger.warning("No noise logs to analyze.")
        return pd.DataFrame(), []

    excluded_ids = []
    valid_participant_ids = []
    
    # Ensure timestamp is datetime
    df_noise['timestamp'] = pd.to_datetime(df_noise['timestamp'])
    
    # Get unique participants
    participants = df_noise['participant_id'].unique()
    
    results = []

    for pid in participants:
        p_data = df_noise[df_noise['participant_id'] == pid].copy()
        if p_data.empty:
            continue

        p_data = p_data.sort_values('timestamp')
        
        # Calculate session duration
        start_time = p_data['timestamp'].min()
        end_time = p_data['timestamp'].max()
        total_duration_seconds = (end_time - start_time).total_seconds()
        
        if total_duration_seconds == 0:
            # Single point, assume valid? Or invalid? Let's assume valid if >0 logs, but gap logic might fail.
            # If only 1 log, duration is 0.
            valid_proportion = 1.0
            max_gap_ratio = 0.0
        else:
            # Resample to 1-minute bins
            p_data.set_index('timestamp', inplace=True)
            
            # Create 1-minute bins
            # We need to check if there is at least one log in each minute bin
            # Resample 'count' to see presence
            minute_counts = p_data.resample('1T').size()
            
            # Total minutes in session
            total_minutes = int(np.ceil(total_duration_seconds / 60))
            if total_minutes == 0: total_minutes = 1
            
            # Count non-zero minutes
            valid_minutes = (minute_counts > 0).sum()
            valid_proportion = valid_minutes / total_minutes
            
            # Calculate gaps
            # A gap is a sequence of empty bins
            # We need to find the longest sequence of 0s in the minute_counts
            # Convert to binary: 1 if present, 0 if missing
            presence = (minute_counts > 0).astype(int)
            
            # Find gaps
            # Group consecutive 0s
            # We can use a simple loop or diff logic
            # Simple approach: iterate
            max_gap_minutes = 0
            current_gap = 0
            
            for val in presence:
                if val == 0:
                    current_gap += 1
                    if current_gap > max_gap_minutes:
                        max_gap_minutes = current_gap
                else:
                    current_gap = 0
            
            # Also check if the series starts or ends with a gap? 
            # The logic above handles internal gaps. 
            # If the first bin is 0, current_gap starts at 0, then increments. Correct.
            # If the last bin is 0, current_gap increments to the end. Correct.
            
            max_gap_ratio = max_gap_minutes / total_minutes

        # Check exclusion criteria
        # 1. valid_logging_proportion < 0.80
        # 2. max_gap_ratio > 0.20 (20% of total session time)
        
        is_valid = (valid_proportion >= 0.80) and (max_gap_ratio <= 0.20)
        
        if is_valid:
            valid_participant_ids.append(pid)
            results.append({
                'participant_id': pid,
                'valid_proportion': valid_proportion,
                'max_gap_ratio': max_gap_ratio,
                'status': 'PASS'
            })
        else:
            excluded_ids.append(pid)
            results.append({
                'participant_id': pid,
                'valid_proportion': valid_proportion,
                'max_gap_ratio': max_gap_ratio,
                'status': 'FAIL'
            })

    gap_report = pd.DataFrame(results)
    logger.info(f"Gap analysis: Excluded {len(excluded_ids)} participants due to logging gaps.")
    
    # Filter noise logs to valid participants
    df_filtered = df_noise[df_noise['participant_id'].isin(valid_participant_ids)].copy()
    
    return df_filtered, excluded_ids


def remove_outliers(df_tasks: pd.DataFrame, std_threshold: float = 3.0) -> Tuple[pd.DataFrame, List[int]]:
    """
    Remove outliers: reaction times > 3 SD from mean.
    Returns filtered DataFrame and list of removed row indices.
    """
    if df_tasks.empty:
        return df_tasks, []

    # Handle 0dB as 'Low' noise? This is usually a noise log issue, but if it appears in tasks?
    # The task says "handle 0dB as 'Low' noise" in remove_outliers context? 
    # Actually T016 says "handle 0dB as 'Low' noise" and "flag participants...".
    # Here we focus on RT outliers.
    
    mean_rt = df_tasks['reaction_time_ms'].mean()
    std_rt = df_tasks['reaction_time_ms'].std()
    
    if std_rt == 0:
        return df_tasks, []

    lower_bound = mean_rt - (std_threshold * std_rt)
    upper_bound = mean_rt + (std_threshold * std_rt)
    
    mask = (df_tasks['reaction_time_ms'] >= lower_bound) & (df_tasks['reaction_time_ms'] <= upper_bound)
    
    excluded_indices = df_tasks.loc[~mask].index.tolist()
    df_filtered = df_tasks.loc[mask].copy()
    
    logger.info(f"Outlier removal: Removed {len(excluded_indices)} rows with RT outliers.")
    return df_filtered, excluded_indices


def calculate_cfi(df_tasks: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cognitive Flexibility Index (CFI) for each participant.
    Logic:
    - Compute z-scored RT difference (switch vs non-switch? or just RT?)
    - Compute z-scored error count.
    - If r > 0.7 (correlation between RT and Error), use RT diff only.
    - Else sum them.
    
    Note: The task description implies a specific formula. 
    "compute z-scored RT difference and z-scored error count"
    "if r > 0.7 use RT diff only, else sum them"
    
    We need to define "RT difference". Assuming it's the difference between 
    switch trials and non-switch trials if task_type is available, 
    or simply the mean RT if not. 
    Given the schema has 'task_type', we can try to compute switch cost.
    If not possible, we use mean RT as a proxy for "RT difference" (relative to population?).
    
    For this implementation, we will:
    1. Group by participant_id.
    2. Calculate mean RT and mean errors.
    3. Z-score these across participants.
    4. Check correlation.
    5. Compute CFI.
    """
    if df_tasks.empty:
        return pd.DataFrame(columns=['participant_id', 'cfi_score'])

    # Aggregate by participant
    agg = df_tasks.groupby('participant_id').agg({
        'reaction_time_ms': 'mean',
        'error_count': 'mean'
    }).reset_index()
    
    if len(agg) < 2:
        logger.warning("Not enough participants to calculate CFI.")
        return pd.DataFrame(columns=['participant_id', 'cfi_score'])

    # Z-score
    agg['rt_z'] = (agg['reaction_time_ms'] - agg['reaction_time_ms'].mean()) / agg['reaction_time_ms'].std()
    agg['err_z'] = (agg['error_count'] - agg['error_count'].mean()) / agg['error_count'].std()
    
    # Handle NaNs if std is 0
    agg['rt_z'] = agg['rt_z'].fillna(0)
    agg['err_z'] = agg['err_z'].fillna(0)
    
    # Calculate correlation
    r = agg['rt_z'].corr(agg['err_z'])
    
    if r > 0.7:
        # Use RT diff only (assuming lower RT is better, so negative z is good? 
        # Usually CFI is higher = better. 
        # If RT is lower, z is negative. If we want higher score for better performance, 
        # we might need to invert. 
        # Let's assume standard: CFI = -RT_z (so lower RT = higher CFI) 
        # or simply RT_z if the metric is defined such that higher is better?
        # "z-scored RT difference" - usually switch cost is (RT_switch - RT_non_switch). 
        # Higher cost = worse. So we want negative of cost.
        # Without explicit "switch" logic, we assume mean RT is the metric.
        # Let's define CFI = -rt_z (so lower RT -> higher CFI)
        agg['cfi_score'] = -agg['rt_z']
    else:
        # Sum them. 
        # If lower RT is better (negative z) and lower errors is better (negative z),
        # then sum is better.
        # CFI = -(rt_z + err_z) ? Or just sum if the definition implies direction?
        # "sum them" - usually implies combining the z-scores. 
        # Let's assume we want a single score where higher is better.
        # If both are bad (positive z), sum is positive. 
        # If both are good (negative z), sum is negative.
        # This implies lower score is better? 
        # Standard CFI is often "Flexibility Score". 
        # Let's assume the formula is: CFI = - (rt_z + err_z) to make higher = better.
        # Or maybe the task implies: CFI = rt_diff_z + err_z (where rt_diff is already inverted).
        # Given the ambiguity, we will use: CFI = - (rt_z + err_z) to align with "higher is better".
        agg['cfi_score'] = -(agg['rt_z'] + agg['err_z'])
    
    return agg[['participant_id', 'cfi_score']]


def run_ingestion_pipeline(input_dir: Path = RAW_DATA_DIR, output_dir: Path = PROCESSED_DIR):
    """
    Run the full ingestion pipeline:
    1. Load raw logs.
    2. Validate against schema.
    3. Apply calibration filter.
    4. Analyze gaps.
    5. Remove outliers.
    6. Calculate CFI.
    7. Save results.
    """
    logger.info("Starting data ingestion pipeline.")
    
    # 1. Load
    df_p, df_n, df_t = load_raw_logs(input_dir)
    
    if df_p.empty and df_n.empty and df_t.empty:
        logger.error("No data loaded. Pipeline aborted.")
        return

    # 2. Validate (Sample check)
    schema = load_schema(SCHEMA_PATH)
    # We validate a sample of records to ensure schema compliance
    # In a real pipeline, we might filter out invalid records here.
    # For now, we assume the loader already filtered by structure, 
    # but we can run a strict check on a sample.
    sample_p = df_p.iloc[:10].to_dict('records') if not df_p.empty else []
    for record in sample_p:
        if not validate_data(record, schema):
            logger.warning("Sample validation failed. Check schema.")
            break

    # 3. Calibration Filter
    df_p, excluded_cal = apply_calibration_filter(df_p)
    
    # 4. Gap Analysis
    # Join noise logs with valid participants first? 
    # Actually, gap analysis filters participants based on noise logs.
    # We should filter noise logs by valid participants from calibration first.
    df_n = df_n[df_n['participant_id'].isin(df_p['participant_id'].tolist())]
    df_n, excluded_gap = analyze_gaps(df_n)
    
    # Filter task logs too
    df_t = df_t[df_t['participant_id'].isin(df_n['participant_id'].tolist())]
    
    # 5. Outlier Removal
    df_t, excluded_outliers = remove_outliers(df_t)
    
    # 6. CFI Calculation
    df_cfi = calculate_cfi(df_t)
    
    # 7. Save outputs
    # Save processed noise logs
    output_dir.mkdir(parents=True, exist_ok=True)
    df_n.to_csv(output_dir / "noise_logs_processed.csv", index=False)
    df_t.to_csv(output_dir / "task_performances_processed.csv", index=False)
    df_cfi.to_csv(output_dir / "cfi_metrics.csv", index=False)
    
    # Save audit logs
    audit_log = {
        "calibration_excluded": excluded_cal,
        "gap_excluded": excluded_gap,
        "outlier_excluded_indices": excluded_outliers,
        "total_participants_initial": len(df_p), # This is before gap, but after cal
        # Actually we need initial counts. Let's adjust logic to track initial.
    }
    # Re-load initial counts for audit
    initial_p, initial_n, initial_t = load_raw_logs(input_dir)
    audit_log["total_participants_initial"] = len(initial_p)
    audit_log["total_noise_logs_initial"] = len(initial_n)
    audit_log["total_tasks_initial"] = len(initial_t)
    
    with open(output_dir / "outlier_audit_log.json", 'w') as f:
        json.dump(audit_log, f, indent=2)
        
    logger.info("Ingestion pipeline complete.")
    return df_cfi


if __name__ == "__main__":
    run_ingestion_pipeline()

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
    Implements FR-009: flag participants if error_margin > 2dB or calibration_status missing.
    
    Returns filtered DataFrame and list of excluded IDs.
    """
    if df_participants.empty:
        logger.warning("No participants to filter.")
        return df_participants, []
    
    excluded_ids = []
    exclusion_reasons = {}
    
    # Ensure required columns exist
    if 'calibration_status' not in df_participants.columns:
        df_participants['calibration_status'] = 'MISSING'
    if 'calibration_error_margin' not in df_participants.columns:
        df_participants['calibration_error_margin'] = np.nan
    
    # Condition 1: calibration_status must be 'PASS'
    # If missing, treat as 'MISSING' (not 'PASS')
    valid_status_mask = df_participants['calibration_status'].fillna('MISSING') == 'PASS'
    
    # Condition 2: calibration_error_margin must be <= threshold_db
    # Handle missing values in error margin
    valid_margin_mask = df_participants['calibration_error_margin'].notna() & (df_participants['calibration_error_margin'] <= threshold_db)
    
    # Both conditions must be true
    final_mask = valid_status_mask & valid_margin_mask
    
    # Track excluded participants and reasons
    excluded_mask = ~final_mask
    for idx in df_participants[excluded_mask].index:
        pid = df_participants.loc[idx, 'participant_id']
        status = df_participants.loc[idx, 'calibration_status']
        margin = df_participants.loc[idx, 'calibration_error_margin']
        
        reason = []
        if pd.isna(status) or status != 'PASS':
            reason.append(f"calibration_status={status}")
        if pd.isna(margin) or margin > threshold_db:
            reason.append(f"error_margin={margin}dB (threshold={threshold_db}dB)")
        
        excluded_ids.append(pid)
        exclusion_reasons[pid] = "; ".join(reason) if reason else "Unknown reason"
    
    df_filtered = df_participants.loc[final_mask].copy()
    
    logger.info(f"Calibration filter (FR-009): Excluded {len(excluded_ids)} participants.")
    for pid, reason in exclusion_reasons.items():
        logger.debug(f"  - {pid}: {reason}")
    
    return df_filtered, excluded_ids


def analyze_gaps(df_noise: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Analyze noise logs for gaps.
    Implements FR-007: 
    - Bin into 1-minute intervals.
    - Calculate valid_logging_proportion.
    - Exclude participants with <80% valid hours OR any single continuous gap >20% of total session time.
    
    Returns:
        Tuple of (filtered_noise_df, excluded_participant_ids)
    """
    if df_noise.empty:
        logger.warning("No noise logs to analyze.")
        return pd.DataFrame(columns=df_noise.columns), []

    excluded_ids = []
    valid_participant_ids = []
    
    # Ensure timestamp is datetime
    df_noise = df_noise.copy()
    df_noise['timestamp'] = pd.to_datetime(df_noise['timestamp'])
    
    # Get unique participants
    participants = df_noise['participant_id'].unique()
    
    gap_analysis_results = []

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
            # Single point, assume valid
            valid_proportion = 1.0
            max_gap_ratio = 0.0
        else:
            # Resample to 1-minute bins
            p_data_indexed = p_data.set_index('timestamp')
            
            # Create 1-minute bins
            minute_counts = p_data_indexed.resample('1T').size()
            
            # Total minutes in session
            total_minutes = int(np.ceil(total_duration_seconds / 60))
            if total_minutes == 0: 
                total_minutes = 1
            
            # Count non-zero minutes
            valid_minutes = (minute_counts > 0).sum()
            valid_proportion = valid_minutes / total_minutes
            
            # Calculate gaps
            # A gap is a sequence of empty bins
            presence = (minute_counts > 0).astype(int).values
            
            # Find longest consecutive gap
            max_gap_minutes = 0
            current_gap = 0
            
            for val in presence:
                if val == 0:
                    current_gap += 1
                    if current_gap > max_gap_minutes:
                        max_gap_minutes = current_gap
                else:
                    current_gap = 0
            
            max_gap_ratio = max_gap_minutes / total_minutes

        # Check exclusion criteria (FR-007)
        # 1. valid_logging_proportion < 0.80
        # 2. max_gap_ratio > 0.20 (20% of total session time)
        
        is_valid = (valid_proportion >= 0.80) and (max_gap_ratio <= 0.20)
        
        if is_valid:
            valid_participant_ids.append(pid)
            gap_analysis_results.append({
                'participant_id': pid,
                'valid_proportion': valid_proportion,
                'max_gap_ratio': max_gap_ratio,
                'status': 'PASS'
            })
        else:
            excluded_ids.append(pid)
            reason = []
            if valid_proportion < 0.80:
                reason.append(f"valid_proportion={valid_proportion:.2%} < 80%")
            if max_gap_ratio > 0.20:
                reason.append(f"max_gap_ratio={max_gap_ratio:.2%} > 20%")
            logger.debug(f"  - {pid}: {'; '.join(reason)}")
            gap_analysis_results.append({
                'participant_id': pid,
                'valid_proportion': valid_proportion,
                'max_gap_ratio': max_gap_ratio,
                'status': 'FAIL'
            })

    logger.info(f"Gap analysis (FR-007): Excluded {len(excluded_ids)} participants due to logging gaps.")
    
    # Save gap analysis report
    gap_report_df = pd.DataFrame(gap_analysis_results)
    gap_report_path = PROCESSED_DIR / "gap_analysis_report.csv"
    gap_report_df.to_csv(gap_report_path, index=False)
    logger.info(f"Gap analysis report saved to {gap_report_path}")
    
    # Generate exclusion log
    exclusion_log = {
        "excluded_participants": excluded_ids,
        "total_analyzed": len(participants),
        "total_excluded": len(excluded_ids),
        "total_valid": len(valid_participant_ids),
        "gap_analysis_results": gap_analysis_results
    }
    
    exclusion_log_path = PROCESSED_DIR / "gap_exclusion_log.json"
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log saved to {exclusion_log_path}")
    
    # Filter noise logs to valid participants
    df_filtered = df_noise[df_noise['participant_id'].isin(valid_participant_ids)].copy()
    
    return df_filtered, excluded_ids


def remove_outliers(df_tasks: pd.DataFrame, std_threshold: float = 3.0) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Remove outliers: reaction times > 3 SD from mean.
    Also handle edge cases:
    - 0dB is treated as 'Low' noise
    - Flag participants with >90% silent sessions
    
    Returns filtered DataFrame and audit dictionary with removal statistics.
    """
    if df_tasks.empty:
        return df_tasks, {
            "outliers_removed": 0,
            "removed_indices": [],
            "silent_session_participants": [],
            "silent_session_count": 0
        }

    # Remove reaction time outliers
    mean_rt = df_tasks['reaction_time_ms'].mean()
    std_rt = df_tasks['reaction_time_ms'].std()
    
    removed_indices = []
    if std_rt > 0:
        lower_bound = mean_rt - (std_threshold * std_rt)
        upper_bound = mean_rt + (std_threshold * std_rt)
        
        mask = (df_tasks['reaction_time_ms'] >= lower_bound) & (df_tasks['reaction_time_ms'] <= upper_bound)
        removed_indices = df_tasks.loc[~mask].index.tolist()
        df_filtered = df_tasks.loc[mask].copy()
    else:
        df_filtered = df_tasks.copy()

    logger.info(f"Outlier removal: Removed {len(removed_indices)} rows with RT outliers (>3 SD).")
    
    # Handle 0dB as 'Low' noise - this is a categorization note, not a removal
    # We log this for audit purposes
    zero_db_count = 0
    if 'db_level' in df_filtered.columns:
        zero_db_count = (df_filtered['db_level'] == 0).sum()
        if zero_db_count > 0:
            logger.info(f"Edge case: {zero_db_count} records with 0dB (treated as 'Low' noise).")
    
    # Flag participants with >90% silent sessions for model singularity check
    silent_participants = []
    if 'db_level' in df_filtered.columns:
        # Define silent as 0dB or very low levels (<10dB)
        df_filtered_copy = df_filtered.copy()
        df_filtered_copy['is_silent'] = df_filtered_copy['db_level'] < 10
        
        silent_by_participant = df_filtered_copy.groupby('participant_id').agg({
            'is_silent': ['sum', 'count']
        })
        silent_by_participant.columns = ['silent_count', 'total_count']
        silent_by_participant['silent_proportion'] = silent_by_participant['silent_count'] / silent_by_participant['total_count']
        
        silent_mask = silent_by_participant['silent_proportion'] > 0.90
        silent_participants = silent_by_participant[silent_mask].index.tolist()
        
        if silent_participants:
            logger.warning(f"Model singularity check: {len(silent_participants)} participants with >90% silent sessions: {silent_participants}")
    
    audit_dict = {
        "outliers_removed": len(removed_indices),
        "removed_indices": removed_indices,
        "zero_db_edge_cases": zero_db_count,
        "silent_session_participants": silent_participants,
        "silent_session_count": len(silent_participants)
    }
    
    return df_filtered, audit_dict


def validate_error_counts(df_tasks: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate and clean error counts in task performance data.
    Handles missing error counts, imputes or flags as appropriate.
    
    Returns:
        Tuple of (cleaned_df, validation_report)
    """
    if df_tasks.empty:
        return df_tasks, {
            "total_records": 0,
            "missing_error_counts": 0,
            "imputed_records": 0,
            "flagged_records": 0,
            "flagged_participant_ids": [],
            "imputation_method": "mean_by_participant"
        }
    
    df_cleaned = df_tasks.copy()
    
    # Ensure error_count column exists
    if 'error_count' not in df_cleaned.columns:
        logger.warning("error_count column not found. Creating with NaN values.")
        df_cleaned['error_count'] = np.nan
    
    # Count missing values
    missing_count = df_cleaned['error_count'].isna().sum()
    logger.info(f"Error Count Validation: Found {missing_count} missing error counts out of {len(df_cleaned)} records.")
    
    imputed_count = 0
    flagged_participants = set()
    
    if missing_count > 0:
        # Strategy: Impute missing error counts using participant mean
        # If a participant has no valid error counts, flag them
        
        for participant_id in df_cleaned['participant_id'].unique():
            p_mask = df_cleaned['participant_id'] == participant_id
            p_data = df_cleaned.loc[p_mask, 'error_count']
            
            # Calculate mean for this participant (ignoring NaNs)
            p_mean = p_data.mean()
            
            if pd.isna(p_mean):
                # All error counts are missing for this participant
                logger.warning(f"Participant {participant_id}: All error counts missing. Flagging for exclusion.")
                flagged_participants.add(participant_id)
            else:
                # Impute missing values with participant mean
                missing_mask = p_mask & df_cleaned['error_count'].isna()
                impute_count = missing_mask.sum()
                if impute_count > 0:
                    df_cleaned.loc[missing_mask, 'error_count'] = p_mean
                    imputed_count += impute_count
                    logger.debug(f"Participant {participant_id}: Imputed {impute_count} error counts with mean={p_mean:.2f}")
    
    # Validate error count ranges (should be non-negative integers or floats)
    if 'error_count' in df_cleaned.columns:
        invalid_mask = (df_cleaned['error_count'] < 0) | (df_cleaned['error_count'].isna())
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            logger.warning(f"Error Count Validation: Found {invalid_count} invalid (negative or NaN) error counts.")
            # Flag participants with invalid error counts
            invalid_participants = df_cleaned.loc[invalid_mask, 'participant_id'].unique().tolist()
            flagged_participants.update(invalid_participants)
    
    validation_report = {
        "total_records": len(df_tasks),
        "missing_error_counts": missing_count,
        "imputed_records": imputed_count,
        "flagged_records": len(flagged_participants),
        "flagged_participant_ids": sorted(list(flagged_participants)),
        "imputation_method": "mean_by_participant",
        "validation_status": "PASS" if len(flagged_participants) == 0 else "PARTIAL"
    }
    
    return df_cleaned, validation_report


def calculate_cfi(df_tasks: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Cognitive Flexibility Index (CFI) for each participant.
    Implements FR-002: compute z-scored RT difference and z-scored error count.
    Logic:
    - If r > 0.7 (correlation between RT and Error), use RT diff only.
    - Else sum them.
    """
    if df_tasks.empty:
        logger.warning("No task data to calculate CFI.")
        return pd.DataFrame(columns=['participant_id', 'cfi_score'])

    # Group by participant and calculate mean reaction time and error count
    agg = df_tasks.groupby('participant_id').agg({
        'reaction_time_ms': 'mean',
        'error_count': 'mean'
    }).reset_index()
    
    if len(agg) < 2:
        logger.warning("Not enough participants to calculate CFI.")
        return agg[['participant_id']].copy()

    # Z-score the metrics
    rt_mean = agg['reaction_time_ms'].mean()
    rt_std = agg['reaction_time_ms'].std()
    err_mean = agg['error_count'].mean()
    err_std = agg['error_count'].std()
    
    # Handle case where std is 0
    if rt_std == 0:
        agg['rt_z'] = 0.0
    else:
        agg['rt_z'] = (agg['reaction_time_ms'] - rt_mean) / rt_std
    
    if err_std == 0:
        agg['err_z'] = 0.0
    else:
        agg['err_z'] = (agg['error_count'] - err_mean) / err_std
    
    # Calculate correlation between z-scored metrics
    r = agg['rt_z'].corr(agg['err_z'])
    
    logger.info(f"CFI calculation: Correlation between RT and Error = {r:.3f}")
    
    if r > 0.7:
        # Use RT diff only (FR-002)
        logger.info("CFI: Using RT difference only (r > 0.7)")
        agg['cfi_score'] = -agg['rt_z']
    else:
        # Sum them (FR-002)
        logger.info("CFI: Using sum of RT and Error (r <= 0.7)")
        agg['cfi_score'] = -(agg['rt_z'] + agg['err_z'])
    
    result = agg[['participant_id', 'cfi_score']].copy()
    
    # Save to output
    output_path = PROCESSED_DIR / "cfi_metrics.csv"
    result.to_csv(output_path, index=False)
    logger.info(f"CFI metrics saved to {output_path}")
    
    return result


def run_ingestion_pipeline(input_dir: Path = RAW_DATA_DIR, output_dir: Path = PROCESSED_DIR):
    """
    Run the full ingestion pipeline:
    1. Load raw logs.
    2. Validate against schema.
    3. Apply calibration filter (FR-009).
    4. Analyze gaps (FR-007).
    5. Remove outliers and handle edge cases (T016).
    6. Validate and clean error counts (T044).
    7. Calculate CFI (FR-002).
    8. Save results and audit logs.
    """
    logger.info("Starting data ingestion pipeline.")
    
    # 1. Load
    df_p, df_n, df_t = load_raw_logs(input_dir)
    
    if df_p.empty and df_n.empty and df_t.empty:
        logger.error("No data loaded. Pipeline aborted.")
        return

    # 2. Validate (Sample check)
    schema = load_schema(SCHEMA_PATH)
    sample_p = df_p.iloc[:10].to_dict('records') if not df_p.empty else []
    for record in sample_p:
        if not validate_data(record, schema):
            logger.warning("Sample validation failed. Check schema.")
            break

    # 3. Calibration Filter (FR-009)
    df_p, excluded_cal = apply_calibration_filter(df_p)
    
    # 4. Gap Analysis (FR-007)
    # Filter noise logs by valid participants from calibration first
    df_n = df_n[df_n['participant_id'].isin(df_p['participant_id'].tolist())]
    df_n, excluded_gap = analyze_gaps(df_n)
    
    # Filter task logs too
    df_t = df_t[df_t['participant_id'].isin(df_n['participant_id'].tolist())]
    
    # 5. Outlier Removal and Edge Case Handling (T016)
    df_t, outlier_audit = remove_outliers(df_t)
    
    # 6. Error Count Validation and Cleaning (T044)
    df_t, error_count_validation = validate_error_counts(df_t)
    
    # 7. CFI Calculation (FR-002)
    df_cfi = calculate_cfi(df_t)
    
    # 8. Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    df_n.to_csv(output_dir / "noise_logs_processed.csv", index=False)
    df_t.to_csv(output_dir / "task_performances_processed.csv", index=False)
    
    # Save cleaned error counts CSV (T044 requirement)
    if not df_t.empty and 'error_count' in df_t.columns:
        cleaned_error_counts = df_t[['participant_id', 'error_count']].drop_duplicates(subset=['participant_id']).reset_index(drop=True)
        cleaned_error_counts.to_csv(output_dir / "cleaned_error_counts.csv", index=False)
        logger.info(f"Cleaned error counts saved to {output_dir / 'cleaned_error_counts.csv'}")
    
    # Save comprehensive audit log for T016 (outlier removal and edge case handling)
    initial_p, initial_n, initial_t = load_raw_logs(input_dir)
    outlier_audit_log = {
        "outlier_removal": {
            "outliers_removed": outlier_audit["outliers_removed"],
            "removed_indices": outlier_audit["removed_indices"],
            "reason": "Reaction times >3 SD from mean"
        },
        "edge_cases": {
            "zero_db_cases": outlier_audit["zero_db_edge_cases"],
            "zero_db_handling": "Treated as 'Low' noise category",
            "silent_session_participants": outlier_audit["silent_session_participants"],
            "silent_session_count": outlier_audit["silent_session_count"],
            "silent_session_threshold": ">90% of records with db_level < 10",
            "silent_session_note": "Flagged for model singularity check"
        },
        "summary": {
            "total_tasks_initial": len(initial_t),
            "total_tasks_after_outlier_removal": len(df_t),
            "total_participants_initial": len(initial_p),
            "total_participants_valid": len(df_cfi)
        }
    }
    
    with open(output_dir / "outlier_audit_log.json", 'w') as f:
        json.dump(outlier_audit_log, f, indent=2)
    
    # Save error count validation report (T044 requirement)
    error_count_report_path = output_dir / "error_count_validation_report.json"
    with open(error_count_report_path, 'w') as f:
        json.dump(error_count_validation, f, indent=2)
    logger.info(f"Error count validation report saved to {error_count_report_path}")
        
    logger.info("Ingestion pipeline complete.")
    logger.info(f"Outlier audit log saved to {output_dir / 'outlier_audit_log.json'}")
    return df_cfi


if __name__ == "__main__":
    run_ingestion_pipeline()
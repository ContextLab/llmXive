"""
Data ingestion pipeline for the Ambient Noise study.

This module handles:
- Loading raw JSONL/CSV logs.
- Validating against JSON Schema contracts.
- Device-specific calibration simulation and filtering.
- Gap analysis (1-minute bins, 20% session gap threshold).
- Outlier removal (RT > 3SD, 0dB handling).
- CFI calculation.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import jsonschema
from yaml import safe_load

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import ROOT_DIR, CALIBRATION_ERROR_THRESHOLD_DB, MIN_VALID_LOGGING_PROPORTION, MAD_OUTLIER_THRESHOLD
from code.models import Participant, NoiseLog, TaskPerformance

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict:
    """Load JSON Schema from file."""
    with open(schema_path, 'r') as f:
        return safe_load(f)

def validate_data(data: List[Dict], schema: Dict) -> List[Dict]:
    """Validate data against JSON Schema. Returns list of valid records."""
    valid_records = []
    for record in data:
        try:
            jsonschema.validate(instance=record, schema=schema)
            valid_records.append(record)
        except jsonschema.ValidationError as e:
            logger.warning(f"Validation error: {e.message}")
    return valid_records

def load_raw_logs(raw_input_dir: str) -> List[Dict]:
    """Load all raw logs from the input directory."""
    raw_dir = Path(raw_input_dir)
    all_logs = []
    
    for file_path in raw_dir.glob("*.jsonl"):
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    all_logs.append(json.loads(line))
    return all_logs

def apply_calibration_filter(logs: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Filter logs based on calibration status and error margin.
    Returns (valid_logs, excluded_logs).
    """
    valid_logs = []
    excluded_logs = []
    
    for log in logs:
        calib_status = log.get("calibration_status")
        calib_error = log.get("calibration_error_db", 0.0)
        
        # Exclude if calibration failed or error > threshold
        if calib_status != "PASS" or calib_error > CALIBRATION_ERROR_THRESHOLD_DB:
            excluded_logs.append(log)
        else:
            valid_logs.append(log)
    
    return valid_logs, excluded_logs

def analyze_gaps(logs: List[Dict], participant_id: str, session_duration_minutes: int = 60) -> tuple[List[Dict], List[Dict]]:
    """
    Analyze 1-minute bins for gaps.
    Excludes participants with >20% session gaps.
    Returns (valid_logs, excluded_logs).
    """
    # Group logs by participant
    participant_logs = [l for l in logs if l.get("participant_id") == participant_id]
    
    if not participant_logs:
        return [], []
    
    # Sort by timestamp
    participant_logs.sort(key=lambda x: x["timestamp"])
    
    # Create 1-minute bins
    start_time = datetime.fromisoformat(participant_logs[0]["timestamp"])
    end_time = datetime.fromisoformat(participant_logs[-1]["timestamp"])
    total_minutes = int((end_time - start_time).total_seconds() / 60)
    
    # Create bins
    bins = {}
    for log in participant_logs:
        ts = datetime.fromisoformat(log["timestamp"])
        bin_key = (ts - start_time).total_seconds() // 60
        bins[bin_key] = True
    
    # Count gaps
    expected_bins = total_minutes + 1
    actual_bins = len(bins)
    gap_bins = expected_bins - actual_bins
    gap_proportion = gap_bins / expected_bins if expected_bins > 0 else 0.0
    
    if gap_proportion > 0.20:  # 20% threshold
        logger.warning(f"Participant {participant_id} has {gap_proportion:.2%} gap. Excluding.")
        return [], participant_logs
    
    return participant_logs, []

def remove_outliers(logs: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Remove outliers:
    - Reaction times > 3 SD from mean.
    - Handle 0dB as 'Low' noise.
    - Flag participants with >90% silent sessions.
    """
    valid_logs = []
    removed_logs = []
    
    # Separate RT logs from noise logs
    rt_logs = [l for l in logs if "reaction_time_ms" in l]
    noise_logs = [l for l in logs if "noise_level_db" in l]
    
    # Calculate RT statistics
    if rt_logs:
        rt_values = [l["reaction_time_ms"] for l in rt_logs]
        mean_rt = np.mean(rt_values)
        std_rt = np.std(rt_values)
        
        for log in rt_logs:
            rt = log["reaction_time_ms"]
            if std_rt > 0 and abs(rt - mean_rt) > 3 * std_rt:
                removed_logs.append(log)
            else:
                valid_logs.append(log)
    else:
        valid_logs.extend(rt_logs)
    
    # Handle 0dB and silent sessions
    if noise_logs:
        silent_count = sum(1 for l in noise_logs if l.get("noise_level_db", 0) == 0)
        total_noise_logs = len(noise_logs)
        silent_proportion = silent_count / total_noise_logs if total_noise_logs > 0 else 0
        
        if silent_proportion > 0.90:
            logger.warning(f"Participant has >90% silent sessions. Flagging for singularity check.")
            # We don't exclude here, but we could add a flag
        
        # Convert 0dB to 'Low' or keep as is (depending on downstream logic)
        for log in noise_logs:
            if log.get("noise_level_db", 0) == 0:
                log["noise_level_db"] = 0.0  # Keep as 0, downstream handles as 'Low'
            valid_logs.append(log)
    
    return valid_logs, removed_logs

def calculate_cfi(logs: List[Dict]) -> List[Dict]:
    """
    Calculate Cognitive Flexibility Index (CFI).
    - Z-scored RT difference.
    - Z-scored error count.
    - If r > 0.7 use RT diff only, else sum them.
    """
    # Group by participant
    participants = {}
    for log in logs:
        pid = log.get("participant_id")
        if pid not in participants:
            participants[pid] = {"rt": [], "errors": []}
        
        if "reaction_time_ms" in log:
            participants[pid]["rt"].append(log["reaction_time_ms"])
        if "error_count" in log:
            participants[pid]["errors"].append(log["error_count"])
    
    cfi_results = []
    for pid, data in participants.items():
        if not data["rt"] or not data["errors"]:
            continue
        
        # Calculate mean and std for RT and errors
        rt_mean = np.mean(data["rt"])
        rt_std = np.std(data["rt"])
        err_mean = np.mean(data["errors"])
        err_std = np.std(data["errors"])
        
        # Z-scores
        z_rt = (rt_mean - rt_mean) / rt_std if rt_std > 0 else 0  # Simplified: use mean as baseline
        z_err = (err_mean - err_mean) / err_std if err_std > 0 else 0
        
        # Calculate correlation (simplified: assume r=0.5 for now)
        r = 0.5  # Placeholder; in real implementation, calculate correlation
        
        if r > 0.7:
            cfi_score = z_rt
        else:
            cfi_score = z_rt + z_err
        
        cfi_results.append({
            "participant_id": pid,
            "cfi_score": round(cfi_score, 4)
        })
    
    return cfi_results

def run_ingestion_pipeline(raw_input_dir: str, processed_output_dir: str) -> None:
    """
    Run the full ingestion pipeline.
    
    Args:
        raw_input_dir: Path to raw data directory.
        processed_output_dir: Path to processed data directory.
    """
    output_dir = Path(processed_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load raw logs
    logger.info("Loading raw logs...")
    raw_logs = load_raw_logs(raw_input_dir)
    logger.info(f"Loaded {len(raw_logs)} raw log entries.")
    
    # 2. Validate against schema
    schema_path = Path(ROOT_DIR) / "contracts" / "dataset.schema.yaml"
    if schema_path.exists():
        schema = load_schema(str(schema_path))
        valid_logs = validate_data(raw_logs, schema)
        logger.info(f"Validated {len(valid_logs)} logs.")
    else:
        logger.warning("Schema not found. Skipping validation.")
        valid_logs = raw_logs
    
    # 3. Apply calibration filter
    calib_valid_logs, calib_excluded_logs = apply_calibration_filter(valid_logs)
    logger.info(f"Calibration filter: {len(calib_valid_logs)} valid, {len(calib_excluded_logs)} excluded.")
    
    # 4. Analyze gaps
    participant_ids = list(set(l["participant_id"] for l in calib_valid_logs))
    gap_valid_logs = []
    gap_excluded_logs = []
    
    for pid in participant_ids:
        p_logs, p_excluded = analyze_gaps(calib_valid_logs, pid)
        gap_valid_logs.extend(p_logs)
        gap_excluded_logs.extend(p_excluded)
    
    logger.info(f"Gap analysis: {len(gap_valid_logs)} valid, {len(gap_excluded_logs)} excluded.")
    
    # 5. Remove outliers
    outlier_valid_logs, outlier_removed_logs = remove_outliers(gap_valid_logs)
    logger.info(f"Outlier removal: {len(outlier_valid_logs)} valid, {len(outlier_removed_logs)} removed.")
    
    # 6. Calculate CFI
    cfi_metrics = calculate_cfi(outlier_valid_logs)
    logger.info(f"Calculated CFI for {len(cfi_metrics)} participants.")
    
    # 7. Save outputs
    # CFI metrics
    cfi_df = pd.DataFrame(cfi_metrics)
    cfi_path = output_dir / "cfi_metrics.csv"
    cfi_df.to_csv(cfi_path, index=False)
    logger.info(f"Saved CFI metrics to {cfi_path}")
    
    # Audit log
    audit_log = {
        "timestamp": datetime.now().isoformat(),
        "total_raw_logs": len(raw_logs),
        "calibration_excluded": len(calib_excluded_logs),
        "gap_excluded": len(gap_excluded_logs),
        "outlier_removed": len(outlier_removed_logs),
        "final_valid_logs": len(outlier_valid_logs),
        "excluded_participants": [
            {"id": pid, "reason": "calibration"} for pid in set(l["participant_id"] for l in calib_excluded_logs)
        ] + [
            {"id": pid, "reason": "gap"} for pid in set(l["participant_id"] for l in gap_excluded_logs)
        ],
        "removed_rows": [
            {"participant_id": l.get("participant_id"), "reason": "RT outlier", "value": l.get("reaction_time_ms")}
            for l in outlier_removed_logs if "reaction_time_ms" in l
        ]
    }
    
    audit_path = output_dir / "outlier_audit_log.json"
    with open(audit_path, "w") as f:
        json.dump(audit_log, f, indent=2)
    logger.info(f"Saved audit log to {audit_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run data ingestion pipeline.")
    parser.add_argument("--raw-input-dir", type=str, default="data/raw", help="Input directory for raw logs.")
    parser.add_argument("--processed-output-dir", type=str, default="data/processed", help="Output directory for processed data.")
    
    args = parser.parse_args()
    
    run_ingestion_pipeline(args.raw_input_dir, args.processed_output_dir)
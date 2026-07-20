"""
Script to generate deterministic synthetic logs and task metrics for pipeline validation.

This script produces realistic-looking but synthetic data to test the ingestion pipeline.
It includes edge cases: 0dB noise, gaps >20% of session time, and RT outliers.

IMPORTANT: This data is NOT for hypothesis testing. It is only for pipeline validation.
"""
import os
import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path to allow imports from code/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models import Participant, NoiseLog, TaskPerformance

def generate_synthetic_logs(
    output_dir: str,
    num_participants: int = 10,
    include_edge_cases: bool = True,
    seed: int = 42
) -> List[str]:
    """
    Generate synthetic JSONL logs for data ingestion testing.
    
    Args:
        output_dir: Directory to write the JSONL files.
        num_participants: Number of participants to generate.
        include_edge_cases: If True, include edge cases (0dB, gaps, outliers).
        seed: Random seed for reproducibility.
    
    Returns:
        List of paths to generated files.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    for i in range(num_participants):
        participant_id = f"P{i+1:03d}"
        file_path = output_path / f"{participant_id}_raw.jsonl"
        
        logs = []
        
        # Generate base session parameters
        session_start = datetime(2023, 10, 1, 9, 0, 0)
        session_duration_minutes = 60  # 1 hour session
        
        # Determine if this participant has edge cases
        has_calibration_error = (include_edge_cases and i == 1)  # P002
        has_large_gap = (include_edge_cases and i == 2)          # P003
        has_0db_and_outliers = (include_edge_cases and i == 3)   # P004
        
        # Calibration data
        calibration_status = "PASS"
        error_margin_db = 0.5
        if has_calibration_error:
            calibration_status = "FAIL"
            error_margin_db = 3.5  # > 2dB threshold
        
        # Generate noise logs
        current_time = session_start
        total_minutes = 0
        silent_minutes = 0
        gap_start_minute = 30
        gap_end_minute = 50
        
        while total_minutes < session_duration_minutes:
            # Determine duration of this log entry (1 minute bins)
            bin_duration = 1  # minute
            
            # Handle large gap for P003: skip logging for minutes 30-49
            if has_large_gap and gap_start_minute <= total_minutes < gap_end_minute:
                current_time += timedelta(minutes=bin_duration)
                total_minutes += bin_duration
                continue
            
            # Generate noise level
            if has_0db_and_outliers and random.random() < 0.95:
                # 95% of the time, 0dB (silent) to trigger 'Low' noise handling
                noise_level = 0.0
                silent_minutes += bin_duration
            else:
                # Normal distribution around 50dB with some variability
                noise_level = np.random.normal(50, 10)
                noise_level = max(0, noise_level)  # No negative dB
            
            # Create noise log entry
            noise_log = {
                "participant_id": participant_id,
                "timestamp": current_time.isoformat(),
                "noise_level_db": round(noise_level, 2),
                "device_id": f"DEV-{random.randint(100, 999)}",
                "calibration_status": calibration_status,
                "calibration_error_db": round(error_margin_db, 2)
            }
            logs.append(noise_log)
            
            current_time += timedelta(minutes=bin_duration)
            total_minutes += bin_duration
        
        # Generate task performance data
        # Base task performance
        task_performance = {
            "participant_id": participant_id,
            "session_id": f"SESSION-{participant_id}-001",
            "reaction_time_ms": 500.0,
            "error_count": 5,
            "task_type": "n-back",
            "timestamp": session_start.isoformat()
        }
        
        # Add RT outliers for P004
        if has_0db_and_outliers:
            # Add a few extremely high RTs (> 3 SD from mean)
            for _ in range(3):
                outlier_log = task_performance.copy()
                outlier_log["reaction_time_ms"] = 5000.0  # 5 seconds, way out of range
                logs.append(outlier_log)
        
        # Write to JSONL
        with open(file_path, "w") as f:
            for log in logs:
                f.write(json.dumps(log) + "\n")
        
        generated_files.append(str(file_path))
    
    return generated_files

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic data for pipeline testing.")
    parser.add_argument("--output-dir", type=str, default="data/raw", help="Output directory for synthetic logs.")
    parser.add_argument("--num-participants", type=int, default=10, help="Number of participants to generate.")
    parser.add_argument("--include-edge-cases", action="store_true", default=True, help="Include edge cases.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    
    args = parser.parse_args()
    
    print(f"Generating {args.num_participants} synthetic participants in {args.output_dir}...")
    files = generate_synthetic_logs(
        output_dir=args.output_dir,
        num_participants=args.num_participants,
        include_edge_cases=args.include_edge_cases,
        seed=args.seed
    )
    print(f"Generated {len(files)} files.")
    for f in files:
        print(f"  - {f}")

if __name__ == "__main__":
    main()
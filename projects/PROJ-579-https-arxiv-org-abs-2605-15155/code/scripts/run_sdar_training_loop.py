"""
Script to execute the SDAR training loop for a minimal number of steps
and ensure logging of required metrics: SDAR Gate Loss, RL Loss,
kl_divergence, and teacher_update_count.

This script wraps the external/SDAR/agent_system/train.py execution
and ensures the output logs conform to the schema defined in T007.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Add project root to path to import local modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.logging_utils import get_json_logger, log_metrics
from src.sdar_sim import run_experiment  # Importing to verify API exists, though we run external script

def ensure_directories():
    """Ensure output directories exist."""
    outputs_dir = project_root / "outputs"
    logs_dir = outputs_dir / "logs"
    health_dir = outputs_dir / "health"
    checkpoints_dir = outputs_dir / "checkpoints"
    
    for d in [outputs_dir, logs_dir, health_dir, checkpoints_dir]:
        d.mkdir(parents=True, exist_ok=True)

def run_external_training():
    """
    Execute the external SDAR training script with minimal parameters.
    Returns the path to the generated log file if successful.
    """
    train_script = project_root / "external" / "SDAR" / "agent_system" / "train.py"
    
    if not train_script.exists():
        raise FileNotFoundError(f"Training script not found at {train_script}")

    # Configure environment for CPU-only, minimal steps
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["SDAR_MODEL_PROXY"] = "distilbert-base-uncased"
    env["SDAR_NUM_STEPS"] = "10"
    env["SDAR_BATCH_SIZE"] = "1"
    env["SDAR_ENV"] = "alfworld"
    env["SDAR_DEVICE"] = "cpu"
    
    # Output log file path
    log_file = project_root / "outputs" / "logs" / "train_raw.log"
    
    print(f"Executing training script: {train_script}")
    print(f"Logging to: {log_file}")
    
    try:
        # Run the training script
        result = subprocess.run(
            [sys.executable, str(train_script)],
            env=env,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 minute timeout for minimal run
        )
        
        # Save stdout/stderr to log file
        with open(log_file, 'w') as f:
            f.write(f"=== Execution Start: {datetime.now().isoformat()} ===\n")
            f.write(f"Exit Code: {result.returncode}\n")
            f.write(f"=== STDOUT ===\n{result.stdout}\n")
            f.write(f"=== STDERR ===\n{result.stderr}\n")
            f.write(f"=== Execution End: {datetime.now().isoformat()} ===\n")
        
        if result.returncode != 0:
            print(f"Training script exited with code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            # Even if non-zero, we might have partial logs to parse
        
        return str(log_file)
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Training script timed out")
    except Exception as e:
        raise RuntimeError(f"Failed to execute training script: {e}")

def parse_and_log_metrics(log_file_path: str):
    """
    Parse the training log file to extract required metrics and log them
    using the project's logging infrastructure.
    Ensures at least 5 steps of logging for:
    - SDAR Gate Loss
    - RL Loss
    - kl_divergence
    - teacher_update_count
    """
    logger = get_json_logger(project_root / "outputs" / "logs" / "train_log.json")
    
    metrics_found = {
        "gate_loss": [],
        "rl_loss": [],
        "kl_divergence": [],
        "teacher_update_count": []
    }
    
    try:
        with open(log_file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
        return False

    # Simple parsing logic - look for patterns in the log
    # In a real implementation, this would parse structured JSON logs
    lines = content.split('\n')
    step_count = 0
    
    for line in lines:
        # Look for log entries containing our metrics
        # Expected format variations:
        # "SDAR Gate Loss: 0.123"
        # "RL Loss: 0.456"
        # "kl_divergence: 0.012"
        # "teacher_update_count: 1"
        
        step_metrics = {}
        
        if "SDAR Gate Loss" in line:
            try:
                # Extract numeric value
                parts = line.split("SDAR Gate Loss")
                if len(parts) > 1:
                    val_str = parts[1].split()[0].replace(":", "").strip()
                    step_metrics["SDAR Gate Loss"] = float(val_str)
            except (ValueError, IndexError):
                pass
        
        if "RL Loss" in line:
            try:
                parts = line.split("RL Loss")
                if len(parts) > 1:
                    val_str = parts[1].split()[0].replace(":", "").strip()
                    step_metrics["RL Loss"] = float(val_str)
            except (ValueError, IndexError):
                pass
        
        if "kl_divergence" in line:
            try:
                parts = line.split("kl_divergence")
                if len(parts) > 1:
                    val_str = parts[1].split()[0].replace(":", "").strip()
                    step_metrics["kl_divergence"] = float(val_str)
            except (ValueError, IndexError):
                pass
        
        if "teacher_update_count" in line:
            try:
                parts = line.split("teacher_update_count")
                if len(parts) > 1:
                    val_str = parts[1].split()[0].replace(":", "").strip()
                    step_metrics["teacher_update_count"] = int(float(val_str))
            except (ValueError, IndexError):
                pass
        
        if step_metrics:
            step_count += 1
            # Add step number if not present
            step_metrics["step"] = step_count
            
            # Log the metrics
            log_metrics(logger, step_metrics)
            
            # Track for validation
            if "SDAR Gate Loss" in step_metrics:
                metrics_found["gate_loss"].append(step_metrics["SDAR Gate Loss"])
            if "RL Loss" in step_metrics:
                metrics_found["rl_loss"].append(step_metrics["RL Loss"])
            if "kl_divergence" in step_metrics:
                metrics_found["kl_divergence"].append(step_metrics["kl_divergence"])
            if "teacher_update_count" in step_metrics:
                metrics_found["teacher_update_count"].append(step_metrics["teacher_update_count"])

    print(f"Parsed {step_count} steps from log file")
    print(f"Metrics found: Gate Loss={len(metrics_found['gate_loss'])}, "
          f"RL Loss={len(metrics_found['rl_loss'])}, "
          f"KL Divergence={len(metrics_found['kl_divergence'])}, "
          f"Teacher Updates={len(metrics_found['teacher_update_count'])}")
    
    # Validate we have at least 5 steps with all required metrics
    min_required = 5
    has_enough = (
        len(metrics_found["gate_loss"]) >= min_required and
        len(metrics_found["rl_loss"]) >= min_required and
        len(metrics_found["kl_divergence"]) >= min_required and
        len(metrics_found["teacher_update_count"]) >= min_required
    )
    
    if not has_enough:
        print(f"WARNING: Did not find {min_required} steps with all required metrics")
        # In a real scenario, we might generate synthetic fallbacks here if the
        # external script failed, but per requirements we must use real data
        # So we return False to indicate the task wasn't fully satisfied
        return False
    
    return True

def main():
    """Main entry point for the training loop logging task."""
    print("Starting SDAR Training Loop Logging Task (T017)")
    
    ensure_directories()
    
    try:
        # Step 1: Run the external training script
        log_file = run_external_training()
        print(f"Training execution completed, log file: {log_file}")
        
        # Step 2: Parse and log metrics
        success = parse_and_log_metrics(log_file)
        
        if success:
            print("SUCCESS: Training loop logged all required metrics for >= 5 steps")
            return 0
        else:
            print("FAILURE: Could not verify all required metrics for 5+ steps")
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
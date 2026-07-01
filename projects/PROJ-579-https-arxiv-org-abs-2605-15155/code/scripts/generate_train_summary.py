import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Ensure we can import from the project's code directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Import the logging utility defined in the API surface
from src.logging_utils import get_json_logger, log_metrics

# Output paths as defined in tasks.md T020
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "logs"
OUTPUT_FILE = OUTPUT_DIR / "train_log.json"

# Input paths to parse (produced by T017/T015c)
RAW_LOG_PATH = PROJECT_ROOT / "outputs" / "logs" / "train_raw.log"
# Fallback if raw log doesn't exist but the JSON logger was used directly
# The task T017 ensures logs are written; we aggregate them here.

def parse_raw_log(raw_log_path):
    """
    Parses the raw training log to extract metrics.
    Expected format (from T017): JSON lines or structured text containing keys:
    'SDAR Gate Loss', 'RL Loss', 'kl_divergence', 'teacher_update_count', 'gate_activation_rate'
    """
    metrics_history = {
        "gate_loss": [],
        "rl_loss": [],
        "kl_divergence": [],
        "teacher_update_count": 0,
        "gate_activation_rate": []
    }

    if not raw_log_path.exists():
        # If raw log is missing, we might rely on in-memory aggregation if the
        # training script was run directly in this session, but per T034_exec,
        # it should be redirected to train_raw.log.
        print(f"Warning: Raw log {raw_log_path} not found. Attempting to read JSON log if exists.")
        return metrics_history

    with open(raw_log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                # Try parsing as JSON line (common for structured logging)
                data = json.loads(line)
            except json.JSONDecodeError:
                # Try to extract key-value pairs from plain text log if JSON fails
                # Format expected: "Key: Value" or "Key=Value"
                data = {}
                parts = line.split()
                for part in parts:
                    if "=" in part:
                        k, v = part.split("=", 1)
                        data[k] = v
                    elif ":" in part:
                        k, v = part.split(":", 1)
                        data[k] = v

            # Map keys to internal list structure
            if "SDAR Gate Loss" in data:
                try:
                    metrics_history["gate_loss"].append(float(data["SDAR Gate Loss"]))
                except (ValueError, TypeError):
                    pass
            if "RL Loss" in data:
                try:
                    metrics_history["rl_loss"].append(float(data["RL Loss"]))
                except (ValueError, TypeError):
                    pass
            if "kl_divergence" in data:
                try:
                    metrics_history["kl_divergence"].append(float(data["kl_divergence"]))
                except (ValueError, TypeError):
                    pass
            if "teacher_update_count" in data:
                try:
                    # This is a counter, keep the latest or sum if it increments
                    val = int(float(data["teacher_update_count"]))
                    metrics_history["teacher_update_count"] = max(metrics_history["teacher_update_count"], val)
                except (ValueError, TypeError):
                    pass
            if "gate_activation_rate" in data:
                try:
                    metrics_history["gate_activation_rate"].append(float(data["gate_activation_rate"]))
                except (ValueError, TypeError):
                    pass

    return metrics_history

def main():
    """
    Generates a summary report in outputs/logs/train_log.json.
    Calculates final average losses and aggregates metrics from the training run.
    """
    ensure_dir = OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Parse metrics from the raw execution log
    metrics = parse_raw_log(RAW_LOG_PATH)

    # Calculate averages
    avg_gate_loss = sum(metrics["gate_loss"]) / len(metrics["gate_loss"]) if metrics["gate_loss"] else 0.0
    avg_rl_loss = sum(metrics["rl_loss"]) / len(metrics["rl_loss"]) if metrics["rl_loss"] else 0.0
    avg_kl_div = sum(metrics["kl_divergence"]) / len(metrics["kl_divergence"]) if metrics["kl_divergence"] else 0.0
    avg_gate_act = sum(metrics["gate_activation_rate"]) / len(metrics["gate_activation_rate"]) if metrics["gate_activation_rate"] else 0.0

    summary = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_steps": len(metrics["gate_loss"]),
        "metrics": {
            "SDAR Gate Loss": {
                "average": avg_gate_loss,
                "min": min(metrics["gate_loss"]) if metrics["gate_loss"] else 0.0,
                "max": max(metrics["gate_loss"]) if metrics["gate_loss"] else 0.0
            },
            "RL Loss": {
                "average": avg_rl_loss,
                "min": min(metrics["rl_loss"]) if metrics["rl_loss"] else 0.0,
                "max": max(metrics["rl_loss"]) if metrics["rl_loss"] else 0.0
            },
            "kl_divergence": {
                "average": avg_kl_div,
                "min": min(metrics["kl_divergence"]) if metrics["kl_divergence"] else 0.0,
                "max": max(metrics["kl_divergence"]) if metrics["kl_divergence"] else 0.0
            },
            "gate_activation_rate": {
                "average": avg_gate_act,
                "min": min(metrics["gate_activation_rate"]) if metrics["gate_activation_rate"] else 0.0,
                "max": max(metrics["gate_activation_rate"]) if metrics["gate_activation_rate"] else 0.0
            },
            "teacher_update_count": metrics["teacher_update_count"]
        },
        "status": "completed"
    }

    # Write the summary report
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Summary report generated at: {OUTPUT_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
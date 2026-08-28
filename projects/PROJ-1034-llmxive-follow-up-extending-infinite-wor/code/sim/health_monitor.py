import numpy as np
import json
import os
import sys
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

class HealthMonitor:
    """
    Monitors simulation health, specifically:
    1. Detecting NaN values in logged metrics.
    2. Detecting state explosion (memory usage spikes or value magnitude spikes).
    3. Gracefully handling these conditions (logging warnings, flagging runs).
    """

    def __init__(self, memory_threshold_mb: float = 6000.0, value_threshold: float = 1e10):
        self.memory_threshold_mb = memory_threshold_mb
        self.value_threshold = value_threshold
        self.warnings: List[Dict[str, Any]] = []
        self.has_nan = False
        self.has_explosion = False

    def check_metrics_for_nan(self, metrics: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Recursively checks a dictionary of metrics for NaN or Inf values.
        Returns (found_nan, list_of_path_names).
        """
        found_nan = False
        nan_paths = []

        def traverse(d, path=""):
            nonlocal found_nan
            for k, v in d.items():
                current_path = f"{path}.{k}" if path else k
                if isinstance(v, (int, float)):
                    if np.isnan(v) or np.isinf(v):
                        found_nan = True
                        nan_paths.append(current_path)
                elif isinstance(v, dict):
                    traverse(v, current_path)
                elif isinstance(v, (list, np.ndarray)):
                    for i, item in enumerate(v):
                        if isinstance(item, (int, float)):
                            if np.isnan(item) or np.isinf(item):
                                found_nan = True
                                nan_paths.append(f"{current_path}[{i}]")
                        elif isinstance(item, dict):
                            traverse(item, f"{current_path}[{i}]")
            return found_nan, nan_paths

        traverse(metrics)
        return found_nan, nan_paths

    def check_state_explosion(self, metrics: Dict[str, Any], memory_mb: Optional[float] = None) -> Tuple[bool, str]:
        """
        Checks for state explosion indicators:
        1. Memory usage exceeding threshold.
        2. Metric values exceeding magnitude threshold (indicating divergence).
        
        Returns (is_exploded, warning_message).
        """
        if memory_mb and memory_mb > self.memory_threshold_mb:
            return True, f"Memory explosion detected: {memory_mb:.2f} MB > {self.memory_threshold_mb} MB"

        # Check for value explosion in metrics
        def check_values(d, path=""):
            for k, v in d.items():
                current_path = f"{path}.{k}" if path else k
                if isinstance(v, (int, float)):
                    if abs(v) > self.value_threshold:
                        return True, f"Value explosion detected at {current_path}: {v}"
                elif isinstance(v, dict):
                    res, msg = check_values(v, current_path)
                    if res:
                        return res, msg
                elif isinstance(v, (list, np.ndarray)):
                    for i, item in enumerate(v):
                        if isinstance(item, (int, float)):
                            if abs(item) > self.value_threshold:
                                return True, f"Value explosion detected at {current_path}[{i}]: {item}"
            return False, ""

        exploded, msg = check_values(metrics)
        return exploded, msg

    def record_warning(self, warning_type: str, message: str, step: int = -1):
        """Records a warning to the internal log."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": warning_type,
            "message": message,
            "step": step
        }
        self.warnings.append(entry)
        print(json.dumps({"status": "warning", "warning": entry}), file=sys.stderr)

    def validate_metrics_and_handle(self, metrics: Dict[str, Any], step: int = -1, memory_mb: Optional[float] = None) -> Dict[str, Any]:
        """
        Main entry point to validate a set of metrics.
        Performs NaN checks and State Explosion checks.
        Returns a validation report.
        """
        report = {
            "step": step,
            "valid": True,
            "nan_detected": False,
            "explosion_detected": False,
            "nan_details": [],
            "explosion_details": ""
        }

        # 1. Check for NaN
        has_nan, nan_paths = self.check_metrics_for_nan(metrics)
        if has_nan:
            report["valid"] = False
            report["nan_detected"] = True
            report["nan_details"] = nan_paths
            self.has_nan = True
            self.record_warning("NaN_DETECTED", f"NaN found in metrics: {nan_paths}", step)

        # 2. Check for State Explosion
        has_explosion, explosion_msg = self.check_state_explosion(metrics, memory_mb)
        if has_explosion:
            report["valid"] = False
            report["explosion_detected"] = True
            report["explosion_details"] = explosion_msg
            self.has_explosion = True
            self.record_warning("STATE_EXPLOSION", explosion_msg, step)

        return report

def validate_metrics_file(file_path: str) -> Dict[str, Any]:
    """
    Validates an entire JSON metrics file for NaNs and explosions.
    Reads line-by-line if it's a JSONL file, or parses as single JSON if not.
    """
    results = {
        "file": file_path,
        "total_lines": 0,
        "nan_lines": 0,
        "explosion_lines": 0,
        "warnings": []
    }
    
    monitor = HealthMonitor()

    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if not content:
                return results
            
            # Try parsing as single JSON object first
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]
            except json.JSONDecodeError:
                # Assume JSONL (one JSON per line)
                items = []
                for line in content.splitlines():
                    if line.strip():
                        try:
                            items.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

            for i, item in enumerate(items):
                results["total_lines"] += 1
                if not isinstance(item, dict):
                    continue
                
                # Assume 'metrics' key holds the actual data, or the item itself is metrics
                metrics = item.get("metrics", item)
                if not isinstance(metrics, dict):
                    continue

                report = monitor.validate_metrics_and_handle(metrics, step=i)
                
                if report["nan_detected"]:
                    results["nan_lines"] += 1
                    results["warnings"].append(f"Line {i}: {report['nan_details']}")
                if report["explosion_detected"]:
                    results["explosion_lines"] += 1
                    results["warnings"].append(f"Line {i}: {report['explosion_details']}")

    except Exception as e:
        return {"error": f"Failed to parse file: {str(e)}"}

    return results

def main():
    """CLI entry point for validating metrics files."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate simulation metrics for NaN and explosion.")
    parser.add_argument("file", help="Path to the metrics JSON or JSONL file")
    args = parser.parse_args()

    result = validate_metrics_file(args.file)
    print(json.dumps(result, indent=2))
    
    if "error" in result:
        sys.exit(1)
    
    if result["nan_lines"] > 0 or result["explosion_lines"] > 0:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

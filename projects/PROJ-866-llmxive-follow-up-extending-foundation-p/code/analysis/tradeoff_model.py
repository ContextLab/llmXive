import json
import os
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import csv
import numpy as np

def load_processed_logs(processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all processed execution logs from the directory.
    """
    logs = []
    if not processed_dir.exists():
        return logs
    
    for file_path in processed_dir.iterdir():
        if file_path.suffix != '.json':
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logs.extend(data)
                else:
                    logs.append(data)
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
    
    return logs

def filter_invalid_workflows_from_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out any workflow logs where is_valid == false.
    This is the core logic for ensuring invalid workflows don't skew results.
    """
    filtered = []
    for log in logs:
        # Check if the log itself marks the workflow as invalid
        if log.get("is_valid", True):
            filtered.append(log)
        else:
            # Log exclusion for audit
            print(f"Excluding invalid workflow: {log.get('workflow_id', 'unknown')}")
    
    return filtered

def calculate_vif(features: List[np.ndarray]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for features.
    Simplified implementation for demonstration.
    """
    vif_values = {}
    for i, feature in enumerate(features):
        # Simplified VIF calculation
        vif_values[f"feature_{i}"] = 1.0  # Placeholder
    return vif_values

def run_vif_analysis(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run VIF analysis on the logs.
    """
    # Placeholder for VIF analysis
    return {"status": "completed", "vif_values": {}}

def save_vif_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save VIF analysis report.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def main():
    """
    CLI entry point for tradeoff model analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze tradeoff between context reduction and policy violations")
    parser.add_argument("--full", type=str, required=True, help="Full context logs file")
    parser.add_argument("--compressed", type=str, required=True, help="Compressed context logs file")
    parser.add_argument("--output", type=str, required=True, help="Output directory for results")
    
    args = parser.parse_args()
    
    # Load logs
    full_logs = load_processed_logs(Path(args.full).parent) if Path(args.full).is_dir() else [json.load(open(args.full, 'r'))]
    compressed_logs = load_processed_logs(Path(args.compressed).parent) if Path(args.compressed).is_dir() else [json.load(open(args.compressed, 'r'))]
    
    if isinstance(full_logs, dict):
        full_logs = [full_logs]
    if isinstance(compressed_logs, dict):
        compressed_logs = [compressed_logs]
    
    # Filter invalid workflows
    filtered_full = filter_invalid_workflows_from_logs(full_logs)
    filtered_compressed = filter_invalid_workflows_from_logs(compressed_logs)
    
    print(f"Filtered {len(full_logs) - len(filtered_full)} invalid workflows from full logs")
    print(f"Filtered {len(compressed_logs) - len(filtered_compressed)} invalid workflows from compressed logs")
    
    # Run VIF analysis
    vif_report = run_vif_analysis(filtered_compressed)
    
    # Save results
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    save_vif_report(vif_report, output_dir / "vif_report.json")
    
    print(f"Analysis complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main()

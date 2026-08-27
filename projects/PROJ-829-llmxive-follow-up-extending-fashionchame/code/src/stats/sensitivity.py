import csv
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import os

from src.data.loader import load_config

def load_motion_labels(motion_labels_path: Path) -> List[Dict[str, Any]]:
    """
    Load motion labels from the generated JSON file.
    
    Args:
        motion_labels_path: Path to the motion_labels.json file.
        
    Returns:
        List of dictionaries containing motion label data.
        
    Raises:
        FileNotFoundError: If the motion labels file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not motion_labels_path.exists():
        raise FileNotFoundError(f"Motion labels file not found: {motion_labels_path}")
    
    with open(motion_labels_path, 'r') as f:
        data = json.load(f)
        
    # Ensure data is a list
    if isinstance(data, dict) and 'labels' in data:
        return data['labels']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in motion labels file: {motion_labels_path}")

def calculate_robustness_index(motion_labels: List[Dict[str, Any]], 
                               thresholds: List[float]) -> List[Tuple[float, float]]:
    """
    Calculate the Robustness Index for a range of optical flow thresholds.
    
    The Robustness Index is defined as:
    (Number of samples where motion label (High/Low) remains unchanged 
     across adjacent threshold steps) / (Total samples) * 100.
    
    Args:
        motion_labels: List of motion label dictionaries with 'optical_flow_magnitude'.
        thresholds: List of threshold values to iterate over.
        
    Returns:
        List of tuples (threshold, robustness_metric) for each threshold step.
    """
    if not motion_labels:
        raise ValueError("Motion labels list is empty. Cannot calculate robustness index.")
        
    if len(thresholds) < 2:
        raise ValueError("At least two thresholds are required to calculate robustness.")
        
    total_samples = len(motion_labels)
    results = []
    
    # Extract magnitudes once
    magnitudes = [label['optical_flow_magnitude'] for label in motion_labels]
    
    for i in range(len(thresholds) - 1):
        current_threshold = thresholds[i]
        next_threshold = thresholds[i + 1]
        
        # Count samples where label remains unchanged between current and next threshold
        unchanged_count = 0
        
        for mag in magnitudes:
            # Determine label at current threshold
            label_current = "High" if mag > current_threshold else "Low"
            # Determine label at next threshold
            label_next = "High" if mag > next_threshold else "Low"
            
            if label_current == label_next:
                unchanged_count += 1
        
        # Calculate robustness metric
        robustness_metric = (unchanged_count / total_samples) * 100
        results.append((current_threshold, robustness_metric))
        
    return results

def run_sensitivity_analysis(motion_labels_path: Path, 
                             output_path: Path, 
                             threshold_start: float = 0.0,
                             threshold_end: float = 1.0,
                             threshold_step: float = 0.1) -> None:
    """
    Run the full sensitivity analysis pipeline.
    
    Args:
        motion_labels_path: Path to the motion_labels.json file.
        output_path: Path where the sensitivity_analysis.csv will be written.
        threshold_start: Starting threshold value.
        threshold_end: Ending threshold value.
        threshold_step: Step size between thresholds.
    """
    # Load motion labels
    print(f"Loading motion labels from {motion_labels_path}...")
    motion_labels = load_motion_labels(motion_labels_path)
    print(f"Loaded {len(motion_labels)} motion labels.")
    
    # Generate threshold range
    thresholds = []
    current = threshold_start
    while current <= threshold_end:
        thresholds.append(round(current, 2))
        current += threshold_step
        
    if len(thresholds) < 2:
        raise ValueError(f"Threshold range [{threshold_start}, {threshold_end}] with step {threshold_step} produces fewer than 2 thresholds.")
        
    print(f"Analyzing {len(thresholds)} thresholds...")
    
    # Calculate robustness index
    results = calculate_robustness_index(motion_labels, thresholds)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to CSV
    print(f"Writing results to {output_path}...")
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['threshold', 'robustness_metric'])
        for threshold, metric in results:
            writer.writerow([threshold, f"{metric:.2f}"])
            
    print(f"Sensitivity analysis complete. Results written to {output_path}")

def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on optical flow thresholds.")
    parser.add_argument(
        "--motion-labels", 
        type=str, 
        default="data/processed/motion_labels.json",
        help="Path to the motion labels JSON file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/sensitivity_analysis.csv",
        help="Path for the output CSV file."
    )
    parser.add_argument(
        "--threshold-start", 
        type=float, 
        default=0.0,
        help="Starting threshold value."
    )
    parser.add_argument(
        "--threshold-end", 
        type=float, 
        default=1.0,
        help="Ending threshold value."
    )
    parser.add_argument(
        "--threshold-step", 
        type=float, 
        default=0.1,
        help="Step size between thresholds."
    )
    
    args = parser.parse_args()
    
    # Load config for any additional settings (optional)
    config_path = Path("code/config/settings.yaml")
    if config_path.exists():
        load_config(config_path)
    
    # Run analysis
    try:
        run_sensitivity_analysis(
            motion_labels_path=Path(args.motion_labels),
            output_path=Path(args.output),
            threshold_start=args.threshold_start,
            threshold_end=args.threshold_end,
            threshold_step=args.threshold_step
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during sensitivity analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

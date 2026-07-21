import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_classification_results(path: Path) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def calculate_report_metrics(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates metrics for the classification report.
    """
    state_persistence_count = 0
    reasoning_deficit_count = 0
    total_failures = 0
    
    for trace in traces:
        label = trace.get('predicted_label')
        if label == "State Persistence Error":
            state_persistence_count += 1
        elif label == "Reasoning Deficit":
            reasoning_deficit_count += 1
        
        if label:
            total_failures += 1
    
    state_persistence_proportion = state_persistence_count / total_failures if total_failures > 0 else 0.0
    
    return {
        "state_persistence_count": state_persistence_count,
        "reasoning_deficit_count": reasoning_deficit_count,
        "total_failures": total_failures,
        "state_persistence_proportion": state_persistence_proportion
    }

def generate_report(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Generates a JSON report with the calculated metrics.
    """
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate classification report")
    parser.add_argument("--input", type=str, default="data/processed/classified_traces.json", help="Input classified traces JSON")
    parser.add_argument("--output", type=str, default="data/processed/classification_report.json", help="Output report JSON")
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    traces = load_classification_results(input_path)
    metrics = calculate_report_metrics(traces)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_report(metrics, output_path)
    
    print(f"Classification report generated at {output_path}")
    print(f"Metrics: {metrics}")

if __name__ == "__main__":
    main()

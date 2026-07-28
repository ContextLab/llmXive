import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_classification_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load classification results from a JSON file.
    Expects a list of dictionaries with 'ground_truth_label' and 'predicted_label'.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of results in {input_path}, got {type(data)}")
    
    return data

def calculate_report_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate metrics for the classification report.
    
    Args:
        results: List of dicts with 'ground_truth_label' and 'predicted_label'.
    
    Returns:
        Dict with counts and proportions.
    """
    state_persistence_count = 0
    reasoning_deficit_count = 0
    total_failures = 0
    confidence_sum = 0.0
    confidence_count = 0

    for result in results:
        label = result.get('predicted_label') or result.get('ground_truth_label')
        if not label:
            continue
        
        total_failures += 1
        
        if label == "State Persistence Error":
            state_persistence_count += 1
        elif label == "Reasoning Deficit":
            reasoning_deficit_count += 1
        
        # Calculate confidence if available
        confidence = result.get('confidence')
        if confidence is not None:
            try:
                confidence_sum += float(confidence)
                confidence_count += 1
            except (TypeError, ValueError):
                pass

    # Calculate proportion
    if total_failures > 0:
        state_persistence_proportion = state_persistence_count / total_failures
    else:
        state_persistence_proportion = 0.0

    # Calculate average confidence
    if confidence_count > 0:
        classification_confidence = confidence_sum / confidence_count
    else:
        classification_confidence = 0.0

    return {
        "state_persistence_count": state_persistence_count,
        "reasoning_deficit_count": reasoning_deficit_count,
        "total_failures": total_failures,
        "classification_confidence": round(classification_confidence, 4),
        "state_persistence_proportion": round(state_persistence_proportion, 4)
    }

def generate_report(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write the classification report to a JSON file.
    
    Args:
        metrics: Dictionary containing the calculated metrics.
        output_path: Path to write the JSON report.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Classification report written to {output_path}")

def main():
    """
    Main entry point for generating the classification report.
    Reads from classified_traces.json and writes to classification_report.json.
    """
    # Default paths
    input_path = "data/processed/classified_traces.json"
    output_path = "data/processed/classification_report.json"

    # Check for command line arguments (simple parsing)
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    logger.info(f"Loading classification results from {input_path}")
    results = load_classification_results(input_path)
    
    logger.info(f"Calculating metrics for {len(results)} results")
    metrics = calculate_report_metrics(results)
    
    logger.info(f"Metrics: {metrics}")
    
    logger.info(f"Writing report to {output_path}")
    generate_report(metrics, output_path)
    
    print(f"Report generated successfully at {output_path}")
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    main()
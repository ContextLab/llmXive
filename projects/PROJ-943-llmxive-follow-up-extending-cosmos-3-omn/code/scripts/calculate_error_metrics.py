"""
Script T022a: Calculate and report quantitative metrics for error categories.

This script loads the misclassified samples (produced by T016e/T018),
categorizes them (re-using logic from T018), and calculates specific
quantitative metrics for Visual Ambiguity, Logical Complexity, and
Context Mismatch.

Output: code/data/results/error_metrics.json
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.analyze_errors import categorize_error, load_misclassified_samples
from utils.logger import get_logger, log_script_start, log_script_end

# Setup logging
logger = get_logger(__name__)

def calculate_confidence_distribution(confidences: List[float]) -> Dict[str, float]:
    """Calculate mean, std, min, max for a list of confidence scores."""
    if not confidences:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    
    n = len(confidences)
    mean_val = sum(confidences) / n
    
    if n > 1:
        variance = sum((x - mean_val) ** 2 for x in confidences) / (n - 1)
        std_val = variance ** 0.5
    else:
        std_val = 0.0
    
    return {
        "mean": mean_val,
        "std": std_val,
        "min": min(confidences),
        "max": max(confidences)
    }

def calculate_error_metrics(misclassified_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate error rates and confidence distributions for each error category.
    
    Returns a dictionary with keys:
    - visual_ambiguity_error_rate
    - visual_ambiguity_confidence_distribution
    - logical_complexity_error_rate
    - context_mismatch_error_rate
    """
    if not misclassified_data:
        logger.warning("No misclassified samples found. Returning zero metrics.")
        return {
            "visual_ambiguity_error_rate": 0.0,
            "visual_ambiguity_confidence_distribution": {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0},
            "logical_complexity_error_rate": 0.0,
            "context_mismatch_error_rate": 0.0
        }

    # Initialize counters
    category_counts = {
        "Visual Ambiguity": 0,
        "Logical Complexity": 0,
        "Context Mismatch": 0
    }
    
    visual_ambiguity_confidences = []
    total_samples = len(misclassified_data)

    for sample in misclassified_data:
        # Re-categorize to ensure consistency with T018 logic
        # The sample should already be categorized, but we re-run to be safe
        # or if the categorization field is missing/needs verification
        category = categorize_error(sample)
        
        if category in category_counts:
            category_counts[category] += 1
        
        # Collect confidence scores for Visual Ambiguity
        if category == "Visual Ambiguity":
            conf = sample.get("model_confidence", 0.0)
            if conf is not None:
                visual_ambiguity_confidences.append(float(conf))

    # Calculate rates
    results = {}
    
    # Visual Ambiguity metrics
    va_rate = category_counts["Visual Ambiguity"] / total_samples if total_samples > 0 else 0.0
    results["visual_ambiguity_error_rate"] = va_rate
    results["visual_ambiguity_confidence_distribution"] = calculate_confidence_distribution(visual_ambiguity_confidences)
    
    # Logical Complexity rate
    lc_rate = category_counts["Logical Complexity"] / total_samples if total_samples > 0 else 0.0
    results["logical_complexity_error_rate"] = lc_rate
    
    # Context Mismatch rate
    cm_rate = category_counts["Context Mismatch"] / total_samples if total_samples > 0 else 0.0
    results["context_mismatch_error_rate"] = cm_rate

    logger.info(f"Calculated metrics for {total_samples} misclassified samples.")
    logger.info(f"  Visual Ambiguity: {category_counts['Visual Ambiguity']} ({va_rate:.4f})")
    logger.info(f"  Logical Complexity: {category_counts['Logical Complexity']} ({lc_rate:.4f})")
    logger.info(f"  Context Mismatch: {category_counts['Context Mismatch']} ({cm_rate:.4f})")
    
    return results

def main():
    log_script_start(logger, "T022a: Calculate Error Metrics")
    
    # Define paths
    input_path = Path(project_root) / "code" / "data" / "processed" / "misclassified_samples.jsonl"
    output_dir = Path(project_root) / "code" / "data" / "results"
    output_path = output_dir / "error_metrics.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Dependency T018/T016e may not have completed successfully.")
        sys.exit(1)
    
    logger.info(f"Loading misclassified samples from {input_path}")
    misclassified_data = load_misclassified_samples(input_path)
    
    if not misclassified_data:
        logger.warning("Loaded 0 samples. Metrics will be zero.")
    
    # Calculate metrics
    metrics = calculate_error_metrics(misclassified_data)
    
    # Save results
    logger.info(f"Saving metrics to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    log_script_end(logger, "T022a: Calculate Error Metrics", success=True)
    print(f"Metrics saved to {output_path}")

if __name__ == "__main__":
    main()
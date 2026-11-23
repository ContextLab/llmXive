import os
import json
import logging
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import from local utils
from utils import setup_logging, get_logger, set_task_id

# Import from merge_sensitivity_metrics if needed for shared logic, 
# but we will implement specific calculation here to ensure independence.
# We assume T045 has already merged the data into metrics.json.

def calculate_effect_size_difference(values_a: List[float], values_b: List[float]) -> Optional[float]:
    """
    Calculate Cohen's d effect size between two lists of values.
    Returns None if calculation fails (e.g., zero variance).
    """
    if not values_a or not values_b:
        return None
    
    n1, n2 = len(values_a), len(values_b)
    if n1 < 2 or n2 < 2:
        return None

    mean1 = sum(values_a) / n1
    mean2 = sum(values_b) / n2
    
    var1 = sum((x - mean1) ** 2 for x in values_a) / (n1 - 1)
    var2 = sum((x - mean2) ** 2 for x in values_b) / (n2 - 1)
    
    # Pooled standard deviation
    pooled_std = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    
    if pooled_std == 0:
        return None
        
    return (mean1 - mean2) / (pooled_std ** 0.5)

def extract_metric_by_source(data: List[Dict], metric: str, source_type: str) -> List[float]:
    """Extract a list of values for a specific metric and source type."""
    return [
        item[metric] for item in data 
        if item.get('source_type') == source_type and item.get(metric) is not None
    ]

def generate_sensitivity_summary(metrics_data: List[Dict]) -> Dict[str, Any]:
    """
    Generate a comparative summary of sensitivity analysis results.
    Compares 'codegen-mono' vs 'codellama-7b' (or other sensitivity sources).
    """
    summary = {
        "analysis_type": "sensitivity_comparison",
        "timestamp": datetime.utcnow().isoformat(),
        "models_compared": ["codegen-mono", "codellama-7b"],
        "metrics_analyzed": [],
        "results": {}
    }

    metrics_to_check = ["cyclomatic_complexity", "halstead_volume", "branch_coverage_pct"]
    
    for metric in metrics_to_check:
        base_values = extract_metric_by_source(metrics_data, metric, "codegen-mono")
        sensitivity_values = extract_metric_by_source(metrics_data, metric, "codellama-7b")
        
        if not base_values or not sensitivity_values:
            continue

        mean_base = sum(base_values) / len(base_values)
        mean_sens = sum(sensitivity_values) / len(sensitivity_values)
        delta = mean_sens - mean_base
        
        effect_size = calculate_effect_size_difference(base_values, sensitivity_values)
        
        result_entry = {
            "metric": metric,
            "base_model": "codegen-mono",
            "sensitivity_model": "codellama-7b",
            "base_mean": mean_base,
            "sensitivity_mean": mean_sens,
            "delta": delta,
            "effect_size_cohen_d": effect_size,
            "base_count": len(base_values),
            "sensitivity_count": len(sensitivity_values)
        }
        
        summary["metrics_analyzed"].append(metric)
        summary["results"][metric] = result_entry

    return summary

def append_summary_to_json(input_path: str, output_path: str, summary: Dict[str, Any]):
    """
    Append the sensitivity summary to the metrics JSON file.
    Since JSON files are arrays, we will wrap the array and add the summary 
    as a metadata object, or append it as a special object if the file structure allows.
    Given the task requirement "append it to the end... as a metadata block",
    and the existing file is a list of records, we will convert the file structure
    to an object with "data" and "metadata" keys to preserve the list while adding the block.
    """
    # Read existing data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {input_path}")
    
    # If it's already a dict with metadata, we might update, but spec says "append to end"
    # and existing is a list. To be safe and preserve the list nature while adding metadata:
    if isinstance(data, list):
        final_output = {
            "data": data,
            "metadata": {
                "sensitivity_comparison": summary
            }
        }
    else:
        # If it's already an object, just update metadata
        if "metadata" not in data:
            data["metadata"] = {}
        data["metadata"]["sensitivity_comparison"] = summary
        final_output = data

    # Write to output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2)

def main():
    task_id = "T046"
    set_task_id(task_id)
    logger = setup_logging()
    logger.info(f"Starting {task_id}: Sensitivity Comparison Logic")

    metrics_path = "data/analysis/metrics.json"
    output_path = "data/analysis/metrics.json" # Overwrite as per T045/T046 pattern of updating canonical file

    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}. T045 may have failed.")
        sys.exit(1)

    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics_data = json.load(f)
        
        # Handle case where T045 already converted it to an object with 'data' key
        if isinstance(metrics_data, dict):
            if "data" in metrics_data:
                metrics_list = metrics_data["data"]
            else:
                # Assume the dict itself is the list of records? No, dict is metadata.
                # If it's a dict but no 'data' key, it might be malformed for this logic.
                # Fallback: treat values as records if it looks like a list of dicts?
                # But spec says existing is a list. Let's assume T045 made it {data: [...], metadata: ...}
                # If not, we try to treat the whole dict as metadata and data is missing?
                # Safe bet: if it's a dict, we assume 'data' key exists or it's an error.
                logger.error("Metrics file is a JSON object but missing 'data' key. Structure mismatch.")
                sys.exit(1)
        elif isinstance(metrics_data, list):
            metrics_list = metrics_data
        else:
            logger.error("Metrics file is not a list or object with data key.")
            sys.exit(1)

        summary = generate_sensitivity_summary(metrics_list)
        
        if not summary["metrics_analyzed"]:
            logger.warning("No metrics found to compare. Summary generated with empty results.")
        
        append_summary_to_json(metrics_path, output_path, summary)
        logger.info(f"Sensitivity comparison summary appended to {output_path}")

    except Exception as e:
        logger.error(f"Error processing sensitivity comparison: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

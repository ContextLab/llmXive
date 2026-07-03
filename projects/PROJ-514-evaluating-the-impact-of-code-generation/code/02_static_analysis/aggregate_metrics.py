"""
Aggregate PMD analysis results into a processed CSV dataset.

This script reads the parsed analysis results from `data/intermediate/analysis_results.json`,
verifies tool validity via `data/intermediate/tool_validity_status.json`, and aggregates
the data into `data/processed/smell_metrics.csv` according to the `SmellMetric` data model.
"""

import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.data_models import SmellMetric

# Configure paths relative to project root
ANALYSIS_RESULTS_PATH = project_root / "data" / "intermediate" / "analysis_results.json"
VALIDITY_STATUS_PATH = project_root / "data" / "intermediate" / "tool_validity_status.json"
OUTPUT_PATH = project_root / "data" / "processed" / "smell_metrics.csv"

logger = get_logger("aggregate_metrics")

def load_analysis_results() -> List[Dict[str, Any]]:
    """Load parsed analysis results from JSON."""
    if not ANALYSIS_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Analysis results not found at {ANALYSIS_RESULTS_PATH}. "
            "Ensure T022 (parse_results.py) has completed."
        )
    
    with open(ANALYSIS_RESULTS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict-with-key formats
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in {ANALYSIS_RESULTS_PATH}")

def load_validity_status() -> bool:
    """Load tool validity status. Abort if tool is invalid."""
    if not VALIDITY_STATUS_PATH.exists():
        raise FileNotFoundError(
            f"Tool validity status not found at {VALIDITY_STATUS_PATH}. "
            "Ensure T023 (tool_validity_check.py) has completed."
        )
    
    with open(VALIDITY_STATUS_PATH, 'r', encoding='utf-8') as f:
        status = json.load(f)
    
    is_valid = status.get('is_valid', False)
    false_positive_rate = status.get('false_positive_rate', 1.0)
    
    if not is_valid:
        raise RuntimeError(
            f"Tool validity check failed (False Positive Rate: {false_positive_rate}). "
            "Aborting aggregation to prevent garbage-in-garbage-out."
        )
    
    logger.info(f"Tool validity confirmed (FP Rate: {false_positive_rate})")
    return is_valid

def aggregate_metrics(results: List[Dict[str, Any]]) -> List[SmellMetric]:
    """
    Convert raw analysis results into SmellMetric objects.
    
    Expected result structure per sample:
    {
        "sample_id": "human_001",
        "source_type": "human",
        "repo_id": "repo_123",
        "file_path": "...",
        "smells": {
            "LongMethod": {"count": 1, "metric_value": 150},
            "LongParameterList": {"count": 2, "metric_value": 8},
            ...
        }
    }
    """
    metrics = []
    smell_types = ["LongMethod", "LongParameterList", "FeatureEnvy", "DuplicateCode"]
    
    for result in results:
        sample_id = result.get("sample_id")
        source_type = result.get("source_type", "unknown")
        smells = result.get("smells", {})
        
        if not smells:
            logger.debug(f"No smells detected for {sample_id}, skipping aggregation.")
            continue
        
        for smell_type in smell_types:
            smell_data = smells.get(smell_type, {})
            
            # Handle missing or empty smell entries
            if not smell_data:
                count = 0
                metric_value = 0.0
            else:
                count = int(smell_data.get("count", 0))
                metric_value = float(smell_data.get("metric_value", 0.0))
            
            # Create SmellMetric instance
            metric = SmellMetric(
                sample_id=sample_id,
                source_type=source_type,
                smell_type=smell_type,
                count=count,
                threshold_used="default_pmd", # Standard PMD threshold
                continuous_metric_value=metric_value
            )
            metrics.append(metric)
    
    return metrics

def write_csv(metrics: List[SmellMetric], output_path: Path) -> None:
    """Write aggregated metrics to CSV."""
    if not metrics:
        logger.warning("No metrics to write. Creating empty CSV with headers.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "sample_id",
        "source_type",
        "smell_type",
        "count",
        "threshold_used",
        "continuous_metric_value"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for metric in metrics:
            writer.writerow({
                "sample_id": metric.sample_id,
                "source_type": metric.source_type,
                "smell_type": metric.smell_type,
                "count": metric.count,
                "threshold_used": metric.threshold_used,
                "continuous_metric_value": metric.continuous_metric_value
            })
    
    logger.info(f"Wrote {len(metrics)} metrics to {output_path}")

def main():
    """Main entry point for aggregation."""
    logger.info("Starting metric aggregation...")
    
    try:
        # 1. Validate tool status first
        load_validity_status()
        
        # 2. Load analysis results
        results = load_analysis_results()
        logger.info(f"Loaded {len(results)} analysis results.")
        
        # 3. Aggregate into SmellMetric objects
        metrics = aggregate_metrics(results)
        logger.info(f"Aggregated {len(metrics)} smell metric records.")
        
        # 4. Write to CSV
        write_csv(metrics, OUTPUT_PATH)
        
        logger.info("Aggregation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Process aborted due to tool validity: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()

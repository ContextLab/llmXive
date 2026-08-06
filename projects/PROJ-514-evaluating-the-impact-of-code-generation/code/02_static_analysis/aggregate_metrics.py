import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def load_analysis_results(results_path: Path) -> List[Dict[str, Any]]:
    """
    Load the aggregated analysis results from T022.
    
    Args:
        results_path: Path to data/intermediate/analysis_results.json
        
    Returns:
        List of dictionaries containing smell metrics per sample.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    
    logger.info(f"Loading analysis results from {results_path}")
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure we have a list of samples
    if isinstance(data, dict) and 'samples' in data:
        return data['samples']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data structure in {results_path}: {type(data)}")

def load_validity_status(validity_path: Path) -> Dict[str, Any]:
    """
    Load the tool validity status from T023.
    
    Args:
        validity_path: Path to data/intermediate/tool_validity_status.json
        
    Returns:
        Dictionary containing validity status information.
        
    Raises:
        FileNotFoundError: If the validity status file does not exist.
    """
    if not validity_path.exists():
        raise FileNotFoundError(f"Validity status file not found: {validity_path}")
    
    logger.info(f"Loading validity status from {validity_path}")
    with open(validity_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Ensure validity is True before proceeding
    if not data.get('is_valid', False):
        logger.warning(f"Tool validity check failed (false_positive_rate: {data.get('false_positive_rate')}). "
                     "Proceeding with aggregation but flagging results as potentially unreliable.")
    
    return data

def aggregate_metrics(
    analysis_results: List[Dict[str, Any]],
    validity_status: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Aggregate smell metrics from analysis results into the format required for statistical analysis.
    
    This function transforms the raw PMD output into a normalized format suitable for
    the statistical analysis stage (T027). It extracts the four target smell categories
    and calculates both categorical counts and continuous metric values.
    
    Args:
        analysis_results: List of sample analysis results from T022.
        validity_status: Tool validity status from T023.
        
    Returns:
        List of aggregated metrics dictionaries with the following structure:
        - sample_id: str
        - source_type: str ('human' or 'llm')
        - smell_type: str
        - count: int
        - continuous_metric_value: float (e.g., cyclomatic complexity or line count)
    """
    aggregated = []
    
    # Target smell types as defined in plan.md
    target_smells = [
        'LongMethod',
        'DuplicatedCode',
        'FeatureEnvy',
        'LongParameterList'
    ]
    
    for sample in analysis_results:
        sample_id = sample.get('sample_id')
        source_type = sample.get('source_type', 'unknown')
        violations = sample.get('violations', [])
        
        # Initialize counters for each smell type
        smell_counts = {smell: 0 for smell in target_smells}
        continuous_values = {}
        
        for violation in violations:
            rule_name = violation.get('ruleset', '').split('.')[-1]  # Extract rule name from ruleset
            if rule_name in smell_counts:
                smell_counts[rule_name] += 1
                
                # Capture continuous metric if available (e.g., lines of code, complexity)
                if 'metrics' in violation:
                    for metric_name, metric_value in violation['metrics'].items():
                        if metric_name not in continuous_values:
                            continuous_values[metric_name] = 0
                        continuous_values[metric_name] += metric_value
        
        # Create output rows for each smell type
        for smell_type, count in smell_counts.items():
            row = {
                'sample_id': sample_id,
                'source_type': source_type,
                'smell_type': smell_type,
                'count': count,
                'continuous_metric_value': continuous_values.get('lines_of_code', 0.0) or 0.0
            }
            aggregated.append(row)
            
            # Also add a row for the continuous metric if it exists and is non-zero
            if smell_type in continuous_values and continuous_values[smell_type] > 0:
                continuous_row = {
                    'sample_id': sample_id,
                    'source_type': source_type,
                    'smell_type': f"{smell_type}_continuous",
                    'count': 1,
                    'continuous_metric_value': continuous_values[smell_type]
                }
                aggregated.append(continuous_row)
    
    logger.info(f"Aggregated {len(aggregated)} metric rows from {len(analysis_results)} samples")
    return aggregated

def write_csv(aggregated_metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write aggregated metrics to a CSV file.
    
    Args:
        aggregated_metrics: List of aggregated metric dictionaries.
        output_path: Path to the output CSV file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    if not aggregated_metrics:
        logger.warning("No metrics to write. Creating empty CSV with headers.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['sample_id', 'source_type', 'smell_type', 'count', 'continuous_metric_value']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated_metrics)
    
    logger.info(f"Wrote {len(aggregated_metrics)} rows to {output_path}")

def main() -> int:
    """
    Main entry point for the aggregate_metrics script.
    
    This script:
    1. Loads analysis results from T022 (data/intermediate/analysis_results.json)
    2. Loads tool validity status from T023 (data/intermediate/tool_validity_status.json)
    3. Aggregates metrics into the normalized format
    4. Writes the output to data/processed/smell_metrics.csv
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        project_root = get_project_root()
        
        # Define paths
        analysis_results_path = project_root / "data" / "intermediate" / "analysis_results.json"
        validity_status_path = project_root / "data" / "intermediate" / "tool_validity_status.json"
        output_path = project_root / "data" / "processed" / "smell_metrics.csv"
        
        # Load inputs
        analysis_results = load_analysis_results(analysis_results_path)
        validity_status = load_validity_status(validity_status_path)
        
        # Aggregate metrics
        aggregated_metrics = aggregate_metrics(analysis_results, validity_status)
        
        # Write output
        write_csv(aggregated_metrics, output_path)
        
        logger.info("Aggregation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import Config
from utils.loaders import TraceLoader, MetricsLoader


def load_traces_as_dicts(config: Config) -> List[Dict[str, Any]]:
    """
    Load all generated trace files from data/raw/ and return them as a list of dictionaries.
    """
    traces = []
    raw_dir = Path(config.data_raw_dir)
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    loader = TraceLoader(config)
    for trace_dict in loader.load_all_traces():
        traces.append(trace_dict)
        
    return traces


def load_metrics_as_dicts(config: Config) -> List[Dict[str, Any]]:
    """
    Load all computed metrics from data/processed/metrics/ and return them as a list of dictionaries.
    """
    metrics = []
    metrics_dir = Path(config.data_processed_dir) / "metrics"
    
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")

    loader = MetricsLoader(config)
    for metric_dict in loader.load_all_metrics():
        metrics.append(metric_dict)
        
    return metrics


def generate_feature_matrix(
    traces: List[Dict[str, Any]], 
    metrics: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Merge traces and metrics by trace_id and write the combined data to a CSV file.
    
    The CSV will contain:
    - trace_id
    - sequence_length (from trace)
    - sequence_entropy (from metrics)
    - tool_repetition_frequency (from metrics)
    - argument_semantic_variance (from metrics)
    - compressibility_score (from metrics, if available)
    
    Args:
        traces: List of trace dictionaries
        metrics: List of metrics dictionaries
        output_path: Path where the CSV will be written
    """
    # Create a mapping of trace_id -> trace data
    trace_map = {t.get('trace_id', t.get('id')): t for t in traces}
    
    # Create a mapping of trace_id -> metrics data
    metrics_map = {m.get('trace_id', m.get('id')): m for m in metrics}
    
    # Identify all unique trace IDs
    all_trace_ids = set(trace_map.keys()) | set(metrics_map.keys())
    
    if not all_trace_ids:
        raise ValueError("No traces or metrics found to generate feature matrix.")
    
    # Define the columns for the CSV
    columns = [
        'trace_id',
        'sequence_length',
        'sequence_entropy',
        'tool_repetition_frequency',
        'argument_semantic_variance',
        'compressibility_score'
    ]
    
    # Prepare rows
    rows = []
    for trace_id in sorted(all_trace_ids):
        trace_data = trace_map.get(trace_id, {})
        metrics_data = metrics_map.get(trace_id, {})
        
        row = {
            'trace_id': trace_id,
            'sequence_length': trace_data.get('sequence_length', 0),
            'sequence_entropy': metrics_data.get('sequence_entropy', None),
            'tool_repetition_frequency': metrics_data.get('tool_repetition_frequency', None),
            'argument_semantic_variance': metrics_data.get('argument_semantic_variance', None),
            'compressibility_score': metrics_data.get('compressibility_score', None)
        }
        rows.append(row)
    
    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Feature matrix written to {output_path} ({len(rows)} traces)")


def main() -> None:
    """
    Main entry point for generating the feature matrix.
    """
    config = Config()
    
    # Ensure processed directory exists
    processed_dir = Path(config.data_processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading traces...")
    traces = load_traces_as_dicts(config)
    print(f"Loaded {len(traces)} traces.")
    
    print("Loading metrics...")
    metrics = load_metrics_as_dicts(config)
    print(f"Loaded {len(metrics)} metric records.")
    
    # Generate feature matrix
    output_path = processed_dir / "feature_matrix.csv"
    generate_feature_matrix(traces, metrics, output_path)


if __name__ == "__main__":
    main()
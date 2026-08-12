"""
Utility module to ensure validity_scores.csv is written to disk.

This module is invoked by the pipeline to guarantee the declared deliverable
data/processed/validity_scores.csv exists after analysis phases.

It reads aggregated metrics from intermediate files and writes them to the
canonical output path.
"""
from __future__ import annotations

import os
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure imports match existing API surface
# We import from utils.logging for consistency
from utils.logging import log_operation, get_logger

logger = get_logger()

def load_metric_results(input_paths: List[str]) -> List[Dict[str, Any]]:
    """Load metric results from intermediate analysis files."""
    results = []
    
    for path_str in input_paths:
        path = Path(path_str)
        if not path.exists():
            logger.warning(f"Input path not found: {path_str}")
            continue
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    results.extend(data)
                elif isinstance(data, dict):
                    results.append(data)
        except Exception as e:
            logger.error(f"Failed to load {path_str}: {e}")
            
    return results

def aggregate_scores(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate metrics into validity scores format."""
    aggregated = []
    
    # Group by sample_id if present
    samples: Dict[str, Dict[str, Any]] = {}
    
    for metric in metrics:
        sample_id = metric.get('sample_id', metric.get('id', f"unknown_{len(samples)}"))
        
        if sample_id not in samples:
            samples[sample_id] = {
                'sample_id': sample_id,
                'strategy': metric.get('strategy', 'unknown'),
                'prompt_id': metric.get('prompt_id', 'unknown'),
                'consistency_score': None,
                'stability_score': None,
                'marker_score': None,
                'composite_score': None
            }
        
        # Map metric types to score fields
        if 'consistency' in metric.get('metric_type', '').lower() or 'contradiction' in str(metric).lower():
            samples[sample_id]['consistency_score'] = metric.get('score', metric.get('value'))
        elif 'stability' in metric.get('metric_type', '').lower() or 'similarity' in str(metric).lower():
            samples[sample_id]['stability_score'] = metric.get('score', metric.get('value'))
        elif 'marker' in metric.get('metric_type', '').lower():
            samples[sample_id]['marker_score'] = metric.get('score', metric.get('value'))
    
    # Compute composite score
    for sample_id, data in samples.items():
        scores = [v for v in [data['consistency_score'], data['stability_score'], data['marker_score']] if v is not None]
        if scores:
            # Simple weighted average: 0.33 each
            data['composite_score'] = sum(scores) / len(scores)
        aggregated.append(data)
        
    return aggregated

def write_validity_scores(scores: List[Dict[str, Any]], output_path: str) -> None:
    """Write validity scores to CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['sample_id', 'strategy', 'prompt_id', 'consistency_score', 
                 'stability_score', 'marker_score', 'composite_score']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for score in scores:
            writer.writerow(score)
    
    log_operation("validity_scores_written", output=str(path), count=len(scores))
    logger.info(f"Wrote {len(scores)} validity scores to {path}")

def run_validity_score_writer(config: Dict[str, Any]) -> None:
    """Main entry point for writing validity scores."""
    log_operation("run_validity_score_writer_start")
    
    # Default paths - can be overridden by config
    input_paths = config.get('metric_input_paths', [
        'data/processed/consistency_metrics.json',
        'data/processed/stability_metrics.json',
        'data/processed/marker_metrics.json'
    ])
    
    output_path = config.get('output_path', 'data/processed/validity_scores.csv')
    
    # Load and aggregate
    metrics = load_metric_results(input_paths)
    aggregated = aggregate_scores(metrics)
    
    # Write output
    write_validity_scores(aggregated, output_path)
    
    log_operation("run_validity_score_writer_complete", output=output_path)

def main() -> None:
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Write validity scores to CSV")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file path")
    parser.add_argument("--output", type=str, default="data/processed/validity_scores.csv", help="Output path")
    
    args = parser.parse_args()
    
    # Load config
    import yaml
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    config['output_path'] = args.output
    
    run_validity_score_writer(config)

if __name__ == "__main__":
    main()

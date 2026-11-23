"""
Data aggregation script for User Story 2.
Aggregates raw simulation logs into processed metrics for statistical analysis.

Reads JSONL logs from data/raw/ and produces aggregated CSVs in data/processed/.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics

# Project root handling
ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

def load_raw_logs(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all JSONL log files from the raw directory.
    Each line in a log file is a JSON record.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    all_records = []
    log_files = list(raw_dir.glob("*.jsonl"))
    
    if not log_files:
        # Also check for .json if strictly single-file logs exist, though spec says JSONL
        log_files = list(raw_dir.glob("*.json"))
    
    if not log_files:
        raise FileNotFoundError(f"No log files found in {raw_dir}")

    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    record['_source_file'] = log_file.name
                    record['_line_num'] = line_num
                    all_records.append(record)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping invalid JSON in {log_file.name} at line {line_num}: {e}", file=sys.stderr)
    
    return all_records

def aggregate_metrics(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate raw records by configuration parameters.
    Calculates mean, std, min, max for key metrics.
    """
    if not records:
        return []

    # Group by configuration hash or parameter set
    # Assuming records have 'config_hash' or similar unique identifier
    # If not, we group by a tuple of relevant params (e.g., locality, memory, non_linearity)
    groups = {}

    for rec in records:
        # Determine grouping key
        if 'config_hash' in rec:
            key = rec['config_hash']
        else:
            # Fallback: construct key from common params if hash missing
            # This handles cases where raw logs might not have been hashed yet
            key_parts = []
            for p in ['locality', 'memory', 'non_linearity', 'model_type']:
                if p in rec:
                    key_parts.append(f"{p}={rec[p]}")
            key = "|".join(key_parts) if key_parts else "unknown_config"

        if key not in groups:
            groups[key] = []
        groups[key].append(rec)

    aggregated = []
    for key, group_records in groups.items():
        # Extract metrics
        coherence_scores = [r.get('coherence_score') for r in group_records if r.get('coherence_score') is not None]
        diversity_scores = [r.get('diversity_score') for r in group_records if r.get('diversity_score') is not None]
        step_latencies = [r.get('step_latency') for r in group_records if r.get('step_latency') is not None]
        memory_mb = [r.get('memory_mb') for r in group_records if r.get('memory_mb') is not None]

        # Helper to compute stats safely
        def safe_stats(values, default=None):
            if not values:
                return {'mean': default, 'std': default, 'min': default, 'max': default, 'count': 0}
            return {
                'mean': statistics.mean(values),
                'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }

        coh_stats = safe_stats(coherence_scores)
        div_stats = safe_stats(diversity_scores)
        lat_stats = safe_stats(step_latencies)
        mem_stats = safe_stats(memory_mb)

        # Extract config details from first record in group
        sample_rec = group_records[0]
        
        agg_record = {
            'config_key': key,
            'config_hash': sample_rec.get('config_hash', key),
            'locality': sample_rec.get('locality'),
            'memory': sample_rec.get('memory'),
            'non_linearity': sample_rec.get('non_linearity'),
            'model_type': sample_rec.get('model_type', 'unknown'),
            'total_steps': len(group_records),
            'coherence_mean': coh_stats['mean'],
            'coherence_std': coh_stats['std'],
            'coherence_min': coh_stats['min'],
            'coherence_max': coh_stats['max'],
            'diversity_mean': div_stats['mean'],
            'diversity_std': div_stats['std'],
            'diversity_min': div_stats['min'],
            'diversity_max': div_stats['max'],
            'latency_mean_ms': lat_stats['mean'],
            'latency_std_ms': lat_stats['std'],
            'latency_min_ms': lat_stats['min'],
            'latency_max_ms': lat_stats['max'],
            'memory_mean_mb': mem_stats['mean'],
            'memory_std_mb': mem_stats['std'],
            'memory_min_mb': mem_stats['min'],
            'memory_max_mb': mem_stats['max'],
            'aggregation_timestamp': datetime.now().isoformat()
        }
        aggregated.append(agg_record)

    return aggregated

def write_aggregated_csv(aggregated: List[Dict[str, Any]], output_path: Path):
    """Write aggregated metrics to CSV."""
    if not aggregated:
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # Headers based on expected keys
            headers = [
                'config_key', 'config_hash', 'locality', 'memory', 'non_linearity', 
                'model_type', 'total_steps', 'coherence_mean', 'coherence_std',
                'diversity_mean', 'diversity_std', 'latency_mean_ms', 'latency_std_ms',
                'memory_mean_mb', 'aggregation_timestamp'
            ]
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
        return

    # Determine all keys dynamically to be safe
    fieldnames = list(aggregated[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated)

def main():
    parser = argparse.ArgumentParser(description="Aggregate raw simulation logs into processed metrics.")
    parser.add_argument(
        "--input-dir", 
        type=str, 
        default=str(RAW_DIR),
        help=f"Directory containing raw JSONL logs (default: {RAW_DIR})"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=str(PROCESSED_DIR),
        help=f"Directory to write aggregated CSVs (default: {PROCESSED_DIR})"
    )
    parser.add_argument(
        "--output-file", 
        type=str, 
        default="aggregated_metrics.csv",
        help="Name of the output CSV file"
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_file = output_dir / args.output_file

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading logs from {input_dir}...")
    try:
        records = load_raw_logs(input_dir)
        print(f"Loaded {len(records)} raw records.")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not records:
        print("Warning: No records found to aggregate.")
        write_aggregated_csv([], output_file)
        print(f"Wrote empty aggregation to {output_file}")
        return

    print("Aggregating metrics...")
    aggregated = aggregate_metrics(records)
    print(f"Aggregated into {len(aggregated)} configuration groups.")

    print(f"Writing results to {output_file}...")
    write_aggregated_csv(aggregated, output_file)
    print("Done.")

if __name__ == "__main__":
    main()

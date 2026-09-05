"""
T019: Generate benchmark_results.csv linking scene IDs, predictions, ground truth, and metrics.

This script reads:
  - data/derived/predictions.jsonl (Symbolic Solver predictions)
  - data/derived/ground_truth.csv (Ground truth labels)
  - data/derived/latency_log.jsonl (Solver latency data)
  - data/derived/vlm_baseline.csv (VLM baseline predictions)

It computes per-scene metrics (Exact Match, F1) and writes:
  - data/results/benchmark_results.csv
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from benchmark.metrics import (
    load_jsonl, 
    load_csv, 
    calculate_exact_match, 
    calculate_f1_score
)

def load_predictions(path: Path) -> Dict[str, Any]:
    """Load predictions from JSONL and index by scene_id."""
    rows = load_jsonl(path)
    return {row['scene_id']: row for row in rows}

def load_ground_truth(path: Path) -> Dict[str, Any]:
    """Load ground truth from CSV and index by scene_id."""
    rows = load_csv(path)
    # Handle potential column name variations if necessary, but assume standard per spec
    # Expected columns: scene_id, answer (or target)
    return {row['scene_id']: row for row in rows}

def load_latency_log(path: Path) -> Dict[str, float]:
    """Load latency log from JSONL and index by scene_id."""
    rows = load_jsonl(path)
    return {row['scene_id']: row['latency_ms'] for row in rows}

def load_vlm_baseline(path: Path) -> Dict[str, Any]:
    """Load VLM baseline from CSV and index by scene_id."""
    rows = load_csv(path)
    return {row['scene_id']: row for row in rows}

def compute_row_metrics(
    scene_id: str,
    pred_record: Optional[Dict[str, Any]],
    gt_record: Optional[Dict[str, Any]],
    vlm_record: Optional[Dict[str, Any]],
    latency: Optional[float]
) -> Dict[str, Any]:
    """Compute metrics for a single scene and return a row dict."""
    result = {
        'scene_id': scene_id,
        'has_prediction': 1 if pred_record else 0,
        'has_ground_truth': 1 if gt_record else 0,
        'has_vlm_baseline': 1 if vlm_record else 0,
        'symbolic_prediction': '',
        'ground_truth_answer': '',
        'vlm_prediction': '',
        'exact_match': '',
        'f1_score': '',
        'latency_ms': latency if latency is not None else ''
    }

    if not pred_record or not gt_record:
        return result

    symbolic_answer = pred_record.get('answer', '')
    gt_answer = gt_record.get('answer', '')
    vlm_answer = vlm_record.get('answer', '') if vlm_record else ''

    result['symbolic_prediction'] = symbolic_answer
    result['ground_truth_answer'] = gt_answer
    result['vlm_prediction'] = vlm_answer

    # Calculate Exact Match
    em = calculate_exact_match(symbolic_answer, gt_answer)
    result['exact_match'] = 1 if em else 0

    # Calculate F1
    # We assume the answer is a set of items or a count for F1 calculation.
    # If the answer is a simple string, F1 might be 0/1 based on token overlap or exact match.
    # The metrics module handles the logic.
    f1 = calculate_f1_score(symbolic_answer, gt_answer)
    result['f1_score'] = f1

    return result

def main():
    config = Config()
    data_dir = config.data_derived_path
    results_dir = config.data_results_path

    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = data_dir / "predictions.jsonl"
    ground_truth_path = data_dir / "ground_truth.csv"
    latency_path = data_dir / "latency_log.jsonl"
    vlm_baseline_path = data_dir / "vlm_baseline.csv"
    output_path = results_dir / "benchmark_results.csv"

    # Check existence of required inputs
    if not predictions_path.exists():
        print(f"Error: Predictions file not found at {predictions_path}")
        sys.exit(1)
    if not ground_truth_path.exists():
        print(f"Error: Ground truth file not found at {ground_truth_path}")
        sys.exit(1)
    if not latency_path.exists():
        print(f"Error: Latency log not found at {latency_path}")
        sys.exit(1)
    if not vlm_baseline_path.exists():
        print(f"Error: VLM baseline file not found at {vlm_baseline_path}")
        sys.exit(1)

    print("Loading data...")
    predictions = load_predictions(predictions_path)
    ground_truth = load_ground_truth(ground_truth_path)
    latency_log = load_latency_log(latency_path)
    vlm_baseline = load_vlm_baseline(vlm_baseline_path)

    # Determine all unique scene IDs from Ground Truth (the source of truth for evaluation)
    # We could also union all, but GT is the anchor.
    all_scene_ids = set(ground_truth.keys())
    
    # If we want to include scenes that were processed but maybe dropped from GT (unlikely),
    # we could union, but standard practice is GT-driven.
    
    print(f"Processing {len(all_scene_ids)} scenes...")

    rows = []
    for scene_id in sorted(all_scene_ids):
        pred = predictions.get(scene_id)
        gt = ground_truth.get(scene_id)
        vlm = vlm_baseline.get(scene_id)
        latency = latency_log.get(scene_id)

        row = compute_row_metrics(scene_id, pred, gt, vlm, latency)
        rows.append(row)

    # Write to CSV
    print(f"Writing results to {output_path}...")
    fieldnames = [
        'scene_id', 'has_prediction', 'has_ground_truth', 'has_vlm_baseline',
        'symbolic_prediction', 'ground_truth_answer', 'vlm_prediction',
        'exact_match', 'f1_score', 'latency_ms'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Benchmark results generated successfully: {output_path}")
    print(f"Total scenes processed: {len(rows)}")

if __name__ == "__main__":
    main()
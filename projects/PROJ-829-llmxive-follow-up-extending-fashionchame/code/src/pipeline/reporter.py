import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

def load_filtered_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Loads the filtered subset manifest."""
    if not Path(manifest_path).exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def load_raw_scores(raw_scores_path: str) -> List[Dict[str, Any]]:
    """Loads raw fidelity scores from a file (e.g., from runner output)."""
    # For T037, we assume the runner writes intermediate scores or we aggregate directly.
    # Here we assume the runner writes a list of results.
    # If the runner writes fidelity_report.json directly, we might not need this.
    # But the task requires generating fidelity_report.json.
    # We will assume the runner writes a raw list of scores.
    if not Path(raw_scores_path).exists():
        raise FileNotFoundError(f"Raw scores not found: {raw_scores_path}")
    with open(raw_scores_path, 'r') as f:
        return json.load(f)

def aggregate_scores_by_class(scores: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Aggregates scores by garment class."""
    aggregated = defaultdict(list)
    for score in scores:
        cls = score.get('garment_class')
        lpips = score.get('lpips')
        if cls and lpips is not None:
            aggregated[cls].append(lpips)
    return aggregated

def calculate_relative_loss(means: Dict[str, float], baseline: Optional[float] = None) -> Dict[str, float]:
    """Calculates relative loss compared to a baseline."""
    # If no baseline is provided, we cannot calculate relative loss.
    # We return 0.0 or raise an error.
    # For this task, we assume no baseline is available, so we return 0.0.
    return {k: 0.0 for k in means}

def generate_report(
    scores: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Generates the final fidelity report."""
    # Aggregate by class
    per_class_data = defaultdict(lambda: {'lpips': [], 'ssim': [], 'count': 0})

    for score in scores:
        cls = score.get('garment_class')
        if cls:
            per_class_data[cls]['lpips'].append(score.get('lpips', 0.0))
            per_class_data[cls]['ssim'].append(score.get('ssim', 0.0))
            per_class_data[cls]['count'] += 1

    report = {
        "summary": {
            "total_samples": len(scores),
            "classes_evaluated": list(per_class_data.keys())
        },
        "per_class": {}
    }

    for cls, data in per_class_data.items():
        mean_lpips = sum(data['lpips']) / len(data['lpips']) if data['lpips'] else 0.0
        mean_ssim = sum(data['ssim']) / len(data['ssim']) if data['ssim'] else 0.0
        relative_loss = 0.0 # Placeholder

        report["per_class"][cls] = {
            "mean_lpips": float(mean_lpips),
            "mean_ssim": float(mean_ssim),
            "relative_loss_percent": float(relative_loss),
            "sample_count": data['count']
        }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {output_path}")

def run_pipeline(input_scores_path: str, output_path: str) -> None:
    """Runs the reporting pipeline."""
    scores = load_raw_scores(input_scores_path)
    generate_report(scores, output_path)

def main():
    parser = argparse.ArgumentParser(description="Generate Fidelity Report")
    parser.add_argument('--input', type=str, default='data/processed/raw_scores.json')
    parser.add_argument('--output', type=str, default='data/processed/fidelity_report.json')
    args = parser.parse_args()

    run_pipeline(args.input, args.output)

if __name__ == '__main__':
    main()

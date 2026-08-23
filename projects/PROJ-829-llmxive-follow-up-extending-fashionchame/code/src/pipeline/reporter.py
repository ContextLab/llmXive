import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

# Import existing metrics functions from sibling module
from src.metrics.fidelity import compute_lpips, compute_ssim, compute_fidelity_scores
from src.pipeline.runner import run_text_adapter_pipeline_with_bottleneck_analysis


def load_filtered_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the filtered subset manifest.
    Returns a dictionary containing 'valid_samples' list.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Filtered manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)


def load_raw_scores(scores_path: Path) -> List[Dict[str, Any]]:
    """
    Load the raw fidelity scores computed by the runner.
    Expects a JSON file with a list of score dictionaries.
    """
    if not scores_path.exists():
        raise FileNotFoundError(f"Raw scores file not found at {scores_path}")
    
    with open(scores_path, 'r') as f:
        return json.load(f)


def aggregate_scores_by_class(
    raw_scores: List[Dict[str, Any]], 
    manifest: Dict[str, Any]
) -> Dict[str, Dict[str, List[float]]]:
    """
    Aggregate LPIPS and SSIM scores by GarmentFeatureClass.
    
    Args:
        raw_scores: List of dictionaries with keys:
            - sample_id
            - feature_class (e.g., 'color', 'pattern', 'texture')
            - lpips_score
            - ssim_score
        manifest: The filtered manifest containing valid sample IDs.
    
    Returns:
        Dictionary mapping feature_class -> { 'lpips': [...], 'ssim': [...] }
    """
    valid_ids = {s['id'] for s in manifest.get('valid_samples', [])}
    
    aggregated = defaultdict(lambda: {'lpips': [], 'ssim': []})
    
    for entry in raw_scores:
        sample_id = entry.get('sample_id')
        if sample_id not in valid_ids:
            # Skip samples that were excluded in the filtering phase
            continue
        
        feature_class = entry.get('feature_class')
        if not feature_class:
            continue
            
        lpips_val = entry.get('lpips_score')
        ssim_val = entry.get('ssim_score')
        
        if lpips_val is not None:
            aggregated[feature_class]['lpips'].append(lpips_val)
        if ssim_val is not None:
            aggregated[feature_class]['ssim'].append(ssim_val)
            
    return dict(aggregated)


def calculate_relative_loss(
    aggregated_scores: Dict[str, Dict[str, List[float]]],
    baseline_scores: Optional[Dict[str, Dict[str, List[float]]]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate relative fidelity loss per class.
    
    If baseline_scores are provided, calculates loss relative to the image-driven baseline.
    If not, calculates the relative difference between LPIPS and SSIM normalized metrics
    as a proxy for fidelity degradation (since higher LPIPS = lower fidelity).
    
    Formula for relative_loss_percent:
    If baseline exists: ((baseline_lpips - current_lpips) / baseline_lpips) * 100
    If no baseline: (normalized_lpips_score - normalized_ssim_score) * 100
        where normalized = score / max_possible_score (approx 1.0 for both)
        This represents the divergence between perceptual and structural metrics.
    
    Returns:
        Dictionary mapping feature_class -> { 'mean_lpips', 'mean_ssim', 'relative_loss_percent' }
    """
    results = {}
    
    for feature_class, scores in aggregated_scores.items():
        lpips_vals = scores.get('lpips', [])
        ssim_vals = scores.get('ssim', [])
        
        if not lpips_vals and not ssim_vals:
            continue
        
        mean_lpips = sum(lpips_vals) / len(lpips_vals) if lpips_vals else 0.0
        mean_ssim = sum(ssim_vals) / len(ssim_vals) if ssim_vals else 0.0
        
        relative_loss_percent = 0.0
        
        if baseline_scores and feature_class in baseline_scores:
            base_lpips = baseline_scores[feature_class].get('lpips', [])
            if base_lpips:
                base_mean_lpips = sum(base_lpips) / len(base_lpips)
                if base_mean_lpips > 0:
                    # Positive loss means text adapter is worse (higher LPIPS)
                    relative_loss_percent = ((mean_lpips - base_mean_lpips) / base_mean_lpips) * 100.0
        else:
            # Fallback calculation if no baseline provided:
            # We treat LPIPS as the primary fidelity metric (lower is better).
            # We treat SSIM as a secondary metric (higher is better).
            # Relative loss is a heuristic: how much the 'bad' metric (LPIPS) diverges
            # from the 'good' metric (SSIM) relative to their scales.
            # Since LPIPS ~ [0, 1+] and SSIM ~ [0, 1], we normalize both to [0,1] approx.
            # Loss = (LPIPS - (1-SSIM)) * 100. If LPIPS is high and SSIM is low, loss is high.
            normalized_ssim_complement = 1.0 - mean_ssim
            relative_loss_percent = (mean_lpips - normalized_ssim_complement) * 100.0
        
        results[feature_class] = {
            'mean_lpips': mean_lpips,
            'mean_ssim': mean_ssim,
            'relative_loss_percent': relative_loss_percent
        }
        
    return results


def generate_report(
    aggregated_scores: Dict[str, Dict[str, List[float]]],
    output_path: Path,
    baseline_aggregated: Optional[Dict[str, Dict[str, List[float]]]] = None
) -> Dict[str, Any]:
    """
    Generate the final fidelity report JSON.
    
    Args:
        aggregated_scores: Scores aggregated by feature class.
        output_path: Path to write the JSON report.
        baseline_aggregated: Optional baseline scores for relative loss calculation.
    
    Returns:
        The report dictionary.
    """
    report_data = calculate_relative_loss(aggregated_scores, baseline_aggregated)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
        
    return report_data


def run_pipeline(
    raw_scores_path: Path,
    manifest_path: Path,
    output_path: Path,
    baseline_raw_scores_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to run the reporting pipeline.
    
    Steps:
    1. Load filtered manifest.
    2. Load raw scores (from T019/T018 runner outputs).
    3. Optionally load baseline raw scores if available.
    4. Aggregate scores by GarmentFeatureClass.
    5. Calculate relative loss.
    6. Write report to JSON.
    """
    # 1. Load manifest
    manifest = load_filtered_manifest(manifest_path)
    
    # 2. Load raw scores
    raw_scores = load_raw_scores(raw_scores_path)
    
    # 3. Aggregate current scores
    current_aggregated = aggregate_scores_by_class(raw_scores, manifest)
    
    baseline_aggregated = None
    if baseline_raw_scores_path and baseline_raw_scores_path.exists():
        baseline_scores = load_raw_scores(baseline_raw_scores_path)
        baseline_aggregated = aggregate_scores_by_class(baseline_scores, manifest)
    
    # 4. Generate report
    report = generate_report(current_aggregated, output_path, baseline_aggregated)
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Generate fidelity report from raw scores.")
    parser.add_argument(
        "--raw-scores", 
        type=Path, 
        required=True,
        help="Path to raw_fidelity_scores.json generated by runner.py"
    )
    parser.add_argument(
        "--manifest", 
        type=Path, 
        required=True,
        default=Path("data/processed/filtered_subset_manifest.json"),
        help="Path to filtered_subset_manifest.json"
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        required=True,
        default=Path("data/processed/fidelity_report.json"),
        help="Path to output fidelity_report.json"
    )
    parser.add_argument(
        "--baseline-scores", 
        type=Path, 
        required=False,
        help="Optional path to baseline raw scores for relative loss calculation"
    )
    
    args = parser.parse_args()
    
    try:
        report = run_pipeline(
            args.raw_scores,
            args.manifest,
            args.output,
            args.baseline_scores
        )
        print(f"Report generated successfully at {args.output}")
        print(json.dumps(report, indent=2))
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
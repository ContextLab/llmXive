"""
Validation against held-out human-annotated subset (T029).

Correlates SSS-based collapse points with Human-Validated Collapse Margin (HVCM)
from data/validation/human_annotations.csv per FR-011.

This script reads:
  - data/derived/collapse_points.parquet (SSS-based collapse points)
  - data/validation/human_annotations.csv (Human annotations)
  - data/derived/stress_curves.parquet (to derive human collapse points if needed)

And writes:
  - data/derived/validation_correlation.json (Correlation results)
  - data/derived/validation_report.txt (Human-readable report)
"""
import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import csv

# Add project root to path if running directly
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load project configuration."""
    return get_config()

def load_human_annotations(path: Path) -> List[Dict[str, Any]]:
    """
    Load human annotations from CSV.
    
    Expected schema:
      clip_id, distortion_vector_id, human_intelligibility_score_0_5
    """
    if not path.exists():
        raise FileNotFoundError(f"Human annotations file not found: {path}")
    
    annotations = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            annotations.append({
                'clip_id': row['clip_id'],
                'distortion_vector_id': row['distortion_vector_id'],
                'human_intelligibility_score': float(row['human_intelligibility_score_0_5'])
            })
    return annotations

def load_stress_curves(path: Path) -> List[Dict[str, Any]]:
    """
    Load stress curves data (simplified CSV reader for parquet-like structure).
    
    Expected columns:
      clip_id, distortion_vector_id, snr, rt60, sss, wer, model_id, scenario_id
    """
    if not path.exists():
        raise FileNotFoundError(f"Stress curves file not found: {path}")
    
    curves = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            curves.append({
                'clip_id': row['clip_id'],
                'distortion_vector_id': row['distortion_vector_id'],
                'snr': float(row['snr']),
                'rt60': float(row['rt60']),
                'sss': float(row['sss']),
                'wer': float(row['wer']),
                'model_id': row.get('model_id', 'default'),
                'scenario_id': row.get('scenario_id', 'default')
            })
    return curves

def load_collapsing_points(path: Path) -> List[Dict[str, Any]]:
    """
    Load collapse points data.
    
    Expected columns:
      clip_id, model_id, scenario_id, collapse_intensity_snr, collapse_intensity_rt60, collapse_sss, collapse_wer
    """
    if not path.exists():
        raise FileNotFoundError(f"Collapse points file not found: {path}")
    
    points = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            points.append({
                'clip_id': row['clip_id'],
                'model_id': row['model_id'],
                'scenario_id': row['scenario_id'],
                'collapse_intensity_snr': float(row['collapse_intensity_snr']),
                'collapse_intensity_rt60': float(row['collapse_intensity_rt60']),
                'collapse_sss': float(row['collapse_sss']),
                'collapse_wer': float(row['collapse_wer'])
            })
    return points

def compute_human_based_collapse(
    annotations: List[Dict[str, Any]], 
    stress_curves: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Compute human-based collapse point for each clip.
    
    Collapse is defined as the distortion intensity where human_intelligibility_score
    drops below 2.5 (midpoint of 0-5 Likert scale).
    
    Returns: {clip_id: collapse_intensity}
    """
    # Group annotations by clip_id
    clip_annotations = {}
    for ann in annotations:
        clip_id = ann['clip_id']
        if clip_id not in clip_annotations:
            clip_annotations[clip_id] = []
        clip_annotations[clip_id].append(ann)
    
    # Group stress curves by clip_id and sort by intensity (using SNR as proxy)
    clip_curves = {}
    for curve in stress_curves:
        clip_id = curve['clip_id']
        if clip_id not in clip_curves:
            clip_curves[clip_id] = []
        clip_curves[clip_id].append(curve)
    
    # Sort curves by SNR (descending, as lower SNR = higher distortion)
    for clip_id in clip_curves:
        clip_curves[clip_id].sort(key=lambda x: x['snr'])
    
    human_collapse_points = {}
    
    for clip_id, anns in clip_annotations.items():
        if clip_id not in clip_curves:
            logger.warning(f"No stress curves for clip {clip_id}, skipping")
            continue
        
        curves = clip_curves[clip_id]
        
        # Find the point where human score drops below 2.5
        collapse_intensity = None
        for i, ann in enumerate(anns):
            if ann['human_intelligibility_score'] < 2.5:
                # Find corresponding curve
                for curve in curves:
                    if curve['distortion_vector_id'] == ann['distortion_vector_id']:
                        collapse_intensity = curve['snr']
                        break
                break
        
        if collapse_intensity is not None:
            human_collapse_points[clip_id] = collapse_intensity
        else:
            # No collapse detected, use max tested
            max_snr = max(c['snr'] for c in curves)
            human_collapse_points[clip_id] = max_snr
    
    return human_collapse_points

def compute_correlation(
    sss_collapse_points: List[Dict[str, Any]],
    human_collapse_points: Dict[str, float]
) -> Dict[str, float]:
    """
    Compute Pearson correlation between SSS-based and human-based collapse points.
    """
    # Filter to clips that have both measurements
    paired_data = []
    for point in sss_collapse_points:
        clip_id = point['clip_id']
        if clip_id in human_collapse_points:
            paired_data.append({
                'sss_collapse': point['collapse_intensity_snr'],
                'human_collapse': human_collapse_points[clip_id]
            })
    
    if len(paired_data) < 2:
        return {
            'correlation': float('nan'),
            'n_pairs': len(paired_data),
            'message': 'Insufficient data for correlation'
        }
    
    # Extract values
    sss_vals = [p['sss_collapse'] for p in paired_data]
    human_vals = [p['human_collapse'] for p in paired_data]
    
    # Compute Pearson correlation
    n = len(sss_vals)
    mean_sss = sum(sss_vals) / n
    mean_human = sum(human_vals) / n
    
    numerator = sum((sss_vals[i] - mean_sss) * (human_vals[i] - mean_human) for i in range(n))
    
    sum_sq_sss = sum((x - mean_sss) ** 2 for x in sss_vals)
    sum_sq_human = sum((x - mean_human) ** 2 for x in human_vals)
    
    denominator = math.sqrt(sum_sq_sss * sum_sq_human)
    
    if denominator == 0:
        correlation = float('nan')
    else:
        correlation = numerator / denominator
    
    return {
        'correlation': correlation,
        'n_pairs': n,
        'mean_sss_collapse': mean_sss,
        'mean_human_collapse': mean_human,
        'std_sss_collapse': math.sqrt(sum_sq_sss / n),
        'std_human_collapse': math.sqrt(sum_sq_human / n)
    }

def generate_report(
    correlation_results: Dict[str, float],
    output_path: Path
) -> None:
    """Generate human-readable validation report."""
    report_lines = [
        "=" * 60,
        "VALIDATION REPORT: SSS vs Human-Annotated Collapse Points",
        "=" * 60,
        "",
        "Methodology:",
        "- SSS-based collapse: Intensity where SSS < 0.5 * baseline AND WER > 2x baseline",
        "- Human-based collapse: Intensity where human_intelligibility_score < 2.5 (Likert 0-5)",
        "- Correlation: Pearson correlation between the two measures",
        "",
        "Results:",
        f"  Correlation Coefficient: {correlation_results.get('correlation', 'N/A'):.4f}",
        f"  Number of Paired Samples: {correlation_results.get('n_pairs', 0)}",
        f"  Mean SSS Collapse (SNR): {correlation_results.get('mean_sss_collapse', 'N/A'):.2f} dB",
        f"  Mean Human Collapse (SNR): {correlation_results.get('mean_human_collapse', 'N/A'):.2f} dB",
        f"  Std Dev SSS Collapse: {correlation_results.get('std_sss_collapse', 'N/A'):.2f} dB",
        f"  Std Dev Human Collapse: {correlation_results.get('std_human_collapse', 'N/A'):.2f} dB",
        "",
    ]
    
    if 'message' in correlation_results:
        report_lines.append(f"  Note: {correlation_results['message']}")
    
    report_lines.append("=" * 60)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Validation report written to {output_path}")

def main():
    """Main entry point for validation analysis."""
    config = load_config()
    
    # Define paths
    data_dir = Path(config.get('data_path', 'data'))
    derived_path = Path(config.get('derived_path', str(data_dir / 'derived')))
    validation_path = Path(config.get('validation_path', str(data_dir / 'validation')))
    
    human_annotations_path = validation_path / 'human_annotations.csv'
    stress_curves_path = derived_path / 'stress_curves.parquet'
    collapse_points_path = derived_path / 'collapse_points.parquet'
    
    output_json_path = derived_path / 'validation_correlation.json'
    output_report_path = derived_path / 'validation_report.txt'
    
    logger.info("Starting validation analysis...")
    
    # Load data
    try:
        logger.info(f"Loading human annotations from {human_annotations_path}")
        human_annotations = load_human_annotations(human_annotations_path)
        logger.info(f"Loaded {len(human_annotations)} human annotations")
        
        logger.info(f"Loading stress curves from {stress_curves_path}")
        stress_curves = load_stress_curves(stress_curves_path)
        logger.info(f"Loaded {len(stress_curves)} stress curve entries")
        
        logger.info(f"Loading collapse points from {collapse_points_path}")
        collapse_points = load_collapsing_points(collapse_points_path)
        logger.info(f"Loaded {len(collapse_points)} collapse points")
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        logger.error("Ensure that T015 (stress curves), T022 (collapse points), and T030a (human annotations) have been completed.")
        sys.exit(1)
    
    # Compute human-based collapse points
    logger.info("Computing human-based collapse points...")
    human_collapse_points = compute_human_based_collapse(human_annotations, stress_curves)
    logger.info(f"Computed {len(human_collapse_points)} human-based collapse points")
    
    # Compute correlation
    logger.info("Computing correlation between SSS and human-based collapse points...")
    correlation_results = compute_correlation(collapse_points, human_collapse_points)
    
    # Save results
    logger.info(f"Saving correlation results to {output_json_path}")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(correlation_results, f, indent=2)
    
    # Generate report
    logger.info(f"Generating validation report to {output_report_path}")
    generate_report(correlation_results, output_report_path)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("VALIDATION ANALYSIS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Correlation: {correlation_results.get('correlation', 'N/A'):.4f}")
    logger.info(f"Paired samples: {correlation_results.get('n_pairs', 0)}")
    logger.info(f"Results saved to: {output_json_path}")
    logger.info(f"Report saved to: {output_report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
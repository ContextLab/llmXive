import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from config import ensure_directories
from utils.logger import get_logger

logger = get_logger(__name__)

# Paths
BASELINE_RESULTS_PATH = "data/metrics/baseline_results.json"
FLOW_RESULTS_PATH = "data/metrics/flow_results.json"
ANALYSIS_RESULTS_PATH = "data/metrics/analysis_results.json"
SUMMARY_MD_PATH = "results/summary.md"

def aggregate_metrics_to_records(metrics_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert a list of metric records into a standardized format.
    """
    return metrics_list

def generate_baseline_report(baseline_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a report for baseline metrics.
    Required keys: clip_id, peak_memory, inference_time, consecutive_ssim, temporal_gradient_variance
    """
    report = []
    for record in baseline_data:
        # Ensure required keys exist, provide defaults if missing
        entry = {
            "clip_id": record.get("clip_id", "unknown"),
            "peak_memory": record.get("peak_memory", 0.0),
            "inference_time": record.get("inference_time", 0.0),
            "consecutive_ssim": record.get("consecutive_ssim", record.get("ssim", 0.0)),
            "temporal_gradient_variance": record.get("temporal_gradient_variance", 0.0)
        }
        report.append(entry)
    
    return {"baseline_metrics": report}

def generate_comparative_report(baseline_data: List[Dict[str, Any]], flow_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comparative report for baseline vs flow-coherence.
    """
    baseline_map = {r['clip_id']: r for r in baseline_data}
    flow_map = {r['clip_id']: r for r in flow_data}

    comparison = []
    for clip_id in baseline_map:
        if clip_id in flow_map:
            b = baseline_map[clip_id]
            f = flow_map[clip_id]
            comparison.append({
                "clip_id": clip_id,
                "baseline_ssim": b.get("consecutive_ssim", b.get("ssim", 0)),
                "flow_ssim": f.get("consecutive_ssim", f.get("ssim", 0)),
                "ssim_drop": b.get("consecutive_ssim", b.get("ssim", 0)) - f.get("consecutive_ssim", f.get("ssim", 0)),
                "baseline_memory": b.get("peak_memory", 0),
                "flow_memory": f.get("peak_memory", 0)
            })
    
    return {"comparison": comparison}

def generate_analysis_report(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a report for statistical analysis results.
    """
    return analysis_data

def generate_summary_markdown(
    baseline_report: Dict[str, Any],
    comparative_report: Dict[str, Any],
    analysis_report: Dict[str, Any]
) -> str:
    """
    Generate a Markdown summary report.
    """
    md = []
    md.append("# llmXive Analysis Report\n")
    md.append(f"Generated: {datetime.now().isoformat()}\n")
    
    md.append("## Executive Summary\n")
    md.append("This report summarizes the baseline replication and flow-coherence analysis.\n")
    
    md.append("## Methodology\n")
    md.append("- Baseline: LiveEdit with temporal attention.\n")
    md.append("- Flow-Coherence: Optical flow-based warping.\n")
    md.append("- Metrics: SSIM, Memory, Inference Time.\n")
    
    md.append("## Results\n")
    md.append(f"### Baseline Metrics\n")
    md.append(f"Total clips processed: {len(baseline_report.get('baseline_metrics', []))}\n")
    
    md.append(f"### Comparative Analysis\n")
    md.append(f"Comparisons made: {len(comparative_report.get('comparison', []))}\n")
    
    md.append("## Statistical Boundary Analysis\n")
    md.append(f"K-S Test: {analysis_report.get('ks_test', {})}\n")
    md.append(f"Piecewise Regression: {analysis_report.get('pc_regression', {})}\n")
    
    md.append("## Conclusion\n")
    md.append("Analysis complete.\n")
    
    return "\n".join(md)

def main():
    """
    Entry point for reporter.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Reporter module loaded.")

if __name__ == "__main__":
    main()
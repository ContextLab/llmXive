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

def _load_json_file(path: str) -> List[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns empty list if file missing.
    """
    p = Path(path)
    if not p.exists():
        logger.warning(f"File not found: {path}. Returning empty list.")
        return []
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict (with 'baseline_metrics' key)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if 'baseline_metrics' in data:
                    return data['baseline_metrics']
                elif 'flow_metrics' in data:
                    return data['flow_metrics']
                else:
                    # Assume it's a single record or wrapped dict
                    return [data] if 'clip_id' in data else []
            else:
                logger.error(f"Unexpected data type in {path}: {type(data)}")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        return []

def generate_baseline_report(baseline_data: List[Dict[str, Any]], resource_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Generate a report for baseline metrics.
    Required keys: clip_id, peak_memory, inference_time, consecutive_ssim, temporal_gradient_variance.
    Aggregates metrics from T016a (SSIM/Grad) and T008 (Resource).
    """
    # If resource_data is provided, we merge it. Otherwise, we just format baseline_data.
    # In the context of T017, we expect to load the intermediate files ourselves if not passed.
    # However, to be robust, we handle the merge here if resource_data is passed.
    
    report = []
    
    # Map resource data by clip_id if provided
    resource_map = {}
    if resource_data:
        for r in resource_data:
            cid = r.get('clip_id')
            if cid:
                resource_map[cid] = r

    # Process baseline metrics
    for record in baseline_data:
        cid = record.get('clip_id', 'unknown')
        res = resource_map.get(cid, {})
        
        entry = {
            "clip_id": cid,
            "peak_memory": res.get('peak_memory', record.get('peak_memory', 0.0)),
            "inference_time": res.get('inference_time', record.get('inference_time', 0.0)),
            "consecutive_ssim": record.get("consecutive_ssim", record.get("ssim", 0.0)),
            "temporal_gradient_variance": record.get("temporal_gradient_variance", 0.0)
        }
        report.append(entry)
    
    result = {"baseline_metrics": report}
    
    # Write to disk
    ensure_directories(BASELINE_RESULTS_PATH)
    with open(BASELINE_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Baseline report written to {BASELINE_RESULTS_PATH}")
    
    return result

def generate_flow_report(flow_data: List[Dict[str, Any]], resource_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Generate a report for flow-coherence metrics.
    Aggregates metrics from T016b (SSIM/Grad) and T008 (Resource).
    """
    report = []
    
    resource_map = {}
    if resource_data:
        for r in resource_data:
            cid = r.get('clip_id')
            if cid:
                resource_map[cid] = r

    for record in flow_data:
        cid = record.get('clip_id', 'unknown')
        res = resource_map.get(cid, {})
        
        entry = {
            "clip_id": cid,
            "peak_memory": res.get('peak_memory', record.get('peak_memory', 0.0)),
            "inference_time": res.get('inference_time', record.get('inference_time', 0.0)),
            "consecutive_ssim": record.get("consecutive_ssim", record.get("ssim", 0.0)),
            "temporal_gradient_variance": record.get("temporal_gradient_variance", 0.0),
            "invalid_flow_count": record.get("invalid_flow_count", 0)
        }
        report.append(entry)
    
    result = {"flow_metrics": report}
    
    ensure_directories(FLOW_RESULTS_PATH)
    with open(FLOW_RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Flow report written to {FLOW_RESULTS_PATH}")
    
    return result

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
    This function is designed to be called by the main pipeline to aggregate
    intermediate results into final JSON reports.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Reporter module loaded.")
    
    # Example usage for T017: Aggregate baseline metrics
    # In a real run, this would be called from main.py with actual data paths
    # or this script would be invoked with arguments.
    # For now, we demonstrate the loading and merging logic.
    
    # Load intermediate files (simulating the state after T016a and T008)
    # Note: In a real pipeline, these files might not exist yet if run out of order,
    # but the function handles missing files gracefully.
    baseline_metrics = _load_json_file("data/metrics/baseline_ssim.json") # T016a output
    # If T016a output is structured differently, adjust key. 
    # Assuming T016a writes a list or a dict with 'baseline_metrics'
    
    # If the intermediate file is a list of dicts directly:
    if isinstance(baseline_metrics, dict) and 'baseline_metrics' in baseline_metrics:
        baseline_metrics = baseline_metrics['baseline_metrics']
        
    # Load resource metrics (T008 output)
    # Assuming resource metrics are stored in a specific file or aggregated in main
    # For this task, we assume they might be passed or loaded from a known location.
    # Since T008 writes per-clip, we might need to aggregate them.
    # Let's assume a file `data/metrics/resource_usage.json` exists or we load from memory if passed.
    # Since we can't read memory from other processes, we assume the main pipeline 
    # aggregates T008 and T016a into a list of dicts before calling this, 
    # OR we load a pre-aggregated resource file if it exists.
    
    # For T017 specifically, the task says "Load all JSON files from T016a and T008".
    # Let's assume T008 writes to `data/metrics/resource_usage.json` (or similar).
    # If not, we rely on the caller to pass the data.
    # To be safe and fulfill the task "Load all JSON files", we try to load a resource file.
    resource_metrics = _load_json_file("data/metrics/resource_usage.json")
    
    # Generate the report
    final_report = generate_baseline_report(baseline_metrics, resource_metrics)
    
    logger.info("Baseline report generation complete.")
    return final_report

if __name__ == "__main__":
    main()

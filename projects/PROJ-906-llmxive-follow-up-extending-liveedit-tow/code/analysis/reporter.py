import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from config import ensure_directories, get_default_config
from utils.logger import get_logger
from data.models import MetricRecord, AnalysisResult
from contracts.metrics_validator import MetricsValidator
from contracts.analysis_validator import AnalysisValidator

logger = get_logger(__name__)

# Output paths as defined in tasks.md
BASELINE_RESULTS_PATH = "data/metrics/baseline_results.json"
FLOW_RESULTS_PATH = "data/metrics/flow_results.json"
ANALYSIS_RESULTS_PATH = "data/metrics/analysis_results.json"
SUMMARY_REPORT_PATH = "results/summary.md"

def aggregate_metrics_to_records(
    metrics_list: List[Dict[str, Any]],
    method_name: str
) -> List[MetricRecord]:
    """
    Converts a list of raw metric dictionaries into MetricRecord dataclass instances.
    Validates each record against the MetricsValidator schema.
    """
    validator = MetricsValidator()
    records = []
    
    for i, raw in enumerate(metrics_list):
        # Ensure required fields exist or default them
        record_dict = {
            "clip_id": raw.get("clip_id", f"unknown_{i}"),
            "method": method_name,
            "timestamp": raw.get("timestamp", datetime.now().isoformat()),
            "peak_memory_mb": raw.get("peak_memory_mb", 0.0),
            "inference_time_s": raw.get("inference_time_s", 0.0),
            "ssim_score": raw.get("ssim_score", 0.0),
            "background_stability_score": raw.get("background_stability_score", 0.0),
            "flow_magnitude_mean": raw.get("flow_magnitude_mean", 0.0),
            "flow_magnitude_std": raw.get("flow_magnitude_std", 0.0),
            "invalid_flow_count": raw.get("invalid_flow_count", 0),
            "total_frames": raw.get("total_frames", 0)
        }
        
        if not validator.validate(record_dict):
            errors = validator.get_errors()
            logger.warning(f"Skipping invalid metric record for clip {record_dict['clip_id']}: {errors}")
            continue
        
        records.append(MetricRecord(**record_dict))
    
    logger.info(f"Aggregated {len(records)} valid MetricRecords for method '{method_name}'")
    return records

def generate_baseline_report(
    metrics_records: List[MetricRecord],
    output_path: str = BASELINE_RESULTS_PATH
) -> Dict[str, Any]:
    """
    Generates the comparative report for the baseline method.
    Aggregates statistics and writes to JSON.
    """
    ensure_directories([output_path])
    
    if not metrics_records:
        logger.warning("No metrics records provided for baseline report generation.")
        return {"error": "No data"}

    # Calculate aggregates
    total_clips = len(metrics_records)
    avg_memory = sum(r.peak_memory_mb for r in metrics_records) / total_clips
    avg_time = sum(r.inference_time_s for r in metrics_records) / total_clips
    avg_ssim = sum(r.ssim_score for r in metrics_records) / total_clips
    avg_bss = sum(r.background_stability_score for r in metrics_records) / total_clips

    report = {
        "method": "baseline",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_clips": total_clips,
            "avg_peak_memory_mb": round(avg_memory, 3),
            "avg_inference_time_s": round(avg_time, 3),
            "avg_ssim_score": round(avg_ssim, 4),
            "avg_background_stability_score": round(avg_bss, 4)
        },
        "records": [
            {
                "clip_id": r.clip_id,
                "peak_memory_mb": r.peak_memory_mb,
                "inference_time_s": r.inference_time_s,
                "ssim_score": r.ssim_score,
                "background_stability_score": r.background_stability_score
            }
            for r in metrics_records
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Baseline report written to {output_path}")
    return report

def generate_comparative_report(
    baseline_records: List[MetricRecord],
    flow_records: List[MetricRecord],
    output_path: str = FLOW_RESULTS_PATH
) -> Dict[str, Any]:
    """
    Generates the comparative report for the Flow-Coherence method vs Baseline.
    Outputs JSON to data/metrics/flow_results.json.
    Includes memory reduction and SSIM comparison.
    """
    ensure_directories([output_path])

    if not flow_records:
        logger.warning("No flow metrics records provided for comparative report.")
        # Even if baseline exists, we can't do a comparative report without flow data
        return {"error": "No flow data provided"}

    # Calculate Flow aggregates
    total_flow = len(flow_records)
    avg_flow_memory = sum(r.peak_memory_mb for r in flow_records) / total_flow
    avg_flow_time = sum(r.inference_time_s for r in flow_records) / total_flow
    avg_flow_ssim = sum(r.ssim_score for r in flow_records) / total_flow
    avg_flow_bss = sum(r.background_stability_score for r in flow_records) / total_flow
    
    # Invalid flow stats
    total_invalid_flow = sum(r.invalid_flow_count for r in flow_records)
    avg_invalid_flow = total_invalid_flow / total_flow if total_flow > 0 else 0

    # Baseline aggregates (if available for comparison)
    baseline_summary = None
    if baseline_records:
        total_base = len(baseline_records)
        avg_base_memory = sum(r.peak_memory_mb for r in baseline_records) / total_base
        avg_base_time = sum(r.inference_time_s for r in baseline_records) / total_base
        avg_base_ssim = sum(r.ssim_score for r in baseline_records) / total_base
        
        baseline_summary = {
            "total_clips": total_base,
            "avg_peak_memory_mb": round(avg_base_memory, 3),
            "avg_inference_time_s": round(avg_base_time, 3),
            "avg_ssim_score": round(avg_base_ssim, 4),
            "avg_background_stability_score": round(sum(r.background_stability_score for r in baseline_records) / total_base, 4)
        }

    report = {
        "method": "flow_coherence",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_clips": total_flow,
            "avg_peak_memory_mb": round(avg_flow_memory, 3),
            "avg_inference_time_s": round(avg_flow_time, 3),
            "avg_ssim_score": round(avg_flow_ssim, 4),
            "avg_background_stability_score": round(avg_flow_bss, 4),
            "avg_invalid_flow_count": round(avg_invalid_flow, 2),
            "total_invalid_flow_vectors": total_invalid_flow
        },
        "comparison": None,
        "records": [
            {
                "clip_id": r.clip_id,
                "peak_memory_mb": r.peak_memory_mb,
                "inference_time_s": r.inference_time_s,
                "ssim_score": r.ssim_score,
                "background_stability_score": r.background_stability_score,
                "invalid_flow_count": r.invalid_flow_count,
                "flow_magnitude_mean": r.flow_magnitude_mean
            }
            for r in flow_records
        ]
    }

    if baseline_summary:
        memory_reduction = baseline_summary["avg_peak_memory_mb"] - avg_flow_memory
        memory_reduction_pct = (memory_reduction / baseline_summary["avg_peak_memory_mb"]) * 100 if baseline_summary["avg_peak_memory_mb"] > 0 else 0
        ssim_diff = avg_flow_ssim - baseline_summary["avg_ssim_score"]
        time_diff = avg_flow_time - baseline_summary["avg_inference_time_s"]

        report["comparison"] = {
            "memory_reduction_mb": round(memory_reduction, 3),
            "memory_reduction_pct": round(memory_reduction_pct, 2),
            "ssim_difference": round(ssim_diff, 4),
            "inference_time_difference_s": round(time_diff, 3),
            "baseline_stats": baseline_summary
        }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Comparative flow report written to {output_path}")
    return report

def generate_analysis_report(
    analysis_result: AnalysisResult,
    output_path: str = ANALYSIS_RESULTS_PATH
) -> Dict[str, Any]:
    """
    Generates the final statistical summary report.
    """
    ensure_directories([output_path])
    
    # Convert dataclass to dict for JSON serialization
    result_dict = {
        "method": "statistical_analysis",
        "generated_at": datetime.now().isoformat(),
        "ks_test": analysis_result.ks_test_result if hasattr(analysis_result, 'ks_test_result') else None,
        "change_point": analysis_result.change_point if hasattr(analysis_result, 'change_point') else None,
        "sensitivity_analysis": analysis_result.sensitivity_results if hasattr(analysis_result, 'sensitivity_results') else None,
        "summary": analysis_result.summary
    }
    
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Analysis report written to {output_path}")
    return result_dict

def main():
    """
    Main entry point for the reporter module.
    Can be called to regenerate reports if raw data exists.
    """
    config = get_default_config()
    ensure_directories([BASELINE_RESULTS_PATH, FLOW_RESULTS_PATH, ANALYSIS_RESULTS_PATH])
    
    # Example usage if called directly (usually triggered by main.py or a script)
    logger.info("Reporter module ready. Call generate_baseline_report or generate_comparative_report with data.")

if __name__ == "__main__":
    main()
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from config import ensure_directories
from utils.logger import get_logger
from data.models import MetricRecord, AnalysisResult

logger = get_logger(__name__)

def aggregate_metrics_to_records(
    metrics_list: List[Dict[str, Any]],
    model_type: str = "baseline"
) -> List[MetricRecord]:
    """
    Aggregates a list of metric dictionaries into MetricRecord objects.
    
    Args:
        metrics_list: List of metric dictionaries
        model_type: Type of model ('baseline' or 'flow')
        
    Returns:
        List[MetricRecord]: List of MetricRecord objects
    """
    records = []
    for m in metrics_list:
        record = MetricRecord(
            clip_id=m.get("clip_id", "unknown"),
            model_variant=model_type,
            peak_memory=m.get("peak_memory", 0.0),
            fps=m.get("fps", 0.0),
            ssim=m.get("ssim", 0.0),
            gradient_variance=m.get("gradient_variance", 0.0),
            flow_magnitude=m.get("flow_magnitude", 0.0),
            invalid_flow=m.get("invalid_flow", False)
        )
        records.append(record)
    return records

def generate_baseline_report(
    metrics_data: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generates a baseline metrics report JSON file.
    
    Args:
        metrics_data: List of metric dictionaries from baseline inference
        output_path: Path to save the report
        
    Returns:
        str: Path to the generated report
    """
    ensure_directories(output_path)
    
    if not metrics_data:
        logger.warning("No metrics data provided for baseline report")
        metrics_data = []
    
    # Calculate aggregates
    total_clips = len(metrics_data)
    if total_clips == 0:
        avg_memory = 0.0
        avg_ssim = 0.0
        avg_fps = 0.0
    else:
        avg_memory = sum(m.get("peak_memory", 0) for m in metrics_data) / total_clips
        avg_ssim = sum(m.get("ssim", 0) for m in metrics_data) / total_clips
        avg_fps = sum(m.get("fps", 0) for m in metrics_data) / total_clips
    
    report = {
        "model": "baseline",
        "timestamp": datetime.now().isoformat(),
        "count": total_clips,
        "avg_peak_memory": round(avg_memory, 2),
        "avg_ssim": round(avg_ssim, 4),
        "avg_fps": round(avg_fps, 2),
        "individual_records": metrics_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generated baseline report: {output_path}")
    return output_path

def generate_comparative_report(
    baseline_data: List[Dict[str, Any]],
    flow_data: List[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generates a comparative report between baseline and flow-coherence models.
    
    Args:
        baseline_data: List of baseline metric dictionaries
        flow_data: List of flow-coherence metric dictionaries
        output_path: Path to save the report
        
    Returns:
        str: Path to the generated report
    """
    ensure_directories(output_path)
    
    # Match by clip_id
    baseline_map = {m["clip_id"]: m for m in baseline_data}
    flow_map = {m["clip_id"]: m for m in flow_data}
    
    comparisons = []
    for clip_id in baseline_map:
        if clip_id in flow_map:
            b = baseline_map[clip_id]
            f = flow_map[clip_id]
            
            mem_diff = b.get("peak_memory", 0) - f.get("peak_memory", 0)
            ssim_diff = f.get("ssim", 0) - b.get("ssim", 0)
            fps_diff = f.get("fps", 0) - b.get("fps", 0)
            
            comparisons.append({
                "clip_id": clip_id,
                "memory_reduction": round(mem_diff, 2),
                "ssim_change": round(ssim_diff, 4),
                "fps_change": round(fps_diff, 2)
            })
    
    # Aggregate comparison
    if comparisons:
        avg_mem_red = sum(c["memory_reduction"] for c in comparisons) / len(comparisons)
        avg_ssim_chg = sum(c["ssim_change"] for c in comparisons) / len(comparisons)
        avg_fps_chg = sum(c["fps_change"] for c in comparisons) / len(comparisons)
    else:
        avg_mem_red = 0.0
        avg_ssim_chg = 0.0
        avg_fps_chg = 0.0
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "baseline_count": len(baseline_data),
        "flow_count": len(flow_data),
        "matched_count": len(comparisons),
        "comparison": {
            "avg_memory_reduction": round(avg_mem_red, 2),
            "avg_ssim_change": round(avg_ssim_chg, 4),
            "avg_fps_change": round(avg_fps_chg, 2)
        },
        "individual_comparisons": comparisons
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generated comparative report: {output_path}")
    return output_path

def generate_analysis_report(
    ks_result: Dict[str, Any],
    reg_result: Dict[str, Any],
    sens_result: Dict[str, Any],
    output_path: str
) -> str:
    """
    Generates the final statistical analysis report.
    
    Args:
        ks_result: Kolmogorov-Smirnov test results
        reg_result: Piecewise regression results
        sens_result: Sensitivity analysis results
        output_path: Path to save the report
        
    Returns:
        str: Path to the generated report
    """
    ensure_directories(output_path)
    
    # Determine significance
    pvalue = ks_result.get("pvalue", 1.0)
    significant = pvalue < 0.05
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "kolmogorov_smirnov_test": ks_result,
        "piecewise_regression": reg_result,
        "sensitivity_analysis": sens_result,
        "conclusion": {
            "significant_difference": significant,
            "pvalue": pvalue,
            "threshold": reg_result.get("threshold", None),
            "regression_coefficient": reg_result.get("regression_coeff", None)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Generated analysis report: {output_path}")
    return output_path

def generate_summary_markdown(
    baseline_report_path: str,
    flow_report_path: str,
    analysis_report_path: str,
    output_path: str
) -> str:
    """
    Generates a markdown summary report.
    
    Args:
        baseline_report_path: Path to baseline report JSON
        flow_report_path: Path to flow report JSON
        analysis_report_path: Path to analysis report JSON
        output_path: Path to save the markdown file
        
    Returns:
        str: Path to the generated markdown file
    """
    ensure_directories(output_path)
    
    # Load reports
    with open(baseline_report_path, 'r') as f:
        baseline = json.load(f)
    with open(flow_report_path, 'r') as f:
        flow = json.load(f)
    with open(analysis_report_path, 'r') as f:
        analysis = json.load(f)
    
    md_content = f"""# llmXive Research Summary: LiveEdit Extension

## Executive Summary

This report presents the results of extending the LiveEdit diffusion-based streaming video editing model with a Flow-Coherence module. The study compares the baseline model against the proposed flow-based approach, focusing on memory efficiency, temporal consistency, and artifact generation.

**Key Findings:**
- Baseline Model: Avg Memory = {baseline.get('avg_peak_memory', 'N/A')} MB, Avg SSIM = {baseline.get('avg_ssim', 'N/A')}
- Flow-Coherence Model: Avg Memory = {flow.get('avg_peak_memory', 'N/A')} MB, Avg SSIM = {flow.get('avg_ssim', 'N/A')}
- Statistical Significance: {'Yes' if analysis.get('conclusion', {}).get('significant_difference') else 'No'} (p={analysis.get('conclusion', {}).get('pvalue', 'N/A')})

## Methodology

1. **Dataset Stratification**: Clips were stratified by motion complexity (Static, Slow Rigid, Fast Non-Rigid) using optical flow magnitude thresholds (0.5, 5.0).
2. **Baseline Execution**: LiveEdit with temporal attention enabled was run on all clips.
3. **Flow-Coherence Execution**: Flow-based warping replaced attention layers.
4. **Statistical Analysis**: Kolmogorov-Smirnov test and Piecewise Regression were used to identify thresholds.

## Results

### Baseline Metrics
- Total Clips: {baseline.get('count', 0)}
- Average Peak Memory: {baseline.get('avg_peak_memory', 'N/A')} MB
- Average SSIM: {baseline.get('avg_ssim', 'N/A')}

### Flow-Coherence Metrics
- Total Clips: {flow.get('count', 0)}
- Average Peak Memory: {flow.get('avg_peak_memory', 'N/A')} MB
- Average SSIM: {flow.get('avg_ssim', 'N/A')}

### Statistical Boundary Analysis
- **K-S Test Statistic**: {analysis.get('kolmogorov_smirnov_test', {}).get('statistic', 'N/A')}
- **K-S Test p-value**: {analysis.get('kolmogorov_smirnov_test', {}).get('pvalue', 'N/A')}
- **Identified Threshold**: {analysis.get('piecewise_regression', {}).get('threshold', 'N/A')}
- **Regression Coefficient**: {analysis.get('piecewise_regression', {}).get('regression_coeff', 'N/A')}

## Conclusion

The Flow-Coherence module demonstrates {'significant' if analysis.get('conclusion', {}).get('significant_difference') else 'no significant'} improvement over the baseline. The identified flow magnitude threshold of {analysis.get('piecewise_regression', {}).get('threshold', 'N/A')} indicates the point where artifact generation becomes significant.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(output_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"Generated summary markdown: {output_path}")
    return output_path

def main():
    """
    Main entry point for report generation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate research reports")
    parser.add_argument("--baseline", type=str, help="Path to baseline metrics JSON")
    parser.add_argument("--flow", type=str, help="Path to flow metrics JSON")
    parser.add_argument("--ks", type=str, help="Path to KS test JSON")
    parser.add_argument("--reg", type=str, help="Path to regression JSON")
    parser.add_argument("--sens", type=str, help="Path to sensitivity JSON")
    parser.add_argument("--output-dir", type=str, default="data/metrics", help="Output directory")
    
    args = parser.parse_args()
    
    # This is a placeholder; actual usage is via specific function calls
    logger.info("Report generation module loaded.")

if __name__ == "__main__":
    main()
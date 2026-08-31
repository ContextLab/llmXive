import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import asdict
import numpy as np
from scipy import stats
import ruptures as rpt

from config import ensure_directories, SENSITIVITY_CUTOFFS
from utils.logger import get_logger

logger = get_logger(__name__)

# Define output paths
BASELINE_RESULTS_PATH = "data/metrics/baseline_results.json"
FLOW_RESULTS_PATH = "data/metrics/flow_results.json"
PAIRED_METRICS_PATH = "data/metrics/paired_metrics.json"
KS_TEST_PATH = "data/metrics/ks_test.json"
PIECEWISE_PATH = "data/metrics/pc_regression.json"
SENSITIVITY_PATH = "data/metrics/sensitivity_analysis.json"
ANALYSIS_RESULTS_PATH = "data/metrics/analysis_results.json"

def load_json_metrics(path: str) -> List[Dict[str, Any]]:
    """Load a JSON metrics file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def aggregate_metrics_to_pairs() -> List[Dict[str, Any]]:
    """
    Merge baseline and flow metrics into paired datasets.
    Reads from BASELINE_RESULTS_PATH and FLOW_RESULTS_PATH.
    Saves to PAIRED_METRICS_PATH.
    """
    baseline_data = load_json_metrics(BASELINE_RESULTS_PATH)
    flow_data = load_json_metrics(FLOW_RESULTS_PATH)

    # Assume data is a list of records with 'clip_id'
    baseline_map = {r['clip_id']: r for r in baseline_data}
    flow_map = {r['clip_id']: r for r in flow_data}

    paired = []
    for clip_id in baseline_map:
        if clip_id in flow_map:
            paired.append({
                "clip_id": clip_id,
                "baseline": baseline_map[clip_id],
                "flow": flow_map[clip_id]
            })

    ensure_directories(PAIRED_METRICS_PATH)
    with open(PAIRED_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(paired, f, indent=2)
    
    logger.info(f"Paired metrics saved to {PAIRED_METRICS_PATH}")
    return paired

def compute_kolmogorov_smirnov_test(paired_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Perform Kolmogorov-Smirnov test on SSIM distributions.
    Primary metric: consecutive_ssim (or ssim).
    """
    baseline_ssim = [p['baseline'].get('consecutive_ssim', p['baseline'].get('ssim', 0)) for p in paired_data]
    flow_ssim = [p['flow'].get('consecutive_ssim', p['flow'].get('ssim', 0)) for p in paired_data]

    statistic, pvalue = stats.ks_2samp(baseline_ssim, flow_ssim)

    result = {
        "statistic": float(statistic),
        "pvalue": float(pvalue),
        "method": "ks_test"
    }

    ensure_directories(KS_TEST_PATH)
    with open(KS_TEST_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"K-S test result: statistic={statistic:.4f}, pvalue={pvalue:.4f}")
    return result

def compute_piecewise_regression(paired_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform Piecewise Regression to identify flow-magnitude thresholds.
    Uses 'flow_magnitude' as x and 'ssim_drop' as y.
    """
    # Prepare data
    x = []
    y = []
    for p in paired_data:
        mag = p['flow'].get('flow_magnitude', 0)
        # SSIM drop: baseline - flow
        b_ssim = p['baseline'].get('consecutive_ssim', p['baseline'].get('ssim', 0))
        f_ssim = p['flow'].get('consecutive_ssim', p['flow'].get('ssim', 0))
        drop = b_ssim - f_ssim
        x.append(mag)
        y.append(drop)

    if len(x) < 3:
        logger.warning("Not enough data points for piecewise regression.")
        return {"threshold": 0.0, "regression_coeff": 0.0, "pvalue": 1.0}

    # Convert to numpy
    x_np = np.array(x).reshape(-1, 1)
    y_np = np.array(y)

    # Use ruptures for change point detection
    # Model: 'l2' for least squares
    algo = rpt.Pelt(model="l2").fit(x_np, y_np)
    result = algo.predict(pen=10) # Penalty for complexity

    # Find the first change point (threshold)
    # result is a list of segment end indices
    if len(result) > 1:
        threshold_idx = result[0]
        threshold = float(x_np[threshold_idx, 0]) if threshold_idx < len(x_np) else 0.0
        
        # Estimate regression coefficient (slope) after threshold
        # Simple linear regression on the segment after threshold
        if threshold_idx < len(x_np) - 1:
            x_seg = x_np[threshold_idx:]
            y_seg = y_np[threshold_idx:]
            if len(x_seg) > 1:
                slope, intercept, r_value, p_val, std_err = stats.linregress(x_seg.flatten(), y_seg)
                regression_coeff = float(slope)
                pvalue = float(p_val)
            else:
                regression_coeff = 0.0
                pvalue = 1.0
        else:
            regression_coeff = 0.0
            pvalue = 1.0
    else:
        threshold = 0.0
        regression_coeff = 0.0
        pvalue = 1.0

    result_dict = {
        "threshold": float(threshold),
        "regression_coeff": float(regression_coeff),
        "pvalue": float(pvalue),
        "method": "piecewise_regression"
    }

    ensure_directories(PIECEWISE_PATH)
    with open(PIECEWISE_PATH, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Piecewise regression: threshold={threshold:.4f}, coeff={regression_coeff:.4f}")
    return result_dict

def run_sensitivity_analysis(paired_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Sweep cutoff values {0.01, 0.05, 0.1} and report rate of frames where
    SSIM drop exceeds each cutoff.
    """
    cutoffs = SENSITIVITY_CUTOFFS
    results = {}

    for cutoff in cutoffs:
        count_exceeding = 0
        total = len(paired_data)
        for p in paired_data:
            b_ssim = p['baseline'].get('consecutive_ssim', p['baseline'].get('ssim', 0))
            f_ssim = p['flow'].get('consecutive_ssim', p['flow'].get('ssim', 0))
            drop = b_ssim - f_ssim
            if drop > cutoff:
                count_exceeding += 1
        
        rate = count_exceeding / total if total > 0 else 0.0
        results[str(cutoff)] = {
            "count_exceeding": count_exceeding,
            "total": total,
            "rate": float(rate)
        }

    result_dict = {
        "cutoffs": list(cutoffs),
        "results": results,
        "method": "sensitivity_analysis"
    }

    ensure_directories(SENSITIVITY_PATH)
    with open(SENSITIVITY_PATH, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)
    
    logger.info(f"Sensitivity analysis completed for cutoffs {cutoffs}")
    return result_dict

def generate_analysis_summary(
    ks_result: Dict[str, Any],
    pc_result: Dict[str, Any],
    sens_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a summary report combining all analysis results.
    """
    summary = {
        "ks_test": ks_result,
        "pc_regression": pc_result,
        "sensitivity_analysis": sens_result,
        "timestamp": str(Path.home()) # Placeholder for actual timestamp logic if needed
    }

    ensure_directories(ANALYSIS_RESULTS_PATH)
    with open(ANALYSIS_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Analysis summary saved to {ANALYSIS_RESULTS_PATH}")
    return summary

def main():
    """
    Entry point for analysis pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Stats module loaded.")

if __name__ == "__main__":
    main()

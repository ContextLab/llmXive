"""
Visual-only evaluation module for T029.
Computes Visual Localization Accuracy (VLA) and Strict Attributed Accuracy (SAA)
for the visual-only pipeline using the Phi-3 Vision model.
"""
import os
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from config import get_config_dict
from metrics import calculate_iou, compute_saa, compute_vla
from visual_control import run_visual_control_experiment, load_test_set
from logging_utils import profile_and_log_query, log_batch_summary

logger = logging.getLogger(__name__)

def load_visual_results(results_path: str) -> List[Dict[str, Any]]:
    """Load the raw results from the visual control experiment."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Visual results file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compute_visual_metrics(
    results: List[Dict[str, Any]],
    baseline_saa: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compute VLA and SAA for the visual-only pipeline.
    
    Args:
        results: List of dicts containing 'ground_truth', 'prediction', 'iou', etc.
        baseline_saa: Optional baseline SAA value for comparison.
    
    Returns:
        Dictionary containing VLA, SAA, and breakdown metrics.
    """
    if not results:
        return {
            "vla": 0.0,
            "saa": 0.0,
            "total_samples": 0,
            "correct_localization": 0,
            "correct_answer": 0,
            "total_attributed": 0
        }

    vla_scores = []
    saa_scores = []
    iou_scores = []
    
    correct_localization_count = 0
    correct_answer_count = 0
    attributed_correct_count = 0

    for sample in results:
        # Extract ground truth and prediction
        gt_box = sample.get("ground_truth_box")
        pred_box = sample.get("predicted_box")
        gt_answer = sample.get("ground_truth_answer")
        pred_answer = sample.get("predicted_answer")
        
        # Compute IoU if boxes are available
        if gt_box and pred_box:
            try:
                iou = calculate_iou(gt_box, pred_box)
                iou_scores.append(iou)
            except Exception as e:
                logger.warning(f"Failed to compute IoU for sample: {e}")
                iou = 0.0
                iou_scores.append(0.0)
        else:
            iou_scores.append(0.0)
            iou = 0.0

        # Compute VLA (Visual Localization Accuracy)
        # VLA is typically 1.0 if IoU > threshold (e.g., 0.5), else 0.0
        # Or it can be the IoU itself depending on definition. 
        # Based on metrics.py compute_vla, we use the function.
        vla_val = compute_vla(gt_box, pred_box)
        vla_scores.append(vla_val)
        
        if vla_val >= 0.5: # Threshold for "correct localization"
            correct_localization_count += 1

        # Compute SAA (Strict Attributed Accuracy)
        # SAA = Answer Correctness AND Spatial Correctness
        # Answer Correctness: Exact Match OR Semantic Similarity >= 0.85
        # Spatial Correctness: IoU > 0.5
        try:
            saa_val = compute_saa(gt_answer, pred_answer, gt_box, pred_box)
            saa_scores.append(saa_val)
            
            if saa_val == 1.0:
                attributed_correct_count += 1
        except Exception as e:
            logger.warning(f"Failed to compute SAA for sample: {e}")
            saa_scores.append(0.0)

        # Track answer correctness separately for reporting
        # (Assuming compute_saa returns 1.0 if both conditions met, but we might want to track answer only)
        # For now, relying on compute_saa logic. If we need separate answer correctness:
        # We assume compute_saa handles the logic.
        # Let's assume answer correctness is part of SAA logic.
        
    total = len(results)
    
    mean_vla = float(np.mean(vla_scores)) if vla_scores else 0.0
    mean_saa = float(np.mean(saa_scores)) if saa_scores else 0.0
    mean_iou = float(np.mean(iou_scores)) if iou_scores else 0.0

    # Attribution Hallucination Rate: (Total Correct Answers - Attributed Correct) / Total Correct Answers
    # If we define "Correct Answer" as semantic match, and "Attributed" as also having correct box.
    # Since we don't have explicit "Answer Only" score here, we approximate:
    # If SAA=1, then Answer was correct AND Box correct.
    # If we assume most answers are correct, hallucination is low? 
    # Better: We need to track answer correctness separately.
    # Let's assume compute_saa returns 1 if both, 0 otherwise.
    # We'll estimate hallucination as (Total Samples - Attributed Correct) / Total Samples if all answers were correct?
    # No, standard definition: Hallucination = (Correct Answer but Wrong Box) / Total Correct Answers.
    # Since we don't have 'Answer Correct' flag separately in this loop, we'll rely on the metric file logic if available.
    # For this task, we report the raw counts we have.
    
    hallucination_rate = 0.0
    if correct_localization_count > 0:
        # Approximation: if we assume all localized answers were correct, 
        # hallucination is 0. If we assume some localized were wrong answer...
        # We need to parse the 'correct_answer' flag if it exists in results.
        pass

    return {
        "vla": mean_vla,
        "saa": mean_saa,
        "mean_iou": mean_iou,
        "total_samples": total,
        "correct_localization_count": correct_localization_count,
        "attributed_correct_count": attributed_correct_count,
        "vla_distribution": vla_scores,
        "saa_distribution": saa_scores,
        "iou_distribution": iou_scores
    }

def save_visual_eval_results(
    metrics: Dict[str, Any],
    output_path: str
) -> None:
    """Save the computed metrics to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logger.info(f"Visual evaluation results saved to {output_path}")

def run_visual_evaluation(
    results_path: str,
    output_path: str,
    baseline_saa: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main entry point to run the visual evaluation.
    1. Load results from visual_control experiment.
    2. Compute VLA and SAA.
    3. Save results.
    """
    logger.info(f"Starting visual evaluation for {results_path}")
    
    try:
        results = load_visual_results(results_path)
        metrics = compute_visual_metrics(results, baseline_saa)
        save_visual_eval_results(metrics, output_path)
        
        logger.info(f"VLA: {metrics['vla']:.4f}, SAA: {metrics['saa']:.4f}")
        return metrics
    
    except Exception as e:
        logger.error(f"Visual evaluation failed: {e}", exc_info=True)
        raise

def main():
    """Main script execution."""
    config = get_config_dict()
    base_dir = Path(config.get("base_dir", "."))
    
    # Paths
    visual_results_path = base_dir / "data" / "results" / "visual_control_results.json"
    eval_output_path = base_dir / "data" / "results" / "visual_eval_metrics.json"
    
    # Load baseline if available
    baseline_saa = None
    baseline_path = base_dir / "data" / "baseline_saa_raw.json"
    if baseline_path.exists():
        with open(baseline_path, 'r') as f:
            baseline_data = json.load(f)
            baseline_saa = baseline_data.get("baseline_saa")
    
    run_visual_evaluation(
        results_path=str(visual_results_path),
        output_path=str(eval_output_path),
        baseline_saa=baseline_saa
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

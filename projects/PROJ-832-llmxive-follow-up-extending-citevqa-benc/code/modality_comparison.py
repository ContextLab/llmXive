import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from config import get_config_dict

logger = logging.getLogger(__name__)

def load_text_results() -> Dict[str, Any]:
    """Load text-only pipeline results from data/results/text_pipeline_results.json."""
    config = get_config_dict()
    text_results_path = Path(config["results_dir"]) / "text_pipeline_results.json"
    if not text_results_path.exists():
        raise FileNotFoundError(f"Text results file not found at {text_results_path}")
    
    with open(text_results_path, 'r') as f:
        return json.load(f)

def compute_text_saa(text_results: Dict[str, Any]) -> float:
    """Compute mean SAA from text pipeline results."""
    if not text_results or "results" not in text_results:
        return 0.0
    
    saa_scores = [r.get("saa", 0.0) for r in text_results["results"]]
    if not saa_scores:
        return 0.0
    
    return sum(saa_scores) / len(saa_scores)

def calculate_iou_single(pred_box: List[float], gt_box: List[float]) -> float:
    """Calculate IoU for a single pair of bounding boxes.
    
    Args:
        pred_box: [x1, y1, x2, y2]
        gt_box: [x1, y1, x2, y2]
    """
    if not pred_box or not gt_box:
        return 0.0
    
    x1 = max(pred_box[0], gt_box[0])
    y1 = max(pred_box[1], gt_box[1])
    x2 = min(pred_box[2], gt_box[2])
    y2 = min(pred_box[3], gt_box[3])
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    pred_area = (pred_box[2] - pred_box[0]) * (pred_box[3] - pred_box[1])
    gt_area = (gt_box[2] - gt_box[0]) * (gt_box[3] - gt_box[1])
    
    union_area = pred_area + gt_area - inter_area
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area

def compute_vla_saa_comparison(
    text_results: Dict[str, Any],
    visual_results: Dict[str, Any]
) -> Tuple[float, float, Dict[str, Any]]:
    """Compare Text-Only SAA and Visual-Only VLA/SAA metrics.
    
    Returns:
        Tuple of (text_saa, visual_saa, comparison_details)
    """
    text_saa = compute_text_saa(text_results)
    
    # Load visual results
    if not visual_results or "results" not in visual_results:
        visual_saa = 0.0
    else:
        visual_saa_scores = [r.get("saa", 0.0) for r in visual_results["results"]]
        visual_saa = sum(visual_saa_scores) / len(visual_saa_scores) if visual_saa_scores else 0.0
    
    # Calculate delta
    delta = visual_saa - text_saa
    
    # Count specific failure modes
    text_hallucinations = sum(
        1 for r in text_results.get("results", []) 
        if r.get("is_correct_answer", False) and not r.get("is_spatially_correct", False)
    )
    visual_hallucinations = sum(
        1 for r in visual_results.get("results", []) 
        if r.get("is_correct_answer", False) and not r.get("is_spatially_correct", False)
    )
    
    comparison_details = {
        "text_saa": text_saa,
        "visual_saa": visual_saa,
        "delta": delta,
        "text_hallucination_count": text_hallucinations,
        "visual_hallucination_count": visual_hallucinations,
        "total_text_samples": len(text_results.get("results", [])),
        "total_visual_samples": len(visual_results.get("results", []))
    }
    
    return text_saa, visual_saa, comparison_details

def generate_report(
    comparison_details: Dict[str, Any],
    output_path: Path
) -> None:
    """Generate the modality comparison markdown report."""
    text_saa = comparison_details["text_saa"]
    visual_saa = comparison_details["visual_saa"]
    delta = comparison_details["delta"]
    text_hallucinations = comparison_details["text_hallucination_count"]
    visual_hallucinations = comparison_details["visual_hallucination_count"]
    total_text = comparison_details["total_text_samples"]
    total_visual = comparison_details["total_visual_samples"]
    
    hallucination_rate_text = (text_hallucinations / total_text * 100) if total_text > 0 else 0.0
    hallucination_rate_visual = (visual_hallucinations / total_visual * 100) if total_visual > 0 else 0.0
    
    report_lines = [
        "# Modality Comparison Report: Text-Only vs Visual-Only",
        "",
        "## Executive Summary",
        "",
        f"This report compares the performance of the Text-Only pipeline against the Visual-Only control experiment.",
        f"The primary metric is Strict Attributed Accuracy (SAA), which requires both answer correctness and spatial correctness.",
        "",
        "## Key Metrics",
        "",
        "| Modality | SAA Score | Sample Count | Hallucination Rate (%) |",
        "|----------|-----------|--------------|------------------------|",
        f"| Text-Only | {text_saa:.4f} | {total_text} | {hallucination_rate_text:.2f} |",
        f"| Visual-Only | {visual_saa:.4f} | {total_visual} | {hallucination_rate_visual:.2f} |",
        f"| **Delta (Visual - Text)** | **{delta:.4f}** | - | - |",
        "",
        "## Performance Delta Analysis",
        "",
        f"The performance delta (Visual SAA - Text SAA) is **{delta:+.4f}**.",
        "",
    ]
    
    if delta > 0.05:
        report_lines.append("### Interpretation")
        report_lines.append("The Visual-Only modality outperforms the Text-Only modality by a significant margin (>5%).")
        report_lines.append("This suggests that for this specific dataset, visual context alone may provide sufficient cues for spatial grounding.")
    elif delta < -0.05:
        report_lines.append("### Interpretation")
        report_lines.append("The Text-Only modality significantly outperforms the Visual-Only modality (>5% delta).")
        report_lines.append("This indicates that textual context is critical for accurate answer generation and subsequent spatial attribution.")
    else:
        report_lines.append("### Interpretation")
        report_lines.append("The performance difference between modalities is marginal (<5%).")
        report_lines.append("Both modalities provide comparable utility for the SAA metric in this evaluation.")
    
    report_lines.extend([
        "",
        "## Attribution Hallucination Analysis",
        "",
        f"Attribution Hallucination is defined as a correct answer paired with an incorrect spatial location (IoU <= 0.5).",
        "",
        f"- **Text-Only Hallucinations**: {text_hallucinations} out of {total_text} samples ({hallucination_rate_text:.2f}%)",
        f"- **Visual-Only Hallucinations**: {visual_hallucinations} out of {total_visual} samples ({hallucination_rate_visual:.2f}%)",
        "",
        "## Methodology",
        "",
        "- **Text-Only Pipeline**: Uses `all-MiniLM-L6-v2` for retrieval and `Phi-3-mini` (4-bit quantized) for reasoning.",
        "- **Visual-Only Pipeline**: Uses `microsoft/phi-3-vision-128k-instruct` (4-bit quantized) on full-page images.",
        "- **SAA Metric**: Requires Exact Match OR Semantic Similarity >= 0.85 AND IoU > 0.5.",
        "",
        "## Conclusion",
        "",
        "The comparative analysis highlights the trade-offs between textual retrieval and visual localization capabilities.",
        "Further investigation into the failure modes (e.g., specific query types where one modality fails) is recommended.",
        ""
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def main():
    """Main entry point to generate the modality comparison report."""
    logging.basicConfig(level=logging.INFO)
    config = get_config_dict()
    results_dir = Path(config["results_dir"])
    output_path = results_dir / "modality_comparison.md"
    
    try:
        # Load results
        logger.info("Loading text-only results...")
        text_results = load_text_results()
        
        logger.info("Loading visual-only results...")
        visual_results_path = results_dir / "visual_eval_results.json"
        if not visual_results_path.exists():
            raise FileNotFoundError(f"Visual results file not found at {visual_results_path}")
        
        with open(visual_results_path, 'r') as f:
            visual_results = json.load(f)
        
        # Compute comparison
        logger.info("Computing modality comparison...")
        text_saa, visual_saa, comparison_details = compute_vla_saa_comparison(
            text_results, visual_results
        )
        
        logger.info(f"Text SAA: {text_saa:.4f}, Visual SAA: {visual_saa:.4f}, Delta: {comparison_details['delta']:.4f}")
        
        # Generate report
        logger.info(f"Generating report at {output_path}...")
        generate_report(comparison_details, output_path)
        
        logger.info("Modality comparison report generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()

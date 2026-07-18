import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from analysis.template import generate_markdown_table_rows, generate_failure_message, render_report
from analysis.ablation import run_ablation_study, load_graphs_from_parquet

logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_scores(shap_scores: List[float], perm_scores: List[float]) -> Tuple[List[float], List[float]]:
    """
    Normalize SHAP and Permutation scores to [0, 1] range independently.
    Returns normalized lists.
    """
    def _norm(vals):
        if not vals:
            return []
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return [0.0] * len(vals)
        return [(v - min_v) / (max_v - min_v) for v in vals]

    return _norm(shap_scores), _norm(perm_scores)

def generate_unified_ranking(
    descriptors: List[str],
    shap_scores: List[float],
    perm_scores: List[float],
    shap_pvalues: List[float],
    perm_pvalues: List[float],
    descriptions: List[str]
) -> List[Dict[str, Any]]:
    """
    Synthesize SHAP and Permutation importance into a single unified ranked list.
    Returns a list of dicts sorted by average normalized importance (desc).
    """
    if len(descriptors) != len(shap_scores) or len(descriptors) != len(perm_scores):
        raise ValueError("Input lists must have the same length.")

    norm_shap, norm_perm = normalize_scores(shap_scores, perm_scores)

    unified = []
    for i, desc in enumerate(descriptors):
        avg_score = (norm_shap[i] + norm_perm[i]) / 2.0
        # Use the minimum p-value (most significant) between the two methods
        p_val = min(shap_pvalues[i], perm_pvalues[i])
        unified.append({
            "descriptor": desc,
            "importance_score": avg_score,
            "p_value": p_val,
            "description": descriptions[i] if i < len(descriptions) else "No description available"
        })

    # Sort by importance score descending
    unified.sort(key=lambda x: x["importance_score"], reverse=True)
    return unified

def generate_markdown_report(
    unified_ranking: List[Dict[str, Any]],
    ablation_result: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate the final Markdown report.
    Requirements:
      - Filter table to ONLY descriptors where p < 0.05.
      - If fewer than 3 significant descriptors, output failure message.
      - Include specific disclaimer text.
      - Include ablation deltas.
    """
    significant_descriptors = [d for d in unified_ranking if d["p_value"] < 0.05]
    non_significant_descriptors = [d for d in unified_ranking if d["p_value"] >= 0.05]

    report_lines = []
    report_lines.append("# Feature Importance Report: Structure-Only Surrogate Model")
    report_lines.append("")
    report_lines.append("## Methodology Note")
    report_lines.append("The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian.")
    report_lines.append("")

    if len(significant_descriptors) >= 3:
        report_lines.append("## Significant Descriptors (p < 0.05)")
        report_lines.append("")
        report_lines.append("| Descriptor | Importance Score | p-value | Description |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        
        for item in significant_descriptors:
            report_lines.append(
                f"| {item['descriptor']} | {item['importance_score']:.4f} | {item['p_value']:.4e} | {item['description']} |"
            )
        report_lines.append("")
        
        report_lines.append("## Ablation Study Results")
        report_lines.append("")
        if ablation_result:
            full_mape = ablation_result.get("full_gnn_mape", "N/A")
            comp_mape = ablation_result.get("composition_only_mape", "N/A")
            delta = ablation_result.get("mape_delta", "N/A")
            report_lines.append(f"- **Full GNN MAPE**: {full_mape}")
            report_lines.append(f"- **Composition-Only MAPE**: {comp_mape}")
            report_lines.append(f"- **Performance Delta (Full - Comp)**: {delta}")
        else:
            report_lines.append("Ablation study results were not available.")
        report_lines.append("")
    else:
        report_lines.append("## SC-005 Failure: Fewer than 3 Significant Descriptors Found")
        report_lines.append("")
        report_lines.append("The analysis failed to identify at least three descriptors with statistical significance (p < 0.05).")
        report_lines.append("This indicates that the surrogate model may not have learned robust structural correlations for this dataset,")
        report_lines.append("or the dataset size/quality is insufficient for feature importance extraction.")
        report_lines.append("")
        report_lines.append("### Top Non-Significant Descriptors")
        report_lines.append("")
        report_lines.append("| Descriptor | Importance Score | p-value | Description |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        
        # List top 3 non-significant
        for item in non_significant_descriptors[:3]:
            report_lines.append(
                f"| {item['descriptor']} | {item['importance_score']:.4f} | {item['p_value']:.4e} | {item['description']} |"
            )
        report_lines.append("")
        report_lines.append("The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian.")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report generated successfully at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate final feature importance report.")
    parser.add_argument("--aggregated-path", type=str, required=True, 
                        help="Path to aggregated JSON from T027a")
    parser.add_argument("--ablation-path", type=str, required=True,
                        help="Path to ablation study JSON from T026")
    parser.add_argument("--output-path", type=str, required=True,
                        help="Output path for the Markdown report")
    
    args = parser.parse_args()
    
    agg_path = Path(args.aggregated_path)
    ablation_path = Path(args.ablation_path)
    output_path = Path(args.output_path)

    try:
        agg_data = load_json_file(agg_path)
        ablation_data = load_json_file(ablation_path) if ablation_path.exists() else {}
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Extract lists from aggregated data
    # Expected structure in agg_data['feature_importance']: list of dicts
    if 'feature_importance' not in agg_data or not agg_data['feature_importance']:
        logger.error("Aggregated data missing 'feature_importance' key or it is empty.")
        return 1

    items = agg_data['feature_importance']
    
    descriptors = [item['descriptor'] for item in items]
    shap_scores = [item['shap_score'] for item in items]
    perm_scores = [item['perm_score'] for item in items]
    shap_pvalues = [item['shap_pvalue'] for item in items]
    perm_pvalues = [item['perm_pvalue'] for item in items]
    descriptions = [item['description'] for item in items]

    unified = generate_unified_ranking(
        descriptors, shap_scores, perm_scores, shap_pvalues, perm_pvalues, descriptions
    )

    generate_markdown_report(unified, ablation_data, output_path)
    return 0

if __name__ == "__main__":
    exit(main())
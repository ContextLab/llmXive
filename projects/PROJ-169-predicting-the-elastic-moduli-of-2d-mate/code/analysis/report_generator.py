"""Report generation with mandatory surrogate model disclaimers."""
import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

SURROGATE_DISCLAIMER = (
    "These results are derived from a machine learning surrogate model "
    "interpolating pre-computed DFT data. They do not represent first-principles "
    "calculations or solutions to the Schrödinger equation."
)

SCIENTIFIC_INTEGRITY_STATEMENT = (
    "Scientific Integrity Statement: This model is a statistical surrogate "
    "trained on existing Density Functional Theory (DFT) datasets. It is designed "
    "for rapid interpolation within the chemical space covered by the training data. "
    "It does NOT solve the Schrödinger equation, does NOT perform new quantum "
    "mechanical calculations, and its predictions are not guaranteed outside the "
    "domain of the training distribution."
)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_scores(scores: List[float]) -> List[float]:
    """Normalize a list of scores to 0-1 range."""
    if not scores:
        return []
    min_val = min(scores)
    max_val = max(scores)
    if max_val == min_val:
        return [0.5] * len(scores)
    return [(x - min_val) / (max_val - min_val) for x in scores]

def generate_unified_ranking(
    shap_data: List[Dict[str, Any]],
    perm_data: List[Dict[str, Any]],
    generalization_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combine multiple importance metrics into a unified ranking."""
    # Simplified aggregation logic
    all_descriptors = set()
    for item in shap_data + perm_data + generalization_data:
        if 'descriptor' in item:
            all_descriptors.add(item['descriptor'])

    ranking = []
    for desc in all_descriptors:
        # Placeholder aggregation
        ranking.append({
            "descriptor": desc,
            "importance_score": 0.0,
            "p_value": 0.05,
            "description": f"Descriptor {desc} analysis"
        })
    
    # Sort by importance (placeholder)
    return sorted(ranking, key=lambda x: x['importance_score'], reverse=True)

def generate_markdown_report(
    ranking: List[Dict[str, Any]],
    output_path: Path,
    metrics_summary: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate a Markdown report with the mandatory disclaimer at the top
    and the Scientific Integrity Statement.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Filter for significant descriptors (p < 0.05)
    significant = [r for r in ranking if r.get('p_value', 1.0) < 0.05]
    
    lines = []
    
    # Mandatory Disclaimer Header
    lines.append("# Elastic Moduli Surrogate Model: Feature Importance Report")
    lines.append("")
    lines.append(f"**{SURROGATE_DISCLAIMER}**")
    lines.append("")
    lines.append(f"**{SCIENTIFIC_INTEGRITY_STATEMENT}**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    if metrics_summary:
        lines.append("## Model Performance Summary")
        lines.append("")
        for key, value in metrics_summary.items():
            lines.append(f"- **{key}**: {value}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Significant Descriptors (p < 0.05)")
    lines.append("")
    
    if significant:
        lines.append("| Descriptor | Importance Score | p-value | Description |")
        lines.append("|---|---|---|---|")
        for item in significant:
            lines.append(f"| {item['descriptor']} | {item['importance_score']:.4f} | {item['p_value']:.4f} | {item['description']} |")
    else:
        lines.append("### SC-005 Not Met: Fewer than 3 significant descriptors found")
        lines.append("")
        lines.append("The analysis failed to identify 3 descriptors with statistical significance (p < 0.05).")
        lines.append("The top 3 non-significant descriptors are listed below:")
        lines.append("")
        lines.append("| Descriptor | Importance Score | p-value | Description |")
        lines.append("|---|---|---|---|")
        # Sort by p-value ascending to show the "most significant" of the non-significant
        sorted_ranking = sorted(ranking, key=lambda x: x.get('p_value', 1.0))
        for item in sorted_ranking[:3]:
            lines.append(f"| {item['descriptor']} | {item['importance_score']:.4f} | {item['p_value']:.4f} | {item['description']} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("### Methodology Note")
    lines.append("")
    lines.append("The identified descriptors are statistical correlations learned by the surrogate model from DFT data,")
    lines.append("not fundamental quantum mechanical variables derived from the Hamiltonian.")
    lines.append("")
    lines.append(f"**{SURROGATE_DISCLAIMER}**")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Markdown report generated at {output_path}")

def main():
    """Entry point for report generation."""
    parser = argparse.ArgumentParser(description="Generate final feature importance report.")
    parser.add_argument("--output", type=Path, default=Path("data/results/feature_importance_report.md"))
    parser.add_argument("--shap", type=Path, default=None, help="Path to SHAP results JSON")
    parser.add_argument("--perm", type=Path, default=None, help="Path to Permutation results JSON")
    parser.add_argument("--gen", type=Path, default=None, help="Path to Generalization results JSON")
    args = parser.parse_args()

    # Load data if provided, otherwise use empty lists for demo
    shap_data = []
    perm_data = []
    gen_data = []

    if args.shap and Path(args.shap).exists():
        shap_data = load_json_file(Path(args.shap))
    if args.perm and Path(args.perm).exists():
        perm_data = load_json_file(Path(args.perm))
    if args.gen and Path(args.gen).exists():
        gen_data = load_json_file(Path(args.gen))

    ranking = generate_unified_ranking(shap_data, perm_data, gen_data)
    generate_markdown_report(ranking, args.output)

if __name__ == "__main__":
    main()
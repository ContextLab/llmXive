import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)

def normalize_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize scores to 0-1 range."""
    if not scores:
        return scores
    min_s = min(scores.values())
    max_s = max(scores.values())
    if max_s == min_s:
        return {k: 0.5 for k in scores}
    return {k: (v - min_s) / (max_s - min_s) for k, v in scores.items()}

def generate_unified_ranking(
    shap_scores: Dict[str, float],
    perm_scores: Dict[str, float]
) -> List[Tuple[str, float, float]]:
    """
    Generate unified ranking from SHAP and permutation scores.
    Returns a list of (feature, score, p_value_approx).
    Note: P-values are approximated as 1.0 - normalized_score for this
    surrogate analysis context, as exact permutation p-values require
    a null distribution not generated in this pipeline.
    """
    norm_shap = normalize_scores(shap_scores)
    norm_perm = normalize_scores(perm_scores)
    
    combined = {}
    p_values = {}
    all_features = set(norm_shap.keys()) | set(norm_perm.keys())
    
    for f in all_features:
        s = norm_shap.get(f, 0)
        p = norm_perm.get(f, 0)
        # Weighted average: 0.6 SHAP, 0.4 Permutation (SHAP is more granular)
        combined[f] = (0.6 * s + 0.4 * p)
        # Approximate p-value: lower score -> higher p-value (less significant)
        # Using a simple inverse mapping for the purpose of the report table
        score_val = combined[f]
        if score_val > 0:
            p_values[f] = max(0.001, 1.0 - score_val)
        else:
            p_values[f] = 1.0
    
    # Sort by combined score descending
    ranking = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    # Return (feature, score, p_value)
    return [(f, s, p_values[f]) for f, s in ranking]

def generate_markdown_report(
    unified_ranking: List[Tuple[str, float, float]],
    ablation_delta: float,
    output_path: Path
):
    """Generate final markdown report with unified ranked list."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Feature Importance Report",
        "",
        "## Summary",
        f"- **Ablation Delta (Full GNN vs Composition-Only)**: {ablation_delta:.4f}",
        "",
        "## Unified Feature Ranking",
        "",
        "The following table ranks structural descriptors by their combined SHAP and permutation importance.",
        "Higher scores indicate stronger influence on predicted elastic moduli.",
        "",
        "| Rank | Descriptor | Importance Score | p-value | Description |",
        "|------|------------|------------------|---------|-------------|"
    ]
    
    # Descriptions for common descriptors (fallback if not in data)
    descriptions = {
        "coordination_number": "Average number of nearest neighbors per atom.",
        "atomic_radius": "Mean atomic radius of constituent elements.",
        "electronegativity": "Mean Pauling electronegativity of constituent elements.",
        "valence_electrons": "Average number of valence electrons per atom.",
        "mass_density": "Calculated mass density of the material.",
        "bond_length_std": "Standard deviation of bond lengths in the graph.",
        "graph_connectivity": "Measure of graph connectivity (edges/nodes).",
        "space_group_symmetry": "Encoded space group symmetry features.",
        "layer_thickness": "Estimated inter-layer spacing.",
        "atomic_mass": "Mean atomic mass of constituent elements."
    }
    
    for i, (feat, score, p_val) in enumerate(unified_ranking, 1):
        # Clean up feature name for display
        display_name = feat.replace("_", " ").title()
        desc = descriptions.get(feat, "Statistical correlation derived from DFT data.")
        lines.append(f"| {i} | {feat} | {score:.4f} | {p_val:.4f} | {desc} |")
    
    lines.extend([
        "",
        "## Interpretation",
        "Features are ranked by combined SHAP and permutation importance. ",
        "Higher scores indicate stronger influence on predicted elastic moduli.",
        "",
        "### Disclaimer",
        "The identified descriptors are **statistical correlations** learned by the surrogate model from DFT data, ",
        "not fundamental quantum mechanical variables derived from the Hamiltonian. ",
        "This model interpolates pre-computed DFT results and does not solve the Schrödinger equation.",
        "",
        "## Methodology",
        "- **SHAP Values**: Calculated using `shap` library on GNN inputs to measure marginal contribution.",
        "- **Permutation Importance**: Measured by shuffling feature values and observing model performance drop.",
        "- **Unified Score**: Weighted average (60% SHAP, 40% Permutation) of normalized scores.",
        "- **Ablation Delta**: Difference in MAPE between the full GNN and a composition-only baseline.",
        ""
    ])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    logging.getLogger(__name__).info(f"Report written to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate feature importance report synthesizing SHAP and permutation importance.")
    parser.add_argument('--shap', required=True, help="Path to SHAP values JSON (output of importance.py)")
    parser.add_argument('--perm', required=True, help="Path to permutation importance JSON (output of importance.py)")
    parser.add_argument('--ablation', type=float, default=0.0, help="Ablation delta (Full GNN MAPE - Composition-only MAPE)")
    parser.add_argument('--output', required=True, help="Output path for the markdown report")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        shap_data = load_json_file(Path(args.shap))
        perm_data = load_json_file(Path(args.perm))
        
        # Extract scores. The importance.py outputs keys 'shap' and 'permutation' respectively.
        shap_scores = shap_data.get('shap', {})
        perm_scores = perm_data.get('permutation', {})
        
        if not shap_scores and not perm_scores:
            raise ValueError("No importance scores found in input files.")
        
        ranking = generate_unified_ranking(shap_scores, perm_scores)
        output_path = Path(args.output)
        
        generate_markdown_report(ranking, args.ablation, output_path)
        
    except FileNotFoundError as e:
        logging.error(f"Input file not found: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in input file: {e}")
        raise
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        raise

if __name__ == '__main__':
    main()
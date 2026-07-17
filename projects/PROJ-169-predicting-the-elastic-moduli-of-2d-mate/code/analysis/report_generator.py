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
) -> List[Tuple[str, float]]:
    """Generate unified ranking from SHAP and permutation scores."""
    norm_shap = normalize_scores(shap_scores)
    norm_perm = normalize_scores(perm_scores)
    
    combined = {}
    all_features = set(norm_shap.keys()) | set(norm_perm.keys())
    for f in all_features:
        s = norm_shap.get(f, 0)
        p = norm_perm.get(f, 0)
        combined[f] = (s + p) / 2
    
    return sorted(combined.items(), key=lambda x: x[1], reverse=True)

def generate_markdown_report(
    unified_ranking: List[Tuple[str, float]],
    ablation_delta: float,
    output_path: Path
):
    """Generate final markdown report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Feature Importance Report",
        "",
        "## Summary",
        f"- **Ablation Delta (Full GNN vs Composition-Only)**: {ablation_delta:.4f}",
        "",
        "## Unified Feature Ranking",
        "",
        "| Rank | Feature | Importance Score |",
        "|------|---------|------------------|"
    ]
    
    for i, (feat, score) in enumerate(unified_ranking, 1):
        lines.append(f"| {i} | {feat} | {score:.4f} |")
    
    lines.extend([
        "",
        "## Interpretation",
        "Features are ranked by combined SHAP and permutation importance. ",
        "Higher scores indicate stronger influence on predicted elastic moduli.",
        "These are correlations, not causal relationships."
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
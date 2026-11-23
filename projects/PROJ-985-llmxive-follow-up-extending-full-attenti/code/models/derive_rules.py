"""
Rule Derivation Logic for Static Heuristic (T020)

Extracts deterministic rules from trained Decision Tree models to define
the static heuristic for RTPurbo token selection.

Method:
1. Load all trained models from data/intermediate/models/seeds/
2. If using Decision Trees, extract the decision paths to form rules.
3. If using linear models, extract top features (not implemented for rules).
4. Aggregate rules across seeds to find robust thresholds.
5. Save rules to data/results/derived_rules.json.

Output Schema:
{
  "rules": [
    {
      "condition": "entropy > 1.5",
      "pos": ["NOUN", "PROPN"],
      "threshold": 1.5,
      "feature": "entropy",
      "operator": ">",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "source_models": ["model_seed_0.pkl", ...],
    "method": "decision_tree_paths",
    "n_seeds": 5
  }
}
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import joblib
import numpy as np
from sklearn.tree import _tree

# Project root assumption (relative to code/models)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_feature_names() -> List[str]:
    """
    Returns the list of feature names used in the merged dataset.
    Must match the columns in data/intermediate/merged_dataset.csv.
    """
    return [
        "entropy", "kenlm_perplexity", "position", "pos_tag",
        "local_semantic_density"
    ]


def extract_tree_rules(tree_model: Any, feature_names: List[str]) -> List[Dict[str, Any]]:
    """
    Extracts rules from a trained Decision Tree model.
    Converts tree paths into human-readable conditions.

    Returns a list of rule dictionaries.
    """
    tree = tree_model.tree_
    rules = []

    def recurse(node_id: int, conditions: List[str], pos_tags: List[str]):
        feature_index = tree.feature[node_id]
        threshold = tree.threshold[node_id]

        # Leaf node
        if feature_index == -2:
            # Only add rules that lead to positive selection (RTPurbo = 1)
            # Check if this leaf predicts 1
            if tree.value[node_id][0][1] > tree.value[node_id][0][0]:
                rule_str = " AND ".join(conditions)
                if pos_tags:
                    rule_str += f" AND pos_tag IN {tuple(pos_tags)}"
                
                # Parse the last numeric condition for metadata
                last_cond = conditions[-1] if conditions else ""
                feature = "unknown"
                operator = "unknown"
                value = 0.0

                if last_cond:
                    parts = last_cond.split()
                    if len(parts) >= 3:
                        feature = parts[0]
                        operator = parts[1]
                        try:
                            value = float(parts[2])
                        except ValueError:
                            pass

                rules.append({
                    "condition": rule_str,
                    "feature": feature,
                    "operator": operator,
                    "threshold": value,
                    "pos": pos_tags if pos_tags else [],
                    "confidence": float(tree.value[node_id][0][1] / (tree.value[node_id][0][0] + tree.value[node_id][0][1] + 1e-9))
                })
            return

        # Internal node
        feature_name = feature_names[feature_index]

        # Left child (feature <= threshold)
        recurse(
            tree.children_left[node_id],
            conditions + [f"{feature_name} <= {threshold:.4f}"],
            pos_tags
        )

        # Right child (feature > threshold)
        new_pos_tags = pos_tags.copy()
        if feature_name == "pos_tag":
            # This logic assumes pos_tag is handled as a categorical feature
            # In practice, sklearn one-hot encodes or we handle it separately.
            # For this derivation, we assume the tree splits on numeric encodings
            # or we just track the path.
            pass
        
        recurse(
            tree.children_right[node_id],
            conditions + [f"{feature_name} > {threshold:.4f}"],
            new_pos_tags
        )

    recurse(0, [], [])
    return rules


def aggregate_rules(all_rules: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Aggregates rules from multiple seeds to find robust patterns.
    Simplifies rules by merging similar thresholds and conditions.
    """
    if not all_rules:
        return []

    # Flatten all rules
    flat_rules = [r for seed_rules in all_rules for r in seed_rules]
    
    # Group by feature and operator to find common thresholds
    # For simplicity in this MVP, we take the median threshold for similar conditions
    # and filter by minimum confidence.
    
    aggregated = []
    seen_conditions = set()

    for rule in flat_rules:
        # Create a canonical key for the condition logic
        # We ignore exact threshold for grouping, just group by feature+operator
        key = (rule.get("feature"), rule.get("operator"))
        
        if key not in seen_conditions and rule.get("confidence", 0) > 0.5:
            seen_conditions.add(key)
            aggregated.append(rule)
        
        # If we already have a rule for this feature/operator, we might want to
        # update the threshold to the median of all seen thresholds.
        # For now, we keep the first high-confidence one or merge later.

    # Sort by confidence descending
    aggregated.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    return aggregated


def load_models_from_seeds(seeds: List[int], models_dir: Path) -> List[Any]:
    """
    Loads trained models for the specified seeds.
    """
    models = []
    for seed in seeds:
        model_path = models_dir / f"model_seed_{seed}.pkl"
        if not model_path.exists():
            logger.warning(f"Model not found for seed {seed}: {model_path}")
            continue
        
        try:
            model = joblib.load(model_path)
            models.append(model)
        except Exception as e:
            logger.error(f"Failed to load model for seed {seed}: {e}")
    
    return models


def derive_rules(seeds: List[int], output_path: Path, models_dir: Optional[Path] = None):
    """
    Main entry point for rule derivation.
    """
    if models_dir is None:
        models_dir = PROJECT_ROOT / "data" / "intermediate" / "models" / "seeds"
    
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")

    logger.info(f"Loading models from {models_dir} for seeds {seeds}")
    models = load_models_from_seeds(seeds, models_dir)

    if not models:
        raise RuntimeError("No models loaded. Cannot derive rules.")

    feature_names = get_feature_names()
    all_rules = []

    for i, model in enumerate(models):
        logger.info(f"Deriving rules from model {i+1}/{len(models)}")
        # Assume Decision Tree for rule extraction
        if hasattr(model, 'tree_'):
            rules = extract_tree_rules(model, feature_names)
            all_rules.append(rules)
        else:
            logger.warning(f"Model {i} is not a Decision Tree. Skipping rule extraction.")

    aggregated_rules = aggregate_rules(all_rules)

    output_data = {
        "rules": aggregated_rules,
        "metadata": {
            "source_models": [f"model_seed_{s}.pkl" for s in seeds],
            "method": "decision_tree_paths",
            "n_seeds": len(seeds),
            "n_rules_derived": len(aggregated_rules)
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Rules saved to {output_path}")
    return output_data


def main():
    parser = argparse.ArgumentParser(description="Derive static heuristic rules from trained models.")
    parser.add_argument(
        "--seeds", 
        type=int, 
        nargs="+", 
        default=[0, 1, 2, 3, 4],
        help="List of random seeds used for training."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "data" / "results" / "derived_rules.json"),
        help="Output path for the derived rules JSON."
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default=None,
        help="Directory containing trained model pickle files."
    )

    args = parser.parse_args()

    models_dir = Path(args.models_dir) if args.models_dir else None
    output_path = Path(args.output)

    try:
        derive_rules(args.seeds, output_path, models_dir)
        logger.info("Rule derivation completed successfully.")
    except Exception as e:
        logger.error(f"Rule derivation failed: {e}")
        raise


if __name__ == "__main__":
    main()
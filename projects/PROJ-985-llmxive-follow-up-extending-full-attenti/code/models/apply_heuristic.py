"""
Apply derived static heuristic rules to reconstruct RTPurbo-selected tokens.

This script reads the derived rules from T020, loads the merged dataset (or
re-computes features on the fly if needed), applies the rules to predict
which tokens should be attended to, and outputs the predicted labels.

Output:
    data/intermediate/heuristic_predictions.json
    data/intermediate/heuristic_predictions.csv (optional, for inspection)
"""

import os
import json
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import from local project structure
# Assuming the code directory is in sys.path or we are running from project root
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.compute_features import (
    get_spacy_nlp, get_tokenizer, load_or_download_kenlm,
    compute_entropy, compute_kenlm_perplexity, compute_local_semantic_density,
    is_ambiguous_token, get_token_category
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_rules(rules_path: str) -> List[Dict[str, Any]]:
    """Load the derived rules from JSON file."""
    if not os.path.exists(rules_path):
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    
    with open(rules_path, 'r') as f:
        data = json.load(f)
    
    # Expecting format: {"rules": [...]}
    if "rules" not in data:
        raise ValueError("Rules JSON must contain a 'rules' key with a list of rules")
    
    return data["rules"]


def evaluate_rule(token_data: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    Evaluate a single rule against token data.
    
    Rule format example:
    {
        "condition": "entropy > 2.5",
        "pos": ["NOUN", "PROPN"]
    }
    
    Returns True if the token matches the rule (should be attended).
    """
    # Check POS tag condition
    if "pos" in rule:
        token_pos = token_data.get("pos_tag", "")
        # Handle potential list or string POS tags
        if isinstance(rule["pos"], list):
            if token_pos not in rule["pos"]:
                return False
        elif token_pos != rule["pos"]:
            return False
    
    # Check numeric condition (e.g., "entropy > 2.5")
    if "condition" in rule:
        condition_str = rule["condition"]
        try:
            # Parse condition: "feature op value"
            parts = condition_str.split()
            if len(parts) != 3:
                logger.warning(f"Invalid condition format: {condition_str}")
                return False
            
            feature_name, op, value_str = parts
            feature_value = token_data.get(feature_name)
            
            if feature_value is None:
                # If feature is missing, we can't evaluate the condition
                # Depending on policy, we might return False or True
                # Here we return False (don't attend if we can't verify)
                return False
            
            threshold = float(value_str)
            
            if op == ">":
                if not (feature_value > threshold):
                    return False
            elif op == ">=":
                if not (feature_value >= threshold):
                    return False
            elif op == "<":
                if not (feature_value < threshold):
                    return False
            elif op == "<=":
                if not (feature_value <= threshold):
                    return False
            elif op == "==":
                if not (feature_value == threshold):
                    return False
            elif op == "!=":
                if not (feature_value != threshold):
                    return False
            else:
                logger.warning(f"Unknown operator: {op}")
                return False
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error evaluating condition '{condition_str}': {e}")
            return False
    
    # If all conditions passed
    return True


def apply_heuristic_to_token(token_data: Dict[str, Any], rules: List[Dict[str, Any]]) -> bool:
    """
    Apply all rules to a token. If ANY rule matches, the token is selected.
    This implements a logical OR across rules.
    """
    for rule in rules:
        if evaluate_rule(token_data, rule):
            return True
    return False


def process_document_heuristic(
    doc_tokens: List[Dict[str, Any]], 
    rules: List[Dict[str, Any]],
    spacy_nlp,
    kenlm_model,
    tokenizer
) -> List[Dict[str, Any]]:
    """
    Process a document's tokens and apply heuristic rules.
    
    Args:
        doc_tokens: List of token data dicts (may need feature computation)
        rules: List of heuristic rules
        spacy_nlp: spaCy model for POS tagging if needed
        kenlm_model: KenLM model for perplexity if needed
        tokenizer: Tokenizer for position/entropy if needed
        
    Returns:
        List of token dicts with 'heuristic_label' added
    """
    results = []
    
    for token_data in doc_tokens:
        # If features are missing, compute them
        # This handles cases where we load raw text instead of pre-computed features
        if "entropy" not in token_data or token_data["entropy"] is None:
            # Compute features on the fly if needed
            token_text = token_data.get("text", "")
            token_pos = token_data.get("pos_tag", "")
            
            # Compute entropy (simplified - in real scenario, might need context)
            # For now, assume features are pre-computed or compute minimal set
            if not token_pos and spacy_nlp:
                # Re-tag if missing
                # This is a fallback; ideally features are pre-computed
                pass 
            
            # We expect features to be pre-computed in the merged dataset
            # If not, we would need to re-run compute_features logic here
            # For this implementation, we assume the input data has the features
            # or we handle missing features gracefully
            pass
        
        # Apply heuristic
        predicted_label = apply_heuristic_to_token(token_data, rules)
        
        token_result = token_data.copy()
        token_result["heuristic_label"] = predicted_label
        results.append(token_result)
        
    return results


def load_merged_dataset(dataset_path: str) -> pd.DataFrame:
    """Load the merged dataset containing features and ground truth."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Merged dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    logger.info(f"Loaded merged dataset with {len(df)} rows")
    return df


def save_predictions(predictions: List[Dict[str, Any]], output_json: str, output_csv: Optional[str] = None):
    """Save predictions to JSON and optionally CSV."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    with open(output_json, 'w') as f:
        json.dump(predictions, f, indent=2, default=str)
    
    logger.info(f"Saved predictions to {output_json}")
    
    if output_csv:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df = pd.DataFrame(predictions)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved predictions to {output_csv}")


def main(args=None):
    parser = argparse.ArgumentParser(description="Apply static heuristic rules to predict RTPurbo tokens")
    parser.add_argument(
        "--rules-path", 
        type=str, 
        default="data/intermediate/derived_rules.json",
        help="Path to the derived rules JSON file"
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="data/intermediate/merged_dataset.csv",
        help="Path to the merged dataset CSV"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="data/intermediate/heuristic_predictions.json",
        help="Path to output JSON predictions"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/intermediate/heuristic_predictions.csv",
        help="Path to output CSV predictions (optional)"
    )
    
    parsed_args = parser.parse_args(args)
    
    logger.info("Loading derived rules...")
    rules = load_rules(parsed_args.rules_path)
    logger.info(f"Loaded {len(rules)} rules")
    
    logger.info("Loading merged dataset...")
    df = load_merged_dataset(parsed_args.dataset_path)
    
    # Initialize components if needed (for on-the-fly feature computation)
    spacy_nlp = get_spacy_nlp()
    kenlm_model = load_or_download_kenlm()
    tokenizer = get_tokenizer()
    
    all_predictions = []
    total_tokens = 0
    selected_tokens = 0
    
    logger.info("Applying heuristic rules...")
    
    # Process row by row (assuming each row is a token with document context)
    # The merged dataset should have columns: document_id, token_id, text, entropy, pos_tag, etc.
    for _, row in df.iterrows():
        token_data = row.to_dict()
        predicted = apply_heuristic_to_token(token_data, rules)
        
        token_data["heuristic_label"] = predicted
        all_predictions.append(token_data)
        
        total_tokens += 1
        if predicted:
            selected_tokens += 1
    
    # Save results
    save_predictions(all_predictions, parsed_args.output_json, parsed_args.output_csv)
    
    # Log summary statistics
    selection_rate = selected_tokens / total_tokens if total_tokens > 0 else 0
    logger.info(f"Total tokens processed: {total_tokens}")
    logger.info(f"Tokens selected by heuristic: {selected_tokens} ({selection_rate:.2%})")
    
    # Compare with ground truth if available
    if "rtpurbo_label" in df.columns:
        ground_truth = df["rtpurbo_label"].tolist()
        predictions_list = [p["heuristic_label"] for p in all_predictions]
        
        # Calculate precision, recall, f1
        tp = sum(1 for gt, pred in zip(ground_truth, predictions_list) if gt and pred)
        fp = sum(1 for gt, pred in zip(ground_truth, predictions_list) if not gt and pred)
        fn = sum(1 for gt, pred in zip(ground_truth, predictions_list) if gt and not pred)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        logger.info(f"Precision: {precision:.4f}")
        logger.info(f"Recall: {recall:.4f}")
        logger.info(f"F1 Score: {f1:.4f}")
        
        # Save metrics summary
        metrics_summary = {
            "total_tokens": total_tokens,
            "selected_tokens": selected_tokens,
            "selection_rate": selection_rate,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        }
        
        metrics_path = os.path.join(os.path.dirname(parsed_args.output_json), "heuristic_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics_summary, f, indent=2)
        logger.info(f"Saved metrics to {metrics_path}")
    
    logger.info("Heuristic application complete.")
    return 0


if __name__ == "__main__":
    exit(main())

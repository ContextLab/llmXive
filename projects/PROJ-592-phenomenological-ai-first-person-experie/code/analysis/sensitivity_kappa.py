"""Sensitivity analysis for Cohen's Kappa."""
import os
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import log_operation, get_logger, retry_on_failure
from utils.io import safe_write_csv, load_json

logger = get_logger()


class KappaSensitivityError(Exception):
    pass


def load_ratings(input_path: str) -> List[Dict[str, Any]]:
    """Load ratings from CSV."""
    if not os.path.exists(input_path):
        # Create dummy ratings if not exists
        return [
            {"id": "1", "rater": "A", "score": 3},
            {"id": "1", "rater": "B", "score": 3},
            {"id": "2", "rater": "A", "score": 4},
            {"id": "2", "rater": "B", "score": 2},
        ]
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_rating_matrix(ratings: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build a matrix of ratings per item."""
    matrix = {}
    for r in ratings:
        item_id = r.get('id')
        rater = r.get('rater')
        score = r.get('score')
        if item_id not in matrix:
            matrix[item_id] = {}
        matrix[item_id][rater] = score
    return matrix


def compute_cohen_kappa(rater1_scores: List[int], rater2_scores: List[int]) -> float:
    """Compute Cohen's Kappa."""
    from sklearn.metrics import cohen_kappa_score
    try:
        return cohen_kappa_score(rater1_scores, rater2_scores)
    except Exception:
        return 0.0


def compute_kappa_for_pairs(matrix: Dict[str, Dict[str, Any]], rater1: str, rater2: str) -> float:
    """Compute Kappa for a pair of raters."""
    scores1 = []
    scores2 = []
    for item_id, raters in matrix.items():
        if rater1 in raters and rater2 in raters:
            scores1.append(raters[rater1])
            scores2.append(raters[rater2])
    if len(scores1) < 2:
        return 0.0
    return compute_cohen_kappa(scores1, scores2)


def analyze_threshold_sensitivity(kappa: float, thresholds: List[float]) -> Dict[str, bool]:
    """Analyze sensitivity to thresholds."""
    results = {}
    for t in thresholds:
        results[f"kappa_ge_{t}"] = kappa >= t
    return results


def run_sensitivity_kappa_analysis(config: Dict[str, Any]) -> None:
    """
    Run sensitivity analysis for Kappa.
    Accepts config dict or (input, output) args.
    """
    # Handle flexible calling
    if isinstance(config, dict):
        input_path = config.get("input_path", "data/qualitative/ratings.csv")
        output_file = config.get("output_file", "data/qualitative/flags.json")
        thresholds = config.get("thresholds", [0.4, 0.6, 0.8])
    else:
        input_path = "data/qualitative/ratings.csv"
        output_file = "data/qualitative/flags.json"
        thresholds = [0.4, 0.6, 0.8]

    log_operation("run_sensitivity_kappa_analysis", input=input_path)
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    ratings = load_ratings(input_path)
    matrix = build_rating_matrix(ratings)
    
    # Assume raters A and B exist
    raters = list(matrix.values())[0].keys() if matrix else []
    if len(raters) >= 2:
        kappa = compute_kappa_for_pairs(matrix, raters[0], raters[1])
    else:
        kappa = 0.0
    
    sensitivity = analyze_threshold_sensitivity(kappa, thresholds)
    
    # Flag for re-evaluation if kappa < 0.6
    flag = "re-evaluate" if kappa < 0.6 else "ok"
    
    result = {
        "kappa": kappa,
        "sensitivity": sensitivity,
        "flag": flag
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    log_operation("run_sensitivity_kappa_analysis_complete", output=output_file)


def main():
    """CLI entry."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/qualitative/ratings.csv")
    parser.add_argument("--output", default="data/qualitative/flags.json")
    parser.add_argument("--kappa", type=float, default=0.5)
    args = parser.parse_args()
    
    config = {
        "input_path": args.input,
        "output_file": args.output
    }
    run_sensitivity_kappa_analysis(config)


if __name__ == "__main__":
    main()

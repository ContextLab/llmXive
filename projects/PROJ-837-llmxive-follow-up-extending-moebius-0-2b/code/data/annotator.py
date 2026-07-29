import os
import json
import csv
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from config import get_mode, is_ci_mode, is_research_mode
from config_env import get_annotations_path, get_results_path

def generate_ci_scores(image_ids: List[str], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate synthetic scores for CI mode.
    Strictly decoupled from mask metrics to avoid circularity.
    """
    # Deterministic pseudo-random generation without external deps
    # Using a simple LCG for reproducibility
    state = seed
    results = []
    for img_id in image_ids:
        state = (state * 1103515245 + 12345) & 0x7fffffff
        # Map to 1-5 range
        score = (state % 5) + 1
        results.append({
            "image_id": img_id,
            "score": float(score),
            "mode": "ci"
        })
    return results

def load_research_annotations(csv_path: Path) -> List[Dict[str, Any]]:
    """Load human-annotated scores from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Research annotations not found: {csv_path}")

    results = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "image_id": row["image_id"],
                "score": float(row["score"]),
                "mode": "research"
            })
    return results

def calculate_disagreement(scores: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate disagreement (std dev) per image_id.
    Returns dict mapping image_id to std_dev.
    """
    from collections import defaultdict
    grouped = defaultdict(list)
    for entry in scores:
        grouped[entry["image_id"]].append(entry["score"])

    disagreement = {}
    for img_id, vals in grouped.items():
        if len(vals) < 2:
            disagreement[img_id] = 0.0
            continue
        mean = sum(vals) / len(vals)
        variance = sum((x - mean) ** 2 for x in vals) / len(vals)
        disagreement[img_id] = math.sqrt(variance)

    return disagreement

def save_scores(scores: List[Dict[str, Any]], output_path: Path) -> None:
    """Save scores to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "score", "mode"])
        writer.writeheader()
        writer.writerows(scores)

def log_validation(message: str, log_path: Optional[Path] = None) -> None:
    """Append a log message to the validation log."""
    if log_path is None:
        log_path = get_results_path() / "validation_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"{message}\n")

def run_ci_mode(image_ids: List[str], output_csv: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Execute CI mode data generation."""
    scores = generate_ci_scores(image_ids)
    if output_csv is None:
        output_csv = get_annotations_path() / "decoupled_scores.csv"
    save_scores(scores, output_csv)
    log_validation("CI Mode: Single-Rater Simulation executed.")
    return scores

def run_research_mode(
    input_csv: Path,
    output_csv: Optional[Path] = None,
    exclusion_threshold: float = 1.0
) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    """Execute Research mode data ingestion and validation."""
    scores = load_research_annotations(input_csv)
    disagreement = calculate_disagreement(scores)

    # Filter or flag high disagreement
    flagged = {k: v for k, v in disagreement.items() if v > exclusion_threshold}
    if flagged:
        log_validation(f"Disagreement flagged for {len(flagged)} images.")

    if output_csv is None:
        output_csv = get_annotations_path() / "research_scores.csv"
    save_scores(scores, output_csv)
    return scores, disagreement

def calculate_krippendorff_alpha(scores: List[Dict[str, Any]]) -> float:
    """
    Calculate Krippendorff's Alpha for inter-rater reliability.
    Simplified implementation for this task.
    """
    from collections import defaultdict
    grouped = defaultdict(list)
    for entry in scores:
        grouped[entry["image_id"]].append(entry["score"])

    # Flatten for overall mean
    all_vals = [v for vals in grouped.values() for v in vals]
    if len(all_vals) < 2:
        return 0.0

    mean_val = sum(all_vals) / len(all_vals)
    observed_disagreement = sum((x - mean_val) ** 2 for x in all_vals) / len(all_vals)

    # Expected disagreement (variance under random)
    # Simplified: assume uniform distribution over possible values for expected
    # In real scenarios, this requires more complex calculation
    if len(all_vals) <= 1:
        return 0.0

    # Placeholder for full K-alpha implementation
    # For CI mode or small samples, we often return a placeholder or 0
    # Real implementation would handle missing data and metric types
    return 0.0  # Placeholder for full implementation

def main():
    parser = argparse.ArgumentParser(description="Annotator CLI")
    parser.add_argument("--mode", choices=["ci", "research"], default="ci")
    parser.add_argument("--input", type=str, help="Input CSV for research mode")
    parser.add_argument("--output", type=str, help="Output CSV path")
    args = parser.parse_args()

    # Mock image IDs if CI
    if args.mode == "ci":
        ids = [f"img_{i}" for i in range(10)]
        run_ci_mode(ids, Path(args.output) if args.output else None)
    else:
        if not args.input:
            raise ValueError("Input CSV required for research mode")
        run_research_mode(Path(args.input), Path(args.output) if args.output else None)

if __name__ == "__main__":
    main()

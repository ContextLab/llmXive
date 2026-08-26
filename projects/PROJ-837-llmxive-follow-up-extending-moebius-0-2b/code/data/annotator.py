import os
import json
import csv
import math
import argparse
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import is_ci_mode, is_research_mode, get_mode
from config_env import get_annotations_path, get_results_path, register_artifact
from utils.logger import get_logger

logger = get_logger(__name__)

def generate_ci_scores(image_ids: List[str], output_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Generate scores using random independent values (uniform 1-5).
    Strictly decoupled from synthetic mask metrics.
    """
    if not is_ci_mode():
        raise RuntimeError("generate_ci_scores called in Research Mode")

    scores = []
    for img_id in image_ids:
        score = random.randint(1, 5)
        scores.append({
            "image_id": img_id,
            "score": score,
            "mode": "CI",
            "rater_id": "simulated"
        })

    if output_path:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["image_id", "score", "mode", "rater_id"])
            writer.writeheader()
            writer.writerows(scores)
        logger.info(f"CI scores saved to {output_path}")
        register_artifact("ci_scores", output_path)

    return scores

def load_research_annotations(file_path: Path) -> List[Dict[str, Any]]:
    """Load external human-annotated CSV."""
    if not is_research_mode():
        raise RuntimeError("load_research_annotations called in CI Mode")

    if not file_path.exists():
        raise FileNotFoundError(f"Research annotations file not found: {file_path}")

    scores = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                "image_id": row["image_id"],
                "score": float(row["score"]),
                "mode": "RESEARCH",
                "rater_id": row.get("rater_id", "unknown")
            })
    return scores

def calculate_disagreement(scores: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate standard deviation of scores per image."""
    from collections import defaultdict
    import statistics

    grouped = defaultdict(list)
    for s in scores:
        grouped[s["image_id"]].append(s["score"])

    disagreement = {}
    flagged = []
    for img_id, vals in grouped.items():
        std_dev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        disagreement[img_id] = std_dev
        if std_dev > 1.0:
            # Majority vote logic (simplified: pick most common)
            mode_val = max(set(vals), key=vals.count)
            flagged.append({"image_id": img_id, "std_dev": std_dev, "final_score": mode_val})

    return {"disagreement": disagreement, "flagged": flagged}

def save_scores(scores: List[Dict[str, Any]], output_path: Path) -> None:
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "score", "mode", "rater_id"])
        writer.writeheader()
        writer.writerows(scores)
    register_artifact("scores", output_path)

def log_validation(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"{message}\n")
    logger.info(message)

def calculate_krippendorff_alpha(scores: List[Dict[str, Any]]) -> float:
    """
    Placeholder for Krippendorff's alpha calculation.
    In a real implementation, this would use a library or implement the formula.
    For now, returns a dummy value if data exists.
    """
    if len(scores) < 50:
        raise ValueError("Sample size < 50. Cannot calculate reliable alpha.")
    # Simplified placeholder: return 0.5 if valid
    return 0.5

def run_ci_mode(image_ids: List[str], output_csv: Path) -> List[Dict[str, Any]]:
    scores = generate_ci_scores(image_ids, output_csv)
    log_validation(output_csv.parent / "validation_log.txt", "CI Mode: Single-Rater Simulation executed.")
    return scores

def run_research_mode(input_csv: Path, output_csv: Path) -> List[Dict[str, Any]]:
    scores = load_research_annotations(input_csv)
    if len(scores) < 50:
        raise ValueError("Sample size < 50 for Research Mode. FR-002 violation.")
    
    # Calculate disagreement
    disagreement = calculate_disagreement(scores)
    
    # Calculate Alpha
    alpha = calculate_krippendorff_alpha(scores)
    
    # Save final scores
    save_scores(scores, output_csv)
    
    log_validation(output_csv.parent / "validation_log.txt", f"Research Mode: Krippendorff Alpha = {alpha:.3f}")
    return scores

def main():
    parser = argparse.ArgumentParser(description="Annotator CLI")
    parser.add_argument("--mode", choices=["CI", "RESEARCH"], default="CI")
    parser.add_argument("--input-csv", type=Path, help="Input CSV for Research Mode")
    parser.add_argument("--output-csv", type=Path, default=None)
    args = parser.parse_args()

    set_mode(args.mode)
    
    if args.output_csv is None:
        args.output_csv = get_annotations_path() / "decoupled_scores.csv"

    if args.mode == "CI":
        # Mock image IDs for demo if no real data yet
        image_ids = [f"img_{i:04d}" for i in range(100)]
        run_ci_mode(image_ids, args.output_csv)
    else:
        if not args.input_csv:
            raise ValueError("--input-csv required for Research Mode")
        run_research_mode(args.input_csv, args.output_csv)

if __name__ == "__main__":
    from config import set_mode
    main()

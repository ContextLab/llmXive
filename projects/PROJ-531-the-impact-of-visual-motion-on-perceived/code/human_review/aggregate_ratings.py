"""
Human Review Aggregation Script (T033b).

Calculates the pass rate for the manual review process.
Verifies SC-005: >= 80% of reviewers must rate the artifacts >= 4/5.

Usage:
    python code/human_review/aggregate_ratings.py
    
Input:
    data/raw/reviewer_ratings.csv
    
Output:
    Prints pass/fail status to stdout.
    Writes summary to data/results/human_review_summary.json
"""
import os
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "reviewer_ratings.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_PATH = OUTPUT_DIR / "human_review_summary.json"

def load_ratings(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load ratings from a CSV file.
    Expects columns: reviewer_id, rating_1, rating_2, ... (or a generic 'rating' column).
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Ratings file not found: {filepath}")

    ratings = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ratings.append(row)
    
    if not ratings:
        raise ValueError("Ratings file is empty or has no valid rows.")
    
    return ratings

def calculate_pass_rate(ratings: List[Dict[str, Any]], threshold: float = 4.0, min_reviews: int = 3) -> Dict[str, Any]:
    """
    Calculate the pass rate based on the threshold (default 4/5).
    Returns a dictionary with the pass rate, total reviews, and pass status.
    """
    if len(ratings) < min_reviews:
        return {
            "total_reviews": len(ratings),
            "pass_rate": 0.0,
            "pass": False,
            "reason": f"Insufficient reviews. Minimum required: {min_reviews}, Found: {len(ratings)}"
        }

    # Identify rating columns (assuming they start with 'rating_')
    # If the CSV has a single 'rating' column, handle that too.
    rating_values = []
    
    for row in ratings:
        # Check for a single 'rating' column
        if 'rating' in row:
            try:
                rating_values.append(float(row['rating']))
            except ValueError:
                continue
        else:
            # Check for multiple rating columns (rating_1, rating_2, etc.)
            # We average the ratings per reviewer if multiple exist, or take the first valid one.
            # For simplicity in this stress test, we look for any column starting with 'rating_'
            reviewer_scores = []
            for key, value in row.items():
                if key.startswith('rating_'):
                    try:
                        reviewer_scores.append(float(value))
                    except ValueError:
                        pass
            
            if reviewer_scores:
                # Average the reviewer's scores
                avg_score = sum(reviewer_scores) / len(reviewer_scores)
                rating_values.append(avg_score)

    if not rating_values:
        return {
            "total_reviews": len(ratings),
            "pass_rate": 0.0,
            "pass": False,
            "reason": "No valid numeric ratings found in the CSV."
        }

    # Calculate pass rate: fraction of ratings >= threshold
    passed_count = sum(1 for r in rating_values if r >= threshold)
    pass_rate = passed_count / len(rating_values)

    return {
        "total_reviews": len(ratings),
        "valid_ratings_count": len(rating_values),
        "passed_count": passed_count,
        "threshold": threshold,
        "pass_rate": pass_rate,
        "pass": pass_rate >= 0.80,
        "reason": "SC-005 Met" if pass_rate >= 0.80 else "SC-005 Not Met (Rate < 80%)"
    }

def main():
    """Main entry point for the aggregation script."""
    print(f"--- Human Review Aggregation (T033b) ---")
    print(f"Input: {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")

    try:
        # Ensure output directory exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Load data
        ratings = load_ratings(INPUT_PATH)
        print(f"Loaded {len(ratings)} reviewer entries.")

        # Calculate metrics
        result = calculate_pass_rate(ratings)

        # Print results
        print(f"Total Reviews: {result['total_reviews']}")
        print(f"Pass Rate: {result['pass_rate']:.2%}")
        print(f"Threshold: {result['threshold']}/5")
        print(f"Result: {'PASS' if result['pass'] else 'FAIL'}")
        print(f"Reason: {result['reason']}")

        # Save JSON summary
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        print(f"Summary saved to: {OUTPUT_PATH}")

        # Exit with error code if failed, to allow CI to catch it
        if not result['pass']:
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

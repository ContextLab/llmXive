import os
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

def load_ratings(filepath: str) -> List[float]:
    """Load ratings from a CSV file with a 'rating_overall' column."""
    ratings = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'rating_overall' not in reader.fieldnames:
            raise ValueError("CSV must contain a column named 'rating_overall'")
        
        for row in reader:
            try:
                rating = float(row['rating_overall'])
                if not (1 <= rating <= 5):
                    raise ValueError(f"Invalid rating value: {rating}")
                ratings.append(rating)
            except ValueError as e:
                print(f"Warning: Skipping invalid row: {e}")
    
    return ratings

def calculate_pass_rate(ratings: List[float]) -> Dict[str, Any]:
    """Calculate the percentage of ratings >= 4."""
    if not ratings:
        return {
            "total_reviewers": 0,
            "pass_count": 0,
            "pass_rate": 0.0,
            "threshold": 0.8,
            "passed": False
        }
    
    pass_count = sum(1 for r in ratings if r >= 4)
    pass_rate = pass_count / len(ratings)
    threshold = 0.8  # 80%
    passed = pass_rate >= threshold
    
    return {
        "total_reviewers": len(ratings),
        "pass_count": pass_count,
        "pass_rate": pass_rate,
        "threshold": threshold,
        "passed": passed
    }

def main():
    """Main entry point for aggregation."""
    input_file = "data/results/reviewer_responses.csv"
    output_dir = Path("data/results")
    output_file = output_dir / "human_review_report.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        ratings = load_ratings(input_file)
        results = calculate_pass_rate(ratings)
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"Human Review Aggregation Report")
        print(f"--------------------------------")
        print(f"Total Reviewers: {results['total_reviewers']}")
        print(f"Ratings >= 4: {results['pass_count']}")
        print(f"Pass Rate: {results['pass_rate']:.2%}")
        print(f"Threshold: {results['threshold']:.0%}")
        print(f"Status: {'PASSED' if results['passed'] else 'FAILED'}")
        print(f"Report saved to: {output_file}")
        
        if not results['passed'] and results['total_reviewers'] > 0:
            print("\nNote: The project did not meet the 80% rating threshold.")
            print("Consider recruiting more reviewers or addressing feedback.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure reviewer responses are saved to 'data/results/reviewer_responses.csv'")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
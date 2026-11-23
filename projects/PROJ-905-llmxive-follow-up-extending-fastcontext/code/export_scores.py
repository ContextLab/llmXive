import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import get_path, ensure_directories
from stratification import load_scores_from_csv

def export_scores_to_csv(scores: List[Dict], output_path: str) -> None:
    """Export scores to a CSV file."""
    ensure_directories([Path(output_path).parent])
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['repo_id', 'regularity_score'])
        writer.writeheader()
        for s in scores:
            writer.writerow(s)

def main():
    # Demo: generate dummy scores if none exist
    input_path = get_path('processed', 'regularity_scores.csv')
    if not Path(input_path).exists():
        # Create dummy data for testing
        dummy_scores = [
            {'repo_id': 'repo1', 'regularity_score': 0.8},
            {'repo_id': 'repo2', 'regularity_score': 0.4}
        ]
        export_scores_to_csv(dummy_scores, input_path)
        print(f"Created dummy scores at {input_path}")
    
    # Load and re-export to verify
    scores = load_scores_from_csv(input_path)
    export_scores_to_csv(scores, input_path)
    print(f"Exported {len(scores)} scores to {input_path}")

if __name__ == '__main__':
    main()
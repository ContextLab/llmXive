import csv
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from config import get_path, ensure_directories

def load_scores_from_csv(input_path: str) -> List[Dict]:
    """Load scores from CSV into a list of dictionaries."""
    scores = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores.append({
                'repo_id': row['repo_id'],
                'regularity_score': float(row['regularity_score'])
            })
    return scores

def split_repos(scores: List[Dict], threshold: Optional[float] = None) -> Tuple[List[str], List[str]]:
    """
    Split repositories into 'Regular' and 'Irregular' sets.
    If threshold is provided, use it. Otherwise, use median split.
    """
    if not scores:
        return [], []

    sorted_scores = sorted(scores, key=lambda x: x['regularity_score'], reverse=True)
    
    if threshold is not None:
        regular = [s['repo_id'] for s in sorted_scores if s['regularity_score'] >= threshold]
        irregular = [s['repo_id'] for s in sorted_scores if s['regularity_score'] < threshold]
    else:
        # Median split
        n = len(sorted_scores)
        mid = n // 2
        regular = [s['repo_id'] for s in sorted_scores[:mid]]
        irregular = [s['repo_id'] for s in sorted_scores[mid:]]
    
    return regular, irregular

def save_sets_to_csv(regular: List[str], irregular: List[str], output_path: str) -> None:
    """Save the split sets to a CSV file."""
    ensure_directories([Path(output_path).parent])
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['repo_id', 'set_type'])
        for repo in regular:
            writer.writerow([repo, 'regular'])
        for repo in irregular:
            writer.writerow([repo, 'irregular'])

def main():
    input_path = get_path('processed', 'regularity_scores.csv')
    output_path = get_path('processed', 'stratified_sets.csv')
    
    if not Path(input_path).exists():
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
    
    scores = load_scores_from_csv(input_path)
    regular, irregular = split_repos(scores)
    save_sets_to_csv(regular, irregular, output_path)
    print(f"Saved {len(regular)} regular and {len(irregular)} irregular repos to {output_path}")

if __name__ == '__main__':
    main()

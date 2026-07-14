"""
Stratification module for splitting repositories into 'Regular' and 'Irregular' sets
based on their calculated regularity scores.
"""
import csv
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Ensure we can import sibling modules if running as a script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, ensure_directories


def split_repos(
    scores_data: List[Dict[str, Any]],
    threshold: Optional[float] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Sort repositories by regularity_score and split into two sets of approximately equal size.

    Args:
        scores_data: List of dicts containing 'repo_id' and 'regularity_score'
        threshold: Optional explicit threshold to split on. If None, uses median split.

    Returns:
        Tuple of (regular_set, irregular_set)
        - regular_set: Repositories with scores >= threshold (top half)
        - irregular_set: Repositories with scores < threshold (bottom half)
    """
    if not scores_data:
        return [], []

    # Sort by score descending (highest scores first)
    sorted_data = sorted(
        scores_data,
        key=lambda x: x.get('regularity_score', 0.0),
        reverse=True
    )

    if threshold is not None:
        # Use explicit threshold
        regular = [r for r in sorted_data if r.get('regularity_score', 0.0) >= threshold]
        irregular = [r for r in sorted_data if r.get('regularity_score', 0.0) < threshold]
    else:
        # Median split: top half regular, bottom half irregular
        mid_point = len(sorted_data) // 2
        regular = sorted_data[:mid_point]
        irregular = sorted_data[mid_point:]

    return regular, irregular


def load_scores_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load repository scores from a CSV file.

    Expected columns: repo_id, regularity_score (and potentially others)

    Args:
        csv_path: Path to the CSV file

    Returns:
        List of dictionaries with score data
    """
    scores = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure score is a float
            if 'regularity_score' in row:
                try:
                    row['regularity_score'] = float(row['regularity_score'])
                except (ValueError, TypeError):
                    row['regularity_score'] = 0.0
            scores.append(row)
    return scores


def save_sets_to_csv(
    regular_set: List[Dict[str, Any]],
    irregular_set: List[Dict[str, Any]],
    output_dir: Path
) -> Tuple[Path, Path]:
    """
    Save the regular and irregular sets to separate CSV files.

    Args:
        regular_set: List of regular repository records
        irregular_set: List of irregular repository records
        output_dir: Directory to write output files

    Returns:
        Tuple of (regular_path, irregular_path)
    """
    ensure_directories([output_dir])

    regular_path = output_dir / 'regular_repos.csv'
    irregular_path = output_dir / 'irregular_repos.csv'

    # Helper to write CSV
    def write_set(data: List[Dict], path: Path):
        if not data:
            # Write empty file with header if no data
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['repo_id', 'regularity_score'])
            return

        fieldnames = list(data[0].keys())
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    write_set(regular_set, regular_path)
    write_set(irregular_set, irregular_path)

    return regular_path, irregular_path


def main():
    """
    Main entry point for stratification.

    Reads from data/processed/regularity_scores.csv (if exists) or expects
    the input path to be provided via command line.
    Splits into regular/irregular sets and writes to data/processed/.
    """
    # Default paths
    input_csv = get_path('data/processed/regularity_scores.csv')
    output_dir = Path('data/processed')

    # Check for command line override
    if len(sys.argv) > 1:
        input_csv = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])

    if not input_csv.exists():
        print(f"Error: Input file not found: {input_csv}")
        sys.exit(1)

    print(f"Loading scores from {input_csv}...")
    scores_data = load_scores_from_csv(input_csv)
    print(f"Loaded {len(scores_data)} repositories.")

    if len(scores_data) == 0:
        print("No data to stratify.")
        sys.exit(0)

    print("Splitting into Regular and Irregular sets...")
    regular, irregular = split_repos(scores_data)

    print(f"Regular set: {len(regular)} repositories")
    print(f"Irregular set: {len(irregular)} repositories")

    regular_path, irregular_path = save_sets_to_csv(regular, irregular, output_dir)

    print(f"Saved regular set to: {regular_path}")
    print(f"Saved irregular set to: {irregular_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

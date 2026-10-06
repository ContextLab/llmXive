"""
Counterbalance Generator for Visual Complexity Study.

Implements Latin Square design generation to counterbalance stimulus presentation order
across participants, ensuring that each stimulus appears in each position exactly once
across the set of participants.

Output: data/processed/counterbalance_order.json
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project config for paths
try:
    from src.config import PROJECT_ROOT, DATA_DIR
except ImportError:
    # Fallback if running directly without full package structure
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"


def generate_latin_square(n: int, seed: int = 42) -> List[List[int]]:
    """
    Generate an n x n Latin Square.

    A Latin Square is an n x n array filled with n different symbols,
    each occurring exactly once in each row and exactly once in each column.

    Args:
        n: Size of the square (number of stimuli/participants).
        seed: Random seed for reproducibility.

    Returns:
        A list of lists representing the Latin Square.
    """
    import random
    random.seed(seed)

    # Start with the base row: [0, 1, 2, ..., n-1]
    base_row = list(range(n))
    square = [base_row]

    # Generate subsequent rows by cyclically shifting the base row
    # To ensure a proper Latin Square, we shift by 1 position each time
    for i in range(1, n):
        # Shift the previous row by 1 to the right (cyclic)
        # Actually, standard cyclic Latin square shifts the row index
        # Row i is base_row shifted by i positions
        new_row = [(base_row[j] - i) % n for j in range(n)]
        # Wait, standard cyclic: Row i, Col j = (i + j) % n
        # Let's construct it explicitly to be safe and clear.
        # Row i: start with i, then i+1, ..., wrapping around.
        new_row = [(i + j) % n for j in range(n)]
        square.append(new_row)

    # Optional: Shuffle rows and columns to randomize the specific square
    # while maintaining the Latin Square property.
    # We shuffle the rows first
    random.shuffle(square)
    
    # Then shuffle the columns (we need to transpose, shuffle rows, transpose back)
    # Transpose
    transposed = [[square[r][c] for r in range(n)] for c in range(n)]
    random.shuffle(transposed)
    # Transpose back
    final_square = [[transposed[r][c] for c in range(n)] for r in range(n)]

    return final_square


def generate_counterbalance_orders(stimuli_ids: List[str], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate counterbalanced presentation orders for participants.

    Uses a Latin Square design to ensure that:
    1. Each stimulus appears in each position exactly once across participants.
    2. Each stimulus follows every other stimulus exactly once (if n is large enough).

    Args:
        stimuli_ids: List of unique stimulus identifiers.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries, each containing:
            - 'participant_id': Unique ID for the participant (1-based index).
            - 'order': List of stimulus IDs in the order they should be presented.
            - 'latin_square_id': Identifier for the specific Latin Square used.
    """
    n = len(stimuli_ids)
    if n == 0:
        return []

    # Generate the Latin Square
    latin_square = generate_latin_square(n, seed)

    orders = []
    for i in range(n):
        # Map the numeric indices from the Latin Square to actual stimulus IDs
        order_indices = latin_square[i]
        order_ids = [stimuli_ids[idx] for idx in order_indices]
        
        orders.append({
            "participant_id": f"P{i+1:03d}",
            "order": order_ids,
            "latin_square_id": f"LS_{seed}",
            "stimulus_count": n
        })

    return orders


def load_stimuli_list(stimuli_dir: Optional[Path] = None) -> List[str]:
    """
    Load list of stimuli IDs from the curated clips or raw stimuli directory.
    
    Attempts to read from data/processed/curated_clips.csv first (as per T032c),
    then falls back to listing files in data/stimuli/raw if CSV is missing.

    Args:
        stimuli_dir: Optional path to stimuli directory.

    Returns:
        List of stimulus IDs (filenames without extension or IDs from CSV).
    """
    if stimuli_dir is None:
        stimuli_dir = DATA_DIR / "stimuli"
    
    # Try curated clips CSV first (T032c output)
    curated_csv = DATA_DIR / "processed" / "curated_clips.csv"
    if curated_csv.exists():
        import csv
        stimuli_ids = []
        with open(curated_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assuming 'clip_id' or 'filename' is the ID column
                if 'clip_id' in row:
                    stimuli_ids.append(row['clip_id'])
                elif 'filename' in row:
                    stimuli_ids.append(row['filename'])
                else:
                    # Fallback to first column
                    stimuli_ids.append(next(iter(row.values())))
        if stimuli_ids:
            return stimuli_ids

    # Fallback: list files in raw stimuli directory
    raw_dir = stimuli_dir / "raw"
    if raw_dir.exists():
        files = sorted([f.name for f in raw_dir.iterdir() if f.is_file()])
        # Strip extensions
        return [os.path.splitext(f)[0] for f in files]
    
    # If nothing found, raise error
    raise FileNotFoundError(f"No stimuli found in {stimuli_dir} or {curated_csv}")


def save_counterbalance_output(orders: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the counterbalance orders to a JSON file.

    Args:
        orders: List of order dictionaries.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(orders, f, indent=2)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Latin Square counterbalance orders for stimuli presentation."
    )
    parser.add_argument(
        "--stimuli-dir",
        type=str,
        default=None,
        help="Path to stimuli directory (default: data/stimuli)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "processed" / "counterbalance_order.json"),
        help="Output path for counterbalance JSON (default: data/processed/counterbalance_order.json)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for Latin Square generation (default: 42)"
    )
    return parser.parse_args()


def main() -> int:
    """Main entry point for counterbalance generation."""
    args = parse_arguments()

    stimuli_dir = Path(args.stimuli_dir) if args.stimuli_dir else None
    output_path = Path(args.output)

    try:
        # Load stimuli IDs
        print(f"Loading stimuli list from {stimuli_dir or 'default location'}...")
        stimuli_ids = load_stimuli_list(stimuli_dir)
        print(f"Found {len(stimuli_ids)} stimuli: {stimuli_ids[:5]}{'...' if len(stimuli_ids) > 5 else ''}")

        if not stimuli_ids:
            print("Error: No stimuli found. Cannot generate counterbalance orders.")
            return 1

        # Generate orders
        print(f"Generating Latin Square counterbalance (seed={args.seed})...")
        orders = generate_counterbalance_orders(stimuli_ids, seed=args.seed)

        # Save output
        print(f"Saving counterbalance orders to {output_path}...")
        save_counterbalance_output(orders, output_path)

        print(f"Success: Generated {len(orders)} participant orders.")
        return 0

    except Exception as e:
        print(f"Error generating counterbalance: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

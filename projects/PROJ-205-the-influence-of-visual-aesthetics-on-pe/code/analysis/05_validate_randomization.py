import os
import sys
import json
import argparse
from pathlib import Path
import pandas as pd
from collections import Counter
import numpy as np

# Import seed enforcement from helpers
from utils.helpers import set_reproducibility_seed, get_project_root

# Set seed at the very start of the script
set_reproducibility_seed()

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_submissions_csv_path() -> Path:
    """Returns the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_output_path() -> Path:
    """Returns the path to the randomization balance report JSON file."""
    return get_project_root() / "data" / "processed" / "randomization_balance_report.json"

def load_submissions_data(input_path: Path) -> pd.DataFrame:
    """Loads submissions data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def validate_randomization_balance(df: pd.DataFrame) -> Dict[str, Any]:
    """Validates the balance of randomization sequences."""
    # Expected sequences (from constants)
    expected_sequences = [
        ['professional', 'minimalist', 'low_quality', 'neutral'],
        ['minimalist', 'neutral', 'professional', 'low_quality'],
        ['low_quality', 'professional', 'neutral', 'minimalist'],
        ['neutral', 'low_quality', 'minimalist', 'professional']
    ]
    
    # Group by participant and reconstruct sequence
    participant_sequences = []
    for pid, group in df.groupby('participant_id'):
        # Sort by timestamp or order if available
        if 'timestamp' in group.columns:
            group = group.sort_values('timestamp')
        sequence = group['stimulus_id'].tolist()
        participant_sequences.append(sequence)
    
    # Count observed sequences
    observed_counts = Counter()
    for seq in participant_sequences:
        seq_tuple = tuple(seq)
        # Find matching expected sequence index
        for i, expected in enumerate(expected_sequences):
            if seq_tuple == tuple(expected):
                observed_counts[i] += 1
                break
    
    total_participants = len(participant_sequences)
    expected_per_sequence = total_participants / len(expected_sequences)
    
    # Calculate chi-square statistic
    chi_sq = 0
    for i in range(len(expected_sequences)):
        observed = observed_counts.get(i, 0)
        expected = expected_per_sequence
        if expected > 0:
            chi_sq += ((observed - expected) ** 2) / expected
    
    # Check for significant deviation (simplified)
    is_balanced = chi_sq < 7.815  # Chi-square critical value for df=3, alpha=0.05
    
    return {
        "total_participants": total_participants,
        "observed_counts": dict(observed_counts),
        "expected_per_sequence": expected_per_sequence,
        "chi_square_statistic": chi_sq,
        "is_balanced": is_balanced,
        "conclusion": "Randomization is balanced." if is_balanced else "Randomization shows significant deviation."
    }

def main():
    """Main entry point for the randomization validation script."""
    parser = argparse.ArgumentParser(description='Validate randomization balance')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else get_submissions_csv_path()
    output_path = Path(args.output) if args.output else get_output_path()
    
    try:
        # Load data
        print(f"Loading data from {input_path}...")
        df = load_submissions_data(input_path)
        
        # Validate balance
        results = validate_randomization_balance(df)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Randomization balance report saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

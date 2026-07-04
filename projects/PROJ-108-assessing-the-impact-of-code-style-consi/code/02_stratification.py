"""
Stratification script for code style consistency scores.

Reads raw style scores from data/metadata/style_scores_raw.csv,
applies user-defined thresholds to assign groups (Low, Medium, High),
and outputs the stratified dataset to data/processed/.
"""
import argparse
import csv
import sys
from pathlib import Path

# Ensure we can import from the code directory if run as a script
# but primarily designed to be run as: python code/02_stratification.py ...
# The input file is expected to exist based on T013 completion.

def load_style_scores(input_path: str) -> list[dict]:
    """
    Load style scores from a CSV file.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        List of dictionaries containing file metadata and scores.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the required 'composite_score' column is missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    rows = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Verify required columns exist
        if 'composite_score' not in reader.fieldnames:
            raise ValueError("Input CSV must contain 'composite_score' column")
        
        for row in reader:
            try:
                row['composite_score'] = float(row['composite_score'])
                # Preserve other fields as strings or convert if necessary
                # We keep file_size and cyclomatic_complexity as strings for now 
                # unless specific numeric operations are needed downstream
                if 'file_size' in row:
                    row['file_size'] = int(row['file_size'])
                if 'cyclomatic_complexity' in row:
                    row['cyclomatic_complexity'] = int(row['cyclomatic_complexity'])
                if 'file_age' in row:
                    # file_age might be an integer (days) or string
                    if row['file_age'] and row['file_age'].isdigit():
                        row['file_age'] = int(row['file_age'])
            except (ValueError, TypeError) as e:
                # Log warning but skip malformed rows to prevent crash
                sys.stderr.write(f"Warning: Skipping row due to parsing error: {e}\n")
                continue
            rows.append(row)
    
    if not rows:
        sys.stderr.write("Warning: No valid rows found in input file.\n")
        
    return rows

def assign_group(score: float, low_threshold: float, high_threshold: float) -> str:
    """
    Assign a group based on the composite score and thresholds.
    
    Logic:
    - Low: score < low_threshold
    - Medium: low_threshold <= score <= high_threshold
    - High: score > high_threshold
    
    Args:
        score: The composite style score.
        low_threshold: The lower boundary for the Medium group.
        high_threshold: The upper boundary for the Medium group.
        
    Returns:
        Group label string ('Low', 'Medium', 'High').
    """
    if score < low_threshold:
        return 'Low'
    elif score > high_threshold:
        return 'High'
    else:
        return 'Medium'

def stratify_data(rows: list[dict], low_threshold: float, high_threshold: float) -> list[dict]:
    """
    Add a 'group' column to each row based on thresholds.
    
    Args:
        rows: List of score dictionaries.
        low_threshold: Lower threshold value.
        high_threshold: Upper threshold value.
        
    Returns:
        Updated list of dictionaries with 'group' key.
    """
    for row in rows:
        row['group'] = assign_group(row['composite_score'], low_threshold, high_threshold)
    return rows

def save_stratified_data(rows: list[dict], output_path: str) -> None:
    """
    Save the stratified data to a CSV file.
    
    Args:
        rows: List of dictionaries to save.
        output_path: Path to the output CSV file.
    """
    if not rows:
        sys.stderr.write("Warning: No data to save.\n")
        # Create empty file with headers if possible, or just return
        # We'll try to infer headers from the first row if it existed, 
        # but since rows is empty, we can't. 
        # Let's create the file with standard headers if we know them, 
        # or just an empty file. 
        # For robustness, we'll create an empty file with a header row 
        # matching the expected schema if we can infer it, otherwise empty.
        # Given the task, we assume standard headers if no data.
        # However, csv.DictWriter needs fieldnames.
        # We'll skip creating a header-only file if rows is empty to avoid 
        # guessing wrong fields, or we can use a default set.
        # Let's assume the standard set from T013 output:
        default_fields = ['file_path', 'pylint_indent', 'radon_line_len', 'composite_score', 'group', 'file_size', 'cyclomatic_complexity', 'file_age']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=default_fields)
            writer.writeheader()
        return

    # Determine fieldnames from the first row
    fieldnames = list(rows[0].keys())
    
    # Ensure 'group' is in fieldnames (it should be)
    if 'group' not in fieldnames:
        fieldnames.append('group')

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(
        description="Stratify code style scores into Low, Medium, and High groups."
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/metadata/style_scores_raw.csv',
        help='Path to the input CSV file with style scores (default: data/metadata/style_scores_raw.csv)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='data/processed',
        help='Directory to save the output CSV file (default: data/processed)'
    )
    parser.add_argument(
        '--low-threshold',
        type=float,
        default=0.25,
        help='Threshold for Low/Medium split (default: 0.25)'
    )
    parser.add_argument(
        '--high-threshold',
        type=float,
        default=0.75,
        help='Threshold for Medium/High split (default: 0.75)'
    )

    args = parser.parse_args()

    # Validate thresholds
    if args.low_threshold >= args.high_threshold:
        sys.stderr.write("Error: --low-threshold must be less than --high-threshold.\n")
        sys.exit(1)
    
    if not (0.0 <= args.low_threshold <= 1.0) or not (0.0 <= args.high_threshold <= 1.0):
        sys.stderr.write("Error: Thresholds must be between 0.0 and 1.0.\n")
        sys.exit(1)

    try:
        # Load data
        sys.stderr.write(f"Loading data from {args.input}...\n")
        rows = load_style_scores(args.input)
        
        if not rows:
            sys.stderr.write("No data found to stratify.\n")
            # Still generate an empty output file to be consistent
            output_filename = f"style_scores_threshold_{args.low_threshold:.2f}_{args.high_threshold:.2f}.csv"
            output_path = Path(args.output_dir) / output_filename
            save_stratified_data([], str(output_path))
            sys.stderr.write(f"Created empty output file: {output_path}\n")
            sys.exit(0)

        # Stratify
        sys.stderr.write(f"Stratifying {len(rows)} files with thresholds: Low<{args.low_threshold}, Med[{args.low_threshold}-{args.high_threshold}], High>{args.high_threshold}...\n")
        stratified_rows = stratify_data(rows, args.low_threshold, args.high_threshold)

        # Generate output filename
        # Format thresholds to avoid floating point representation issues in filename
        # e.g., 0.25 -> 0.25, 0.75 -> 0.75
        output_filename = f"style_scores_threshold_{args.low_threshold:.2f}_{args.high_threshold:.2f}.csv"
        output_path = Path(args.output_dir) / output_filename

        # Save
        save_stratified_data(stratified_rows, str(output_path))
        
        # Summary
        groups = {}
        for row in stratified_rows:
            g = row['group']
            groups[g] = groups.get(g, 0) + 1
        
        sys.stderr.write(f"Success! Output written to {output_path}\n")
        sys.stderr.write(f"Group distribution: Low={groups.get('Low', 0)}, Medium={groups.get('Medium', 0)}, High={groups.get('High', 0)}\n")
        
    except FileNotFoundError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except ValueError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
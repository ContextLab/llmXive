import argparse
import csv
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths

def main():
    parser = argparse.ArgumentParser(description='Generate ground truth file for human annotation.')
    parser.add_argument('--input', default='data/processed/annotation_sample.csv', help='Path to annotation sample CSV')
    parser.add_argument('--output', default='data/processed/annotation_labels.csv', help='Path to output labels CSV')
    
    args = parser.parse_args()
    
    input_path = args.input
    output_path = args.output
    
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Read input
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    if not rows:
        print("Error: No rows found in input file.")
        sys.exit(1)
    
    # Prepare output fieldnames
    output_fieldnames = list(fieldnames) + ['is_violation', 'is_implicit']
    
    # Write output with placeholders
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        for row in rows:
            # Add empty placeholders
            row['is_violation'] = ''
            row['is_implicit'] = ''
            writer.writerow(row)
    
    print(f"Generated ground truth file: {output_path}")
    print(f"Total rows: {len(rows)}")
    print("Please manually fill 'is_violation' and 'is_implicit' columns with 'true' or 'false' values.")

if __name__ == '__main__':
    main()
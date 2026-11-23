"""
Parameter Grid Generator for User Story 2 (US2).

Generates parameter configurations for the CA engine sweep by varying:
- locality: radius of interaction (1, 2, 3)
- memory: number of past states considered (0, 1, 2)
- non_linearity: strength of non-linear update rules (0.1, 0.5, 0.9)

Outputs a CSV file containing all combinations of these parameters.
"""
import argparse
import csv
import os
import itertools
from typing import List, Dict, Any, Iterator

# Define the parameter ranges based on the CA engine requirements
# These correspond to the schema defined in T004a
PARAM_RANGES = {
    'locality': [1, 2, 3],
    'memory': [0, 1, 2],
    'non_linearity': [0.1, 0.5, 0.9]
}

def generate_combinations() -> Iterator[Dict[str, Any]]:
    """
    Generates all combinations of the defined parameter ranges.
    
    Yields:
        Dict[str, Any]: A dictionary representing a single configuration.
    """
    keys = list(PARAM_RANGES.keys())
    values = [PARAM_RANGES[k] for k in keys]
    
    for combo in itertools.product(*values):
        yield dict(zip(keys, combo))

def write_grid_csv(configs: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes the list of configurations to a CSV file.
    
    Args:
        configs: List of configuration dictionaries.
        output_path: Path to the output CSV file.
    """
    if not configs:
        raise ValueError("No configurations to write.")
    
    fieldnames = list(configs[0].keys())
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(configs)

def main() -> None:
    """
    Entry point for the grid generation script.
    """
    parser = argparse.ArgumentParser(
        description='Generate parameter grid for CA simulation sweep.'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/parameter_grid.csv',
        help='Output path for the parameter grid CSV.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite output file if it exists.'
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if os.path.exists(args.output) and not args.force:
        print(f"Error: Output file '{args.output}' already exists. Use --force to overwrite.")
        return

    # Generate configurations
    configs = list(generate_combinations())
    total_configs = len(configs)
    
    print(f"Generated {total_configs} parameter configurations.")
    
    # Write to CSV
    write_grid_csv(configs, args.output)
    print(f"Parameter grid written to: {args.output}")

if __name__ == '__main__':
    main()

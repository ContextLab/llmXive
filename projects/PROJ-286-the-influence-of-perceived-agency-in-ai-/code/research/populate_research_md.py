import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_text_file(path: Path) -> str:
    """Read the contents of a text file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def validate_power_calculation_json(data: Dict[str, Any]) -> bool:
    """
    Validate that the power calculation JSON has the required structure.
    Required keys:
      - params: {effect_size, alpha, power}
      - results: {required_n, calculated_n}
    """
    if 'params' not in data:
        return False
    params = data['params']
    required_params = ['effect_size', 'alpha', 'power']
    if not all(key in params for key in required_params):
        return False

    if 'results' not in data:
        return False
    results = data['results']
    required_results = ['required_n', 'calculated_n']
    if not all(key in results for key in required_results):
        return False

    return True

def populate_research_md(power_calc_path: Path, output_path: Path) -> None:
    """
    Read power_calculation.json and populate the research.md table.
    
    Schema:
    | Effect Size | Alpha | Target Power | Required N | Calculated N |
    |-------------|-------|--------------|------------|--------------|
    | [effect_size] | [alpha] | [power] | [required_n] | [calculated_n] |
    
    Row Order:
    1) Effect Size
    2) Alpha
    3) Target Power
    4) Required N
    5) Calculated N
    """
    if not power_calc_path.exists():
        raise FileNotFoundError(f"Power calculation file not found: {power_calc_path}")

    data = load_json_file(power_calc_path)
    
    if not validate_power_calculation_json(data):
        raise ValueError("Invalid power calculation JSON structure")

    params = data['params']
    results = data['results']

    # Extract values
    effect_size = params['effect_size']
    alpha = params['alpha']
    target_power = params['power']
    required_n = results['required_n']
    calculated_n = results['calculated_n']

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Construct the markdown table
    # Note: The task description specifies a table with columns and rows that seem to
    # invert the typical "row per metric" vs "column per metric" convention.
    # The schema requested:
    # | Effect Size | Alpha | Target Power | Required N | Calculated N |
    # Row 1: Effect Size (value), Alpha (N/A?), ...
    # Actually, looking at the description: "Row Order: 1) Effect Size, 2) Alpha..."
    # This implies the table has 5 rows, one for each metric, and the columns are the metric names?
    # Or is it a single row with 5 columns?
    # Let's re-read: "Markdown table with exact columns: | Effect Size | Alpha | Target Power | Required N | Calculated N |"
    # "Row Order: 1) Effect Size, 2) Alpha..."
    # This is contradictory. A table with columns named "Effect Size" cannot have a row named "Effect Size".
    # Interpretation: The user likely wants a table where the *first row* is the header,
    # and the subsequent rows contain the values. But the "Row Order" instruction lists the metrics.
    #
    # Alternative Interpretation: The table is transposed.
    # Columns: Metric, Value? No, the columns are explicitly listed.
    #
    # Let's assume the standard scientific reporting table format where the header row lists the metrics,
    # and the data row contains the values.
    # Header: | Effect Size | Alpha | Target Power | Required N | Calculated N |
    # Data:   | 0.25 | 0.05 | 0.80 | 128 | 150 | (example)
    #
    # However, the instruction "Row Order: 1) Effect Size..." suggests 5 rows of data.
    # Maybe the table is:
    # | Parameter | Value |
    # |---|---|
    # | Effect Size | ... |
    # | Alpha | ... |
    #
    # But the columns are explicitly defined as the 5 metrics.
    # Let's try to follow the "Row Order" literally as a single row where the columns are the metrics,
    # and the "Row Order" text is a slightly confused way of saying "The values for these columns, in this order".
    #
    # Wait, let's look at the "Row Order" again.
    # "Row Order: 1) Effect Size, 2) Alpha, 3) Target Power, 4) Required N, 5) Calculated N."
    # If these are rows, then the columns must be something else. But the columns are defined as those exact 5 names.
    #
    # Hypothesis: The user wants a table where the *headers* are "Parameter" and "Value", but the prompt explicitly said "exact columns: | Effect Size | Alpha | ...".
    #
    # Let's assume the prompt meant: "The table should have a header row with these columns, and ONE data row containing the values in that order."
    # This is the most standard way to present this summary.
    #
    # Let's construct:
    # | Effect Size | Alpha | Target Power | Required N | Calculated N |
    # | :--- | :--- | :--- | :--- | :--- |
    # | {effect_size} | {alpha} | {target_power} | {required_n} | {calculated_n} |
    
    table_content = f"""| Effect Size | Alpha | Target Power | Required N | Calculated N |
| :--- | :--- | :--- | :--- | :--- |
| {effect_size} | {alpha} | {target_power} | {required_n} | {calculated_n} |
"""

    # If the user strictly meant 5 rows (one for each metric), the columns would have to be different.
    # Given the explicit column definition, I will proceed with the single data row interpretation.
    # If the "Row Order" meant the order of columns in the header, that matches the column definition.

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(table_content)

def main():
    parser = argparse.ArgumentParser(description='Populate research.md from power calculation JSON')
    parser.add_argument('--input', type=str, required=True, help='Path to power_calculation.json')
    parser.add_argument('--output', type=str, required=True, help='Path to output research.md')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        populate_research_md(input_path, output_path)
        print(f"Successfully populated {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
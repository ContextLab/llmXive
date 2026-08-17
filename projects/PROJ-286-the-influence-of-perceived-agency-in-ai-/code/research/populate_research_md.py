import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_text_file(path: Path) -> str:
    """Read a text file and return its contents as a string."""
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def validate_power_calculation_json(data: Dict[str, Any]) -> bool:
    """Validate that the power calculation JSON has the required fields."""
    required_fields = ['effect_size', 'alpha', 'power', 'results']
    return all(field in data for field in required_fields)

def validate_citations_json(data: List[Dict[str, Any]]) -> bool:
    """Validate that the citations JSON has the required fields."""
    if not data:
        return False
    required_fields = ['title', 'status']
    return all(all(field in item for field in required_fields) for item in data)

def validate_citation_log(data: List[Dict[str, Any]]) -> bool:
    """Validate that the citation log has the required fields."""
    if not data:
        return False
    required_fields = ['title', 'status']
    return all(all(field in item for field in required_fields) for item in data)

def populate_research_md(power_calc_data: Dict[str, Any], output_path: Path) -> None:
    """
    Populate the research.md file with the power calculation results.
    
    Args:
        power_calc_data: Dictionary containing power calculation results.
        output_path: Path to the output research.md file.
    """
    # Extract values from the power calculation data
    effect_size = power_calc_data.get('effect_size', 'N/A')
    alpha = power_calc_data.get('alpha', 'N/A')
    target_power = power_calc_data.get('power', 'N/A')
    required_n = power_calc_data.get('results', {}).get('sample_size', 'N/A')
    calculated_n = power_calc_data.get('results', {}).get('calculated_sample_size', required_n)

    # Create the markdown content
    markdown_content = f"""# Research Report: The Influence of Perceived Agency in AI Interactions on Trust

## Power Analysis Summary

| Effect Size | Alpha | Target Power | Required N | Calculated N |
|-------------|-------|--------------|------------|--------------|
| {effect_size} | {alpha} | {target_power} | {required_n} | {calculated_n} |

## Notes

- Effect size: Small-to-moderate magnitude (Cohen's f)
- Alpha level: 0.05 (standard significance threshold)
- Target power: 0.80 (80% probability of detecting an effect if it exists)
- Required N: Minimum sample size needed to achieve target power
- Calculated N: Actual sample size calculated based on power analysis

## References

This analysis is based on the power calculation performed in `research/power_calculation.json`.
The methodology follows standard practices for one-way ANOVA power analysis using statsmodels.
"""

    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the markdown content to the file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

def main():
    """Main function to populate the research.md file."""
    parser = argparse.ArgumentParser(description='Populate research.md with power calculation results')
    parser.add_argument('--input', type=str, required=True, help='Path to power_calculation.json')
    parser.add_argument('--output', type=str, required=True, help='Path to output research.md')
    args = parser.parse_args()

    try:
        # Load the power calculation JSON
        input_path = Path(args.input)
        power_calc_data = load_json_file(input_path)

        # Validate the data
        if not validate_power_calculation_json(power_calc_data):
            print("Error: Invalid power calculation JSON format")
            sys.exit(1)

        # Populate the research.md file
        output_path = Path(args.output)
        populate_research_md(power_calc_data, output_path)
        print(f"Successfully populated {output_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
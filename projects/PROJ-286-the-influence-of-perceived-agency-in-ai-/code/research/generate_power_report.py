import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

def load_json_file(path: Path) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required input file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def ensure_research_md_references_report(research_md_path: Path, report_filename: str) -> None:
    """
    Ensure that research.md contains a reference to the generated power report.
    If the reference is missing, append it to the file.
    """
    if not research_md_path.exists():
        raise FileNotFoundError(f"research.md not found at {research_md_path}")

    content = research_md_path.read_text(encoding='utf-8')
    reference_text = f"- [X] **Power Analysis Report**: See `research/{report_filename}` for detailed pre-study power calculations."

    if report_filename not in content:
        # Append to the end of the file
        with open(research_md_path, 'a', encoding='utf-8') as f:
            f.write("\n\n")
            f.write(reference_text)
            f.write("\n")
    else:
        # Already referenced
        pass

def generate_markdown_report(data: dict, output_path: Path) -> None:
    """
    Generate a formal Markdown report from the power calculation data.
    Sections: Method, Parameters, Result, Conclusion.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    method = """
## Method

A pre-study power analysis was conducted to determine the required sample size for the planned One-Way ANOVA.
The analysis aims to detect a small-to-moderate effect size with a specified alpha level and target power.
The calculation uses the F-test for ANOVA as implemented in the `statsmodels` library.
"""

    parameters = f"""
## Parameters

| Parameter | Value | Description |
| :--- | :--- | :--- |
| **Effect Size (f)** | {data['input']['effect_size']} | Expected magnitude of the effect (small-to-moderate). |
| **Alpha Level (α)** | {data['input']['alpha']} | Significance threshold (Type I error rate). |
| **Target Power (1-β)** | {data['input']['power']} | Probability of correctly rejecting the null hypothesis. |
| **Number of Groups** | {data['input']['n_groups']} | Number of experimental conditions (High, Low, Control). |
"""

    result = f"""
## Result

| Metric | Calculated Value |
| :--- | :--- |
| **Required Sample Size (Total N)** | {data['results']['sample_size']} |
| **Sample Size per Group** | {data['results']['sample_size_per_group']} |
| **Achieved Power** | {data['results']['achieved_power']:.4f} |
"""

    conclusion = f"""
## Conclusion

Based on the parameters defined above, a total sample size of **{data['results']['sample_size']}** participants
is required to achieve a statistical power of **{data['input']['power']:.2f}** at an alpha level of **{data['input']['alpha']:.2f}**.
This sample size will be used to configure the experiment recruitment targets.

*Report generated on {timestamp}.*
"""

    full_content = f"# Pre-Study Power Calculation Report\n\n{method}{parameters}{result}{conclusion}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_content, encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description="Generate formal power analysis report markdown.")
    parser.add_argument(
        "--input-json",
        type=str,
        default="research/power_calculation.json",
        help="Path to the JSON file containing power calculation results."
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="research/power_report.md",
        help="Path for the generated Markdown report."
    )
    parser.add_argument(
        "--research-md",
        type=str,
        default="specs/001-perceived-agency-trust/research.md",
        help="Path to the main research.md file to update with references."
    )

    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_path = Path(args.output_md)
    research_md_path = Path(args.research_md)

    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist. Run T002 first.")
        sys.exit(1)

    data = load_json_file(input_path)

    generate_markdown_report(data, output_path)
    print(f"Report generated: {output_path}")

    ensure_research_md_references_report(research_md_path, output_path.name)
    print(f"Updated reference in: {research_md_path}")

if __name__ == "__main__":
    main()
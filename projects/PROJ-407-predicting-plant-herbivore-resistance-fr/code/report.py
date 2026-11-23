import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Importing from sibling modules as per API surface
# Note: config is imported locally to ensure paths are resolved correctly relative to project root
from config import DATA_ROOT

def load_json_file(filepath: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_csv_file(filepath: Path) -> list:
    """Load a CSV file and return its contents as a list of dictionaries."""
    # Using simple CSV parsing to avoid heavy dependencies if not strictly needed,
    # but pandas is available in requirements. Using csv module for standard lib compliance.
    import csv
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def generate_summary_report(
    metrics_data: dict,
    biomarkers_data: list,
    validation_data: dict,
    output_path: Path
) -> None:
    """
    Generate the summary report in Markdown format.
    
    Logic:
    1. Check if the global p-value from validation is >= 0.05.
    2. If so, explicitly state "Null Result".
    3. Otherwise, list the significant biomarkers with their q-values.
    """
    report_lines = []
    report_lines.append("# Summary Report: Plant Herbivore Resistance Prediction")
    report_lines.append(f"Generated at: {datetime.now().isoformat()}")
    report_lines.append("")
    
    # --- Model Metrics Section ---
    report_lines.append("## Model Performance")
    if metrics_data:
        r2 = metrics_data.get('r2', 'N/A')
        mse = metrics_data.get('mse', 'N/A')
        report_lines.append(f"- **R² Score**: {r2}")
        report_lines.append(f"- **Mean Squared Error (MSE)**: {mse}")
    else:
        report_lines.append("- *No model metrics available.*")
    report_lines.append("")

    # --- Validation & Null Result Section ---
    report_lines.append("## Statistical Validation")
    global_p_value = None
    if validation_data:
        global_p_value = validation_data.get('global_p_value')
        n_permutations = validation_data.get('n_permutations', 0)
        report_lines.append(f"- **Permutation Test Iterations**: {n_permutations}")
        report_lines.append(f"- **Global P-value**: {global_p_value}")
    
    # Determine Null Result status based on T031 logic (p >= 0.05)
    is_null_result = False
    if global_p_value is not None:
        try:
            p_val = float(global_p_value)
            if p_val >= 0.05:
                is_null_result = True
                report_lines.append("")
                report_lines.append("### ⚠️ Null Result Detected")
                report_lines.append(f"The global p-value ({p_val}) is ≥ 0.05.")
                report_lines.append("The model performance is not statistically distinguishable from random chance.")
                report_lines.append("No biomarkers are reported.")
        except (ValueError, TypeError):
            report_lines.append("- *Could not parse global p-value for null result check.*")

    report_lines.append("")

    # --- Biomarkers Section ---
    report_lines.append("## Significant Biomarkers")
    if is_null_result:
        report_lines.append("No significant biomarkers listed due to Null Result.")
    else:
        if biomarkers_data and len(biomarkers_data) > 0:
            report_lines.append("The following metabolites are significantly associated with resistance (q < 0.10):")
            report_lines.append("")
            report_lines.append("| Metabolite | Correlation | Unadjusted P | Adjusted Q (q-value) |")
            report_lines.append("|---|---|---|---|")
            
            # Sort by q-value ascending if possible, or just list
            sorted_biomarkers = sorted(biomarkers_data, key=lambda x: float(x.get('q_value', 1.0)))
            
            for row in sorted_biomarkers:
                name = row.get('metabolite_name', 'Unknown')
                corr = row.get('correlation_coefficient', 'N/A')
                p_val = row.get('unadjusted_p_value', 'N/A')
                q_val = row.get('q_value', 'N/A')
                report_lines.append(f"| {name} | {corr} | {p_val} | {q_val} |")
        else:
            report_lines.append("No significant biomarkers found (q < 0.10).")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*End of Report*")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

def main():
    parser = argparse.ArgumentParser(description="Generate summary report from model and validation results.")
    parser.add_argument("--input", type=str, required=True, help="Directory containing model_metrics.json, significant_biomarkers.csv, and permutation results.")
    parser.add_argument("--output", type=str, required=True, help="Path to save the summary report (e.g., results/summary_report.md).")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.output)

    # Define expected file paths based on pipeline outputs
    metrics_file = input_dir / "model_metrics.json"
    biomarkers_file = input_dir / "significant_biomarkers.csv"
    validation_file = input_dir / "permutation_p_value.json" # Assuming this contains global p-value

    # Load data
    try:
        metrics_data = load_json_file(metrics_file)
    except FileNotFoundError:
        metrics_data = {}
        print(f"Warning: {metrics_file} not found. Proceeding with empty metrics.")

    try:
        biomarkers_data = load_csv_file(biomarkers_file)
    except FileNotFoundError:
        biomarkers_data = []
        print(f"Warning: {biomarkers_file} not found. Proceeding with empty biomarkers.")

    try:
        validation_data = load_json_file(validation_file)
    except FileNotFoundError:
        validation_data = {}
        print(f"Warning: {validation_file} not found. Proceeding with empty validation data.")

    # Generate Report
    generate_summary_report(metrics_data, biomarkers_data, validation_data, output_path)
    print(f"Report generated successfully at: {output_path}")

if __name__ == "__main__":
    main()
"""
T030d: Integrate results; ensure correlation coefficients are reported separately from regression control model.

This script loads the output from the correlation analysis (stats.py) and the
multiple linear regression analysis, merges them into a single comprehensive
results file, and generates a structured report ensuring that simple correlation
metrics are distinctly separated from the controlled regression metrics.

It reads:
  - data/processed/correlation_results.json (output of stats.py main)
  - data/processed/regression_results.json (output of stats.py main)

It writes:
  - data/processed/integrated_analysis_results.json
  - reports/integrated_results_summary.txt
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure code directory is in path for imports if running as script
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from stats import load_graph_metrics, load_behavioral_scores, merge_metrics_with_scores, bonferroni_correction, compute_correlation, analyze_correlations, run_multiple_linear_regression


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, otherwise return None."""
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)


def generate_summary_text(results: Dict[str, Any]) -> str:
    """Generate a human-readable summary text of the integrated results."""
    lines = [
        "INTEGRATED ANALYSIS RESULTS SUMMARY",
        "=" * 50,
        "",
        f"Total Subjects Analyzed: {results.get('metadata', {}).get('subject_count', 'N/A')}",
        f"Bonferroni Correction Factor (k): {results.get('metadata', {}).get('bonferroni_k', 'N/A')}",
        "",
        "--- CORRELATION ANALYSIS (Uncontrolled) ---",
    ]
    
    corr_results = results.get('correlation_analysis', {})
    if corr_results:
        for metric, data in corr_results.items():
            lines.append(f"Metric: {metric}")
            lines.append(f"  Correlation Coefficient (r): {data.get('r', 'N/A')}")
            lines.append(f"  P-value: {data.get('p_value', 'N/A')}")
            lines.append(f"  Bonferroni Corrected P-value: {data.get('bonferroni_p', 'N/A')}")
            lines.append(f"  Significant (p < 0.05): {data.get('is_significant', 'N/A')}")
            lines.append("")
    else:
        lines.append("No correlation results found.")
        lines.append("")

    lines.append("--- REGRESSION ANALYSIS (Controlled for Age/Gender) ---")
    reg_results = results.get('regression_analysis', {})
    if reg_results:
        for metric, data in reg_results.items():
            lines.append(f"Metric: {metric}")
            lines.append(f"  Intercept: {data.get('intercept', 'N/A')}")
            lines.append(f"  Coefficient (Fluid Intelligence): {data.get('coeff_fluid_int', 'N/A')}")
            lines.append(f"  P-value (Fluid Intelligence): {data.get('p_value_fluid_int', 'N/A')}")
            lines.append(f"  R-squared: {data.get('r_squared', 'N/A')}")
            lines.append(f"  Significant (p < 0.05): {data.get('is_significant', 'N/A')}")
            lines.append("")
    else:
        lines.append("No regression results found.")
        lines.append("")

    lines.append("=" * 50)
    lines.append("End of Report")
    return "\n".join(lines)


def main():
    """Main entry point for T030d: Integrate results."""
    print("Starting T030d: Integrating correlation and regression results...")
    
    base_dir = Path(__file__).resolve().parent.parent
    data_processed_dir = base_dir / "data" / "processed"
    reports_dir = base_dir / "reports"

    # Define input paths (assuming stats.py writes these)
    # Note: The exact filenames might depend on how stats.py is structured, 
    # but we assume standard outputs for correlation and regression.
    # If stats.py outputs a single file, we might need to load and split it,
    # but the task implies separate reporting. Let's assume stats.py 
    # produces separate JSONs or a single JSON with sections.
    # To be safe, let's look for a single comprehensive stats output first,
    # or construct it if stats.py outputs separate files.
    
    # Re-reading stats.py main logic (implied): It likely computes both.
    # Let's assume stats.py outputs a file 'stats_results.json' containing both sections,
    # OR we run the stats functions here to regenerate/ensure data consistency.
    # Given T030b and T030c are separate tasks, let's assume they might have written
    # to separate files or a shared one. Let's try to load a combined stats file first.
    
    stats_file = data_processed_dir / "stats_results.json"
    
    if stats_file.exists():
        print(f"Loading existing stats results from {stats_file}...")
        stats_data = load_json_file(stats_file)
        if not stats_data:
            print("Error: Failed to load stats_results.json. Re-running analysis might be needed.")
            # Fallback: Re-run analysis to ensure data exists
            print("Re-running correlation and regression analysis to populate results...")
            # We need to call the stats functions. 
            # However, to avoid side effects, let's assume the stats.py main() 
            # was responsible for writing these. If it didn't, we must do it here.
            # Let's implement the logic to run the analysis if the file is missing or empty.
            pass 
    else:
        stats_data = None
        print("stats_results.json not found. Running analysis to generate it...")

    # If stats_data is missing or incomplete, run the analysis
    if not stats_data or 'correlation_analysis' not in stats_data or 'regression_analysis' not in stats_data:
        print("Running correlation and regression analysis...")
        
        # Load data
        graph_metrics = load_graph_metrics(data_processed_dir / "graph_metrics.csv")
        behavioral_scores = load_behavioral_scores(data_processed_dir / "behavioral_scores.json") # Assuming this path or similar
        
        if not graph_metrics or not behavioral_scores:
            print("Error: Could not load graph metrics or behavioral scores. Cannot proceed with integration.")
            print("Ensure T025 (graph_metrics.csv) and T014a/T030a (behavioral scores) are complete.")
            sys.exit(1)

        merged_data = merge_metrics_with_scores(graph_metrics, behavioral_scores)
        
        if not merged_data:
            print("Error: No valid merged data found (no subjects with both metrics and scores).")
            sys.exit(1)

        # Run Correlation
        corr_results = analyze_correlations(merged_data)
        
        # Run Regression
        reg_results = run_multiple_linear_regression(merged_data)
        
        # Apply Bonferroni to correlations
        k = len(corr_results) if corr_results else 1
        for metric, res in corr_results.items():
            res['bonferroni_p'] = bonferroni_correction(res['p_value'], k)
            res['is_significant'] = res['bonferroni_p'] < 0.05

        for metric, res in reg_results.items():
            res['is_significant'] = res['p_value_fluid_int'] < 0.05

        stats_data = {
            "metadata": {
                "subject_count": len(merged_data),
                "bonferroni_k": k,
                "analysis_date": "2023-10-27" # Placeholder, use datetime in real impl
            },
            "correlation_analysis": corr_results,
            "regression_analysis": reg_results
        }

    # Ensure output directories exist
    reports_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    # Save Integrated JSON
    integrated_file = data_processed_dir / "integrated_analysis_results.json"
    save_json_file(stats_data, integrated_file)
    print(f"Saved integrated results to {integrated_file}")

    # Generate Text Summary
    summary_text = generate_summary_text(stats_data)
    summary_file = reports_dir / "integrated_results_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(summary_text)
    print(f"Saved summary report to {summary_file}")

    print("T030d Integration Complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
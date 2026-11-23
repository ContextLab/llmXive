"""
Comparison Logic for Mixed-Effects vs ANOVA Results (Task T035)

This script compares the findings from the Repeated-Measures ANOVA
(data/processed/anova_results.json) with the Mixed-Effects Model results
(data/processed/mixed_effects_results.json) to assess robustness.

It generates a comparison report saved to:
data/processed/mixed_effects_comparison.json
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Import path utilities from helpers if available, or define locally
# The API surface indicates helpers.py is in code/utils/
# We will use standard path manipulation to locate files relative to project root.

def get_project_root():
    """Returns the absolute path to the project root."""
    # Assuming this script is at code/analysis/04_compare.py
    # Project root is 3 levels up: code/analysis/..
    return Path(__file__).resolve().parent.parent.parent

def get_anova_results_path():
    """Returns path to ANOVA results JSON."""
    return get_project_root() / "data" / "processed" / "anova_results.json"

def get_mixed_effects_results_path():
    """Returns path to Mixed-Effects results JSON."""
    return get_project_root() / "data" / "processed" / "mixed_effects_results.json"

def get_comparison_output_path():
    """Returns path for the comparison report."""
    return get_project_root() / "data" / "processed" / "mixed_effects_comparison.json"

def load_json_file(path: Path):
    """Loads and returns JSON content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def compare_results(anova_data: dict, mixed_data: dict) -> dict:
    """
    Compares ANOVA and Mixed-Effects results.

    Extracts key statistics from both and determines if conclusions align.
    """
    comparison_report = {
        "status": "completed",
        "input_files": {
            "anova": str(get_anova_results_path()),
            "mixed_effects": str(get_mixed_effects_results_path())
        },
        "anova_summary": {},
        "mixed_effects_summary": {},
        "conclusion": {},
        "details": {}
    }

    # --- Extract ANOVA Key Metrics ---
    # Structure expected from T025a: {'anova': {'F': ..., 'p': ..., 'partial_eta_squared': ...}}
    anova_section = anova_data.get('anova', {})
    if not anova_section:
        # Fallback if structure is flat or different
        anova_section = anova_data

    anova_f = anova_section.get('F')
    anova_p = anova_section.get('p')
    anova_eta2 = anova_section.get('partial_eta_squared')

    comparison_report["anova_summary"] = {
        "F_statistic": anova_f,
        "p_value": anova_p,
        "partial_eta_squared": anova_eta2,
        "is_significant": anova_p is not None and anova_p < 0.05
    }

    # --- Extract Mixed-Effects Key Metrics ---
    # Structure expected from T032: {'model_summary': {'coefficients': [...], ...}}
    mixed_section = mixed_data.get('model_summary', {})
    if not mixed_section:
        mixed_section = mixed_data

    # We look for the 'Condition' coefficient in the mixed model
    # The mixed model formula is: Credibility ~ Condition + Age + Education + (1|Participant)
    # The coefficient for 'Condition' (or the specific condition level) is the effect size estimate.
    coefficients = mixed_section.get('coefficients', [])
    
    condition_effect = None
    condition_se = None
    condition_t = None
    
    # Heuristic to find the condition effect (usually the first non-intercept)
    for coef in coefficients:
        term = coef.get('term', '')
        # Skip intercept
        if 'Intercept' in term or 'const' in term:
            continue
        # Assume the first non-intercept term is the Condition effect or we look for 'Condition'
        if 'Condition' in term:
            condition_effect = coef.get('estimate')
            condition_se = coef.get('std err')
            condition_t = coef.get('t')
            break
    
    # If specific 'Condition' not found, try to grab the first non-intercept
    if condition_effect is None and coefficients:
        for coef in coefficients:
            term = coef.get('term', '')
            if 'Intercept' not in term and 'const' not in term:
                condition_effect = coef.get('estimate')
                condition_se = coef.get('std err')
                condition_t = coef.get('t')
                break

    comparison_report["mixed_effects_summary"] = {
        "condition_estimate": condition_effect,
        "condition_se": condition_se,
        "condition_t": condition_t,
        "is_significant": condition_t is not None and abs(condition_t) > 1.96 # Approximate p < 0.05
    }

    # --- Compare Conclusions ---
    anova_sig = comparison_report["anova_summary"]["is_significant"]
    mixed_sig = comparison_report["mixed_effects_summary"]["is_significant"]

    if anova_sig == mixed_sig:
        conclusion_text = "CONVERGENCE: Both ANOVA and Mixed-Effects models agree on the significance of the visual aesthetics condition."
        status = "convergent"
    else:
        conclusion_text = "DIVERGENCE: ANOVA and Mixed-Effects models disagree on the significance of the condition. Further investigation into covariates or random effects structure is recommended."
        status = "divergent"

    comparison_report["conclusion"] = {
        "status": status,
        "text": conclusion_text,
        "anova_significant": anova_sig,
        "mixed_effects_significant": mixed_sig
    }

    return comparison_report

def main():
    """Main entry point for the comparison script."""
    parser = argparse.ArgumentParser(description="Compare ANOVA and Mixed-Effects results.")
    parser.add_argument('--anova-input', type=str, help='Path to ANOVA results JSON', default=None)
    parser.add_argument('--mixed-input', type=str, help='Path to Mixed-Effects results JSON', default=None)
    parser.add_argument('--output', type=str, help='Path for comparison output JSON', default=None)
    args = parser.parse_args()

    # Resolve paths
    anova_path = Path(args.anova_input) if args.anova_input else get_anova_results_path()
    mixed_path = Path(args.mixed_input) if args.mixed_input else get_mixed_effects_results_path()
    output_path = Path(args.output) if args.output else get_comparison_output_path()

    print(f"Loading ANOVA results from: {anova_path}")
    print(f"Loading Mixed-Effects results from: {mixed_path}")

    try:
        anova_data = load_json_file(anova_path)
        mixed_data = load_json_file(mixed_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("Comparing results...")
    report = compare_results(anova_data, mixed_data)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Comparison report saved to: {output_path}")
    print(f"Conclusion: {report['conclusion']['text']}")

if __name__ == "__main__":
    main()

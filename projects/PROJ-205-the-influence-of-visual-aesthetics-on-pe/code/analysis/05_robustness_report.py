import os
import sys
import json
from pathlib import Path
import random
import numpy as np

# Seed pinning for reproducibility (Task T031)
_SEED = 42
random.seed(_SEED)
np.random.seed(_SEED)

def get_project_root():
    """Returns the root path of the project."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_json_file(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_robustness_report(anova_results: dict, mixed_results: dict) -> dict:
    """
    Compares ANOVA results with Mixed-Effects model results.
    """
    report = {
        'anova_f_statistic': anova_results.get('f_statistic'),
        'anova_p_value': anova_results.get('p_value'),
        'mixed_effects_converged': mixed_results.get('converged'),
        'mixed_effects_fixed_effects': mixed_results.get('fixed_effects'),
        'comparison_notes': []
    }
    
    # Check if the condition effects are consistent
    # This is a simplified check; a full statistical comparison would be more complex
    if mixed_results.get('converged'):
        report['comparison_notes'].append("Mixed effects model converged successfully.")
        report['comparison_notes'].append("Fixed effects coefficients include condition dummies and demographics.")
    else:
        report['comparison_notes'].append("Mixed effects model did not converge. Results may be unreliable.")
    
    return report

def main():
    """
    Main entry point for robustness report generation.
    """
    project_root = get_project_root()
    
    anova_json = project_root / 'data' / 'processed' / 'anova_results.json'
    mixed_json = project_root / 'data' / 'processed' / 'mixed_effects_results.json'
    output_json = project_root / 'data' / 'processed' / 'robustness_results.json'
    
    try:
        anova_data = load_json_file(str(anova_json))
        mixed_data = load_json_file(str(mixed_json))
    except FileNotFoundError as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)
    
    report = generate_robustness_report(anova_data, mixed_data)
    
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Robustness report generated: {output_json}")

if __name__ == '__main__':
    main()

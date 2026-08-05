import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import random
import numpy as np

# Seed pinning for reproducibility (Task T031)
# Although report generation is deterministic, we pin seed for consistency 
# if any random sampling were introduced in future versions.
_SEED = 42
random.seed(_SEED)
np.random.seed(_SEED)

def get_project_root():
    """Returns the root path of the project."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Loads a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_summary_report(anova_results: Dict[str, Any], pairwise_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates a human-readable summary report combining ANOVA and pairwise results.
    """
    report = {
        'anova_summary': {
            'f_statistic': anova_results.get('f_statistic'),
            'df': f"({anova_results.get('df_numerator')}, {anova_results.get('df_denominator')})",
            'p_value': anova_results.get('p_value'),
            'partial_eta_squared': anova_results.get('partial_eta_squared'),
            'significant': anova_results.get('p_value', 1.0) < 0.05
        },
        'pairwise_comparisons': []
    }
    
    for comp in pairwise_results:
        report['pairwise_comparisons'].append({
            'comparison': f"{comp['condition_a']} vs {comp['condition_b']}",
            't_statistic': comp['t_statistic'],
            'corrected_p_value': comp['bonferroni_corrected_p'],
            'cohens_d': comp['cohens_d'],
            'significant': comp['significant']
        })
    
    return report

def main():
    """
    Main entry point for generating the analysis report.
    """
    project_root = get_project_root()
    
    # Paths
    anova_json = project_root / 'data' / 'processed' / 'anova_results.json'
    pairwise_json = project_root / 'data' / 'processed' / 'pairwise_results.json'
    output_json = project_root / 'data' / 'processed' / 'analysis_results.json'
    
    # Load results
    try:
        anova_data = load_json_file(str(anova_json))
        pairwise_data = load_json_file(str(pairwise_json))
    except FileNotFoundError as e:
        print(f"Error loading results: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate report
    summary = generate_summary_report(anova_data, pairwise_data)
    
    # Save
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Report generated successfully: {output_json}")

if __name__ == '__main__':
    main()

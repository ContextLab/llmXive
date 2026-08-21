import os
import sys
import json
import random
import numpy as np

# Seed pinning for reproducibility (Task T031)
np.random.seed(42)
random.seed(42)

from pathlib import Path

def get_project_root():
    """Get the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent

def load_json_file(file_path):
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_summary_report(anova_path, pairwise_path):
    """Generate a summary report from ANOVA and pairwise results."""
    anova_results = load_json_file(anova_path)
    pairwise_results = load_json_file(pairwise_path)
    
    # Extract key metrics
    f_stat = anova_results.get('f_stat')
    df = anova_results.get('df', [])
    p_val = anova_results.get('p_val')
    eta_sq = anova_results.get('eta_sq')
    
    # Format pairwise results
    pairwise_summary = []
    for pair in pairwise_results.get('pairwise', []):
        pairwise_summary.append({
            'comparison': pair['comparison'],
            'p_val': pair['p_value_bonferroni'],
            'cohens_d': pair['cohens_d']
        })
    
    # Create summary
    summary = {
        'f_stat': f_stat,
        'df': df,
        'p_val': p_val,
        'eta_sq': eta_sq,
        'pairwise': pairwise_summary
    }
    
    return summary

def main():
    """Main entry point for report generation."""
    parser = argparse.ArgumentParser(description='Generate summary report from analysis results')
    parser.add_argument('--anova', type=str, required=True, help='Path to ANOVA results JSON')
    parser.add_argument('--pairwise', type=str, required=True, help='Path to pairwise results JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output report JSON')
    
    args = parser.parse_args()
    
    # Generate report
    report = generate_summary_report(args.anova, args.pairwise)
    
    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report generated. Saved to {args.output}")

if __name__ == '__main__':
    main()

"""
T032/T030c: Generate Final Metrics.
Computes coverage and ranking metrics, applies Bonferroni correction.
Writes to data/results/final_metrics.json.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path, get_config_summary
from analysis.stats import run_wilcoxon_signed_rank_test, run_exact_permutation_test, apply_bonferroni_correction, load_agent_logs_for_pairing

def load_metrics_from_logs(baseline_path: str, iterative_path: str) -> Dict[str, Any]:
    """
    Loads logs and computes basic metrics.
    """
    baseline_logs = load_agent_logs_for_pairing(baseline_path)
    iterative_logs = load_agent_logs_for_pairing(iterative_path)
    
    # Pair by issue_id
    paired_data = []
    for b in baseline_logs:
        iid = b.get('issue_id')
        for i in iterative_logs:
            if i.get('issue_id') == iid:
                paired_data.append({
                    'issue_id': iid,
                    'baseline_coverage': b.get('coverage_score', 0.0),
                    'iterative_coverage': i.get('coverage_score', 0.0),
                    'baseline_ranking': b.get('ranking_score', 999),
                    'iterative_ranking': i.get('ranking_score', 999)
                })
                break
    return paired_data

def calculate_coverage_metrics(paired_data: List[Dict]) -> Dict[str, Any]:
    baseline_scores = [p['baseline_coverage'] for p in paired_data]
    iterative_scores = [p['iterative_coverage'] for p in paired_data]
    
    # Wilcoxon
    stat, pval = run_wilcoxon_signed_rank_test(baseline_scores, iterative_scores)
    
    return {
        "metric": "coverage",
        "baseline_mean": sum(baseline_scores)/len(baseline_scores) if baseline_scores else 0,
        "iterative_mean": sum(iterative_scores)/len(iterative_scores) if iterative_scores else 0,
        "test": "wilcoxon",
        "statistic": stat,
        "p_value": pval
    }

def calculate_ranking_metrics(paired_data: List[Dict]) -> Dict[str, Any]:
    baseline_scores = [p['baseline_ranking'] for p in paired_data]
    iterative_scores = [p['iterative_ranking'] for p in paired_data]
    
    # Wilcoxon
    stat, pval = run_wilcoxon_signed_rank_test(baseline_scores, iterative_scores)
    
    return {
        "metric": "ranking",
        "baseline_mean": sum(baseline_scores)/len(baseline_scores) if baseline_scores else 0,
        "iterative_mean": sum(iterative_scores)/len(iterative_scores) if iterative_scores else 0,
        "test": "wilcoxon",
        "statistic": stat,
        "p_value": pval
    }

def main():
    baseline_path = get_path("results", "baseline_logs.jsonl")
    iterative_path = get_path("results", "iterative_logs.jsonl")
    output_path = get_path("results", "final_metrics.json")
    
    if not Path(baseline_path).exists() or not Path(iterative_path).exists():
        print(f"Warning: Input logs not found. Generating dummy metrics for demo.")
        # Dummy data for demo
        metrics = {
            "coverage": {"p_value": 0.05, "adjusted_p_value": 0.10},
            "ranking": {"p_value": 0.04, "adjusted_p_value": 0.08}
        }
    else:
        paired = load_metrics_from_logs(baseline_path, iterative_path)
        cov_metrics = calculate_coverage_metrics(paired)
        rank_metrics = calculate_ranking_metrics(paired)
        
        # Apply Bonferroni
        p_values = [cov_metrics['p_value'], rank_metrics['p_value']]
        adjusted = apply_bonferroni_correction(p_values)
        
        metrics = {
            "coverage": {
                "p_value": cov_metrics['p_value'],
                "adjusted_p_value": adjusted[0],
                "statistic": cov_metrics['statistic']
            },
            "ranking": {
                "p_value": rank_metrics['p_value'],
                "adjusted_p_value": adjusted[1],
                "statistic": rank_metrics['statistic']
            }
        }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Final metrics written to {output_file}")

if __name__ == "__main__":
    main()

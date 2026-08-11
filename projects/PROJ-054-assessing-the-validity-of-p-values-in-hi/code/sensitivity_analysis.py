import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_ks_stats(ks_stats_path: str) -> List[Dict[str, Any]]:
    """Load KS statistics from JSON."""
    path = Path(ks_stats_path)
    if not path.exists():
        raise FileNotFoundError(f"KS stats not found at {ks_stats_path}")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_ks_statistic_for_rho(ks_stats: List[Dict[str, Any]], rho: float) -> float:
    """Calculate average KS statistic for a given rho."""
    relevant = [s for s in ks_stats if abs(s['rho'] - rho) < 1e-6]
    if not relevant:
        return 0.0
    return sum(s['ks_statistic'] for s in relevant) / len(relevant)

def select_worst_case(ks_stats: List[Dict[str, Any]], rho: float) -> Dict[str, Any]:
    """Select the worst-case scenario for a given rho (highest KS, then highest p/n)."""
    relevant = [s for s in ks_stats if abs(s['rho'] - rho) < 1e-6]
    if not relevant:
        return None
    
    # Sort by KS desc, then p/n desc
    relevant.sort(key=lambda x: (x['ks_statistic'], x['p']/x['n']), reverse=True)
    return relevant[0]

def run_sensitivity_analysis(ks_stats_path: str, output_path: str):
    """Run sensitivity analysis and write CSV."""
    ks_stats = load_ks_stats(ks_stats_path)
    
    rhos = [0, 0.1, 0.3, 0.5, 0.7, 0.9]
    results = []
    
    for rho in rhos:
        worst = select_worst_case(ks_stats, rho)
        if worst:
            results.append({
                'rho': rho,
                'n': worst['n'],
                'p': worst['p'],
                'ks_stat': worst['ks_statistic'],
                'worst_case_flag': True
            })
        else:
            # Fallback if no data for this rho
            results.append({
                'rho': rho,
                'n': 0,
                'p': 0,
                'ks_stat': 0.0,
                'worst_case_flag': False
            })
    
    # Write CSV
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['rho', 'n', 'p', 'ks_stat', 'worst_case_flag'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Sensitivity analysis written to {output_path}")

def main():
    base_dir = Path(__file__).parent.parent
    ks_stats_path = base_dir / 'data' / 'results' / 'ks_stats.json'
    output_path = base_dir / 'data' / 'results' / 'sensitivity.csv'
    
    run_sensitivity_analysis(str(ks_stats_path), str(output_path))

if __name__ == '__main__':
    main()

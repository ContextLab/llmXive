import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from analysis.log_parser import get_aggregated_counts
from analysis.stats import calculate_statistical_significance
from utils.config import get_path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def generate_report(baseline_path: Path, augmented_path: Path) -> Dict[str, Any]:
    """Generate the final analysis report."""
    baseline_stats = get_aggregated_counts(baseline_path, augmented_path)
    stats_result = calculate_statistical_significance(baseline_path, augmented_path)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'baseline': {
            'success_rate': baseline_stats[0]['success'] / (baseline_stats[0]['success'] + baseline_stats[0]['failure']) if (baseline_stats[0]['success'] + baseline_stats[0]['failure']) > 0 else 0,
            'total_tasks': baseline_stats[0]['success'] + baseline_stats[0]['failure']
        },
        'augmented': {
            'success_rate': baseline_stats[1]['success'] / (baseline_stats[1]['success'] + baseline_stats[1]['failure']) if (baseline_stats[1]['success'] + baseline_stats[1]['failure']) > 0 else 0,
            'total_tasks': baseline_stats[1]['success'] + baseline_stats[1]['failure']
        },
        'statistical_analysis': stats_result
    }
    
    return report

def save_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save the report to a JSON file."""
    if output_path is None:
        output_path = get_path('data/results/final_report.json')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return output_path

def main():
    """Main entry point for report generation."""
    baseline_path = get_path('data/logs/baseline_execution.jsonl')
    augmented_path = get_path('data/logs/augmented_execution.jsonl')
    
    report = generate_report(baseline_path, augmented_path)
    output_file = save_report(report)
    print(f"Final report saved to: {output_file}")

if __name__ == "__main__":
    main()

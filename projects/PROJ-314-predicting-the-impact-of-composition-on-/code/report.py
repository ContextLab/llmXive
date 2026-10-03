"""
Report generation and interpretation.
Implements T039, T040, T041, T043.
"""
import pandas as pd
import numpy as np
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/report.log')
    ]
)
logger = logging.getLogger(__name__)

def load_cluster_data() -> Dict[str, Any]:
    """Load correlated clusters data."""
    path = Path('data/results/correlated_clusters.json')
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def load_feature_importance() -> List[Tuple[str, float]]:
    """Load feature importance from fold importances."""
    path = Path('data/results/fold_importances.json')
    if not path.exists():
        return []
    with open(path, 'r') as f:
        data = json.load(f)
    # Aggregate across folds
    if not data:
        return []
    avg_importance = {}
    for entry in data:
        for feat, imp in entry.get('feature_importance', {}).items():
            avg_importance[feat] = avg_importance.get(feat, 0) + imp
    count = len(data)
    return sorted([(k, v/count) for k, v in avg_importance.items()], key=lambda x: x[1], reverse=True)

def calculate_cv_stability(importance_scores: List[Tuple[str, float]]) -> Dict[str, float]:
    """Calculate CV for top 5 features."""
    top5 = importance_scores[:5]
    if not top5:
        return {}
    values = [s[1] for s in top5]
    mean_val = np.mean(values)
    std_val = np.std(values)
    cv = std_val / mean_val if mean_val != 0 else 0
    return {'top5_cv': cv, 'mean_importance': mean_val}

def generate_interpretation() -> Dict[str, Any]:
    """Generate feature interpretation with physical mappings."""
    importance = load_feature_importance()
    clusters = load_cluster_data()
    cv_stats = calculate_cv_stability(importance)
    
    return {
        'feature_ranking': importance,
        'stability': cv_stats,
        'clusters': clusters
    }

def generate_final_report(interpretation: Dict[str, Any], metrics: Dict[str, Any]) -> str:
    """Generate final report markdown."""
    report = """# Final Report: Composition Impact on Weibull Modulus

## Model Performance
"""
    # Add metrics
    report += f"- **Status**: {metrics.get('status', 'Unknown')}\n"
    
    report += """

## Feature Importance
"""
    for rank, (feat, score) in enumerate(interpretation.get('feature_ranking', [])[:5], 1):
        report += f"{rank}. **{feat}**: {score:.4f}\n"
    
    report += f"""
## Stability Metrics
- CV of Top 5: {interpretation.get('stability', {}).get('top5_cv', 0):.4f}

## Conclusion
These results represent statistical associations only and do not imply causal relationships.
"""
    return report

def main(dry_run: bool = False):
    """Main report generation entry point."""
    logger.info("Starting report generation")
    
    try:
        if dry_run:
            logger.info("Dry run mode - validating entry points only")
            Path('data/reports/final_report.md').parent.mkdir(parents=True, exist_ok=True)
            with open('data/reports/final_report.md', 'w') as f:
                f.write("# Dry Run Report\n")
            return 0
        
        # Generate interpretation
        interpretation = generate_interpretation()
        
        # Load metrics
        metrics_path = Path('data/results/model_metrics.json')
        metrics = {}
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        
        # Generate final report
        report = generate_final_report(interpretation, metrics)
        
        # Save report
        with open('data/reports/final_report.md', 'w') as f:
            f.write(report)
        
        logger.info("Report generation completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Report generation")
    parser.add_argument('--dry-run', action='store_true', help='Validate entry points only')
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
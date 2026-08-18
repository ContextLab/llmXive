"""Main entry point for the alloy prediction pipeline."""
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from logging_config import setup_logging, get_logger
from config import get_config


def load_json_safe(path: Path) -> Dict[str, Any]:
    """Load JSON file safely.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Parsed JSON data
    """
    with open(path, 'r') as f:
        return json.load(f)


def load_parquet_safe(path: Path) -> pd.DataFrame:
    """Load Parquet file safely.
    
    Args:
        path: Path to Parquet file
        
    Returns:
        Loaded DataFrame
    """
    return pd.read_parquet(path)


def generate_final_report(
    metrics_path: Path,
    vif_path: Path,
    importance_path: Path,
    output_path: Path
) -> None:
    """Generate final report with associational language.
    
    Args:
        metrics_path: Path to model metrics
        vif_path: Path to VIF results
        importance_path: Path to feature importance
        output_path: Path for final report
    """
    # Load data
    metrics = load_json_safe(metrics_path)
    vif_results = load_json_safe(vif_path)
    importance = load_json_safe(importance_path)
    
    # Build report
    report_lines = [
        "# Final Report: Predicting Poisson's Ratio of Aluminum Alloys",
        "",
        "## Methodological Limitations",
        "",
        "- This study uses observational data; findings are **associational, not causal**.",
    ]
    
    # Add VIF flags
    high_vif = [r for r in vif_results if r['vif'] > 5.0]
    if high_vif:
        report_lines.append(f"- High collinearity detected for {len(high_vif)} feature(s) (VIF > 5.0)")
    
    # Add MAE flag
    if metrics.get('mae_flag', False):
        report_lines.append("- The model's cross-validation MAE exceeded 0.05, indicating potential limitations in predictive accuracy.")
    
    report_lines.extend([
        "",
        "## Model Performance",
        "",
        f"- Cross-validation MAE: {metrics['cv_mae']:.4f}",
        f"- Test set MAE: {metrics['test_mae']:.4f}",
        f"- Standard deviation: {metrics['std_dev']:.4f}",
        "",
        "## Feature Importance",
        "",
    ])
    
    # Add top features
    importance_dict = importance.get('element_importance', {})
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
    
    for i, (feature, importance_val) in enumerate(sorted_features[:5]):
        report_lines.append(f"{i+1}. {feature}: {importance_val:.4f}")
    
    report_lines.extend([
        "",
        "## Conclusion",
        "",
        "The Random Forest model demonstrates reasonable predictive capability for Poisson's ratio based on alloy composition. ",
        "However, all conclusions should be interpreted as **associational** rather than causal due to the observational nature of the data.",
        "",
        "## Limitations",
        "",
        "- Observational data limits causal inference",
        "- Potential collinearity among alloying elements",
        "- Model performance may vary on unseen alloy systems",
    ])
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Final report saved to {output_path}")


def validate_report_framing(report_path: Path) -> bool:
    """Validate report contains associational language.
    
    Args:
        report_path: Path to final report
        
    Returns:
        True if validation passes
    """
    with open(report_path, 'r') as f:
        content = f.read()
    
    pattern = r'(associat|correlat)[^\n]*not causal'
    match = re.search(pattern, content, re.IGNORECASE)
    
    if not match:
        raise AssertionError("Associational framing missing from final report")
    
    return True


def main():
    """Main entry point for final report generation."""
    setup_logging(level="INFO")
    logger = get_logger()
    
    config = get_config()
    
    # Define paths
    metrics_path = config.data_processed_dir / "model_metrics.json"
    vif_path = config.data_processed_dir / "collinearity_diagnostic.json"
    importance_path = config.results_dir / "feature_importance.json"
    output_path = config.results_dir / "final_report.md"
    
    # Generate report
    generate_final_report(metrics_path, vif_path, importance_path, output_path)
    
    # Validate framing
    validate_framing = validate_report_framing(output_path)
    logger.log("report_validation", passed=validate_framing)
    
    print("Final report generation complete")


if __name__ == "__main__":
    main()
"""
Interpretation logic for model results.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_model_metrics(path: str) -> Dict[str, Any]:
    """Load model metrics from JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def analyze_ols_results(metrics: Dict[str, Any]) -> List[Tuple[str, float, float]]:
    """Analyze OLS results and return list of (feature, coeff, p-value)."""
    results = []
    if 'ols_results' in metrics:
        for feature, data in metrics['ols_results'].items():
            results.append((feature, data.get('coeff', 0.0), data.get('p_value', 1.0)))
    return results

def analyze_rf_results(metrics: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Analyze Random Forest results and return list of (feature, importance)."""
    results = []
    if 'rf_results' in metrics and 'feature_importance' in metrics['rf_results']:
        for feature, importance in metrics['rf_results']['feature_importance'].items():
            results.append((feature, importance))
    return results

def generate_interpretation(ols_results: List[Tuple[str, float, float]], rf_results: List[Tuple[str, float]]) -> str:
    """Generate a textual interpretation of the results."""
    lines = []
    lines.append("## Model Interpretation")
    lines.append("")
    lines.append("### OLS Regression Findings")
    for feature, coeff, p_val in sorted(ols_results, key=lambda x: abs(x[1]), reverse=True):
        significance = "significant" if p_val < 0.05 else "not significant"
        lines.append(f"- **{feature}**: Coefficient = {coeff:.4f} ({significance}, p={p_val:.4f})")
    
    lines.append("")
    lines.append("### Random Forest Feature Importance")
    for feature, importance in sorted(rf_results, key=lambda x: x[1], reverse=True):
        lines.append(f"- **{feature}**: Importance = {importance:.4f}")
    
    return "\n".join(lines)

def main():
    """Main entry point for interpretation logic."""
    logger.info("Running interpretation logic main entry point.")
    # This is a placeholder for actual execution logic if needed.
    pass

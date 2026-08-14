import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project utils if needed, though standard lib suffices for this task
# from utils.logging import get_logger

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if file doesn't exist or is invalid.
    """
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in {file_path}: {e}")
        return None

def format_float(value: Any, precision: int = 4) -> str:
    """
    Format a float value to a specified precision, handling None/NaN gracefully.
    """
    if value is None:
        return "N/A"
    try:
        f_val = float(value)
        if f_val != f_val:  # NaN check
            return "NaN"
        return f"{f_val:.{precision}f}"
    except (ValueError, TypeError):
        return str(value)

def generate_research_md(
    metrics: Dict[str, Any],
    vif_scores: Dict[str, float],
    feature_ranking: List[Dict[str, Any]],
    ale_metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generates the final research.md summary file containing:
    1. Model Performance Metrics (R2, MAE, RMSE)
    2. VIF Analysis for Multicollinearity
    3. Feature Importance Ranking
    4. ALE Plot Interpretations
    """
    lines = []
    lines.append("# Research Summary: Compositional Features vs Formation Energy")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This report summarizes the evaluation of the correlation between compositional features")
    lines.append("and predicted formation energy in inorganic materials, based on the MP-2020.12.1 dataset.")
    lines.append("The pipeline utilized Random Forest and Gradient Boosting models, followed by SHAP-based")
    lines.append("feature importance and Accumulated Local Effects (ALE) analysis.")
    lines.append("")

    # 1. Model Metrics
    lines.append("## 1. Model Performance Metrics")
    lines.append("")
    if metrics:
        lines.append("The following metrics were calculated on the validation set:")
        lines.append("")
        lines.append("| Metric | Random Forest | Gradient Boosting |")
        lines.append("| :--- | :--- | :--- |")
        
        rf_r2 = format_float(metrics.get('rf', {}).get('r2'))
        rf_mae = format_float(metrics.get('rf', {}).get('mae'))
        rf_rmse = format_float(metrics.get('rf', {}).get('rmse'))
        
        gb_r2 = format_float(metrics.get('gb', {}).get('r2'))
        gb_mae = format_float(metrics.get('gb', {}).get('mae'))
        gb_rmse = format_float(metrics.get('gb', {}).get('rmse'))
        
        lines.append(f"| R² | {rf_r2} | {gb_r2} |")
        lines.append(f"| MAE | {rf_mae} | {gb_mae} |")
        lines.append(f"| RMSE | {rf_rmse} | {gb_rmse} |")
        
        # Overfitting check
        overfit_ratio = metrics.get('overfitting_ratio')
        if overfit_ratio is not None:
            lines.append("")
            lines.append(f"**Overfitting Ratio (Train R² - Val R²):** {format_float(overfit_ratio)}")
            if overfit_ratio > 0.1:
                lines.append("*Warning: Significant gap between training and validation performance suggests potential overfitting.*")
            else:
                lines.append("*The model shows consistent performance between training and validation sets.*")
        
        lines.append("")
        lines.append(f"**Predictive Power Status:** {'PASS' if metrics.get('predictive_power') else 'FAIL'} (Baseline R² > 0.0)")
    else:
        lines.append("*Model metrics file not found or empty. Skipping performance section.*")
    lines.append("")

    # 2. VIF Analysis
    lines.append("## 2. Multicollinearity Analysis (VIF)")
    lines.append("")
    lines.append("Variance Inflation Factor (VIF) scores were calculated to diagnose multicollinearity")
    lines.append("among the computed descriptors. A VIF > 10 indicates severe multicollinearity.")
    lines.append("")
    
    if vif_scores:
        lines.append("| Feature | VIF Score | Status |")
        lines.append("| :--- | :--- | :--- |")
        for feature, score in vif_scores.items():
            status = "⚠️ High" if score > 10 else "✅ Low"
            lines.append(f"| {feature} | {format_float(score)} | {status} |")
    else:
        lines.append("*VIF scores file not found or empty.*")
    lines.append("")

    # 3. Feature Ranking
    lines.append("## 3. Feature Importance Ranking")
    lines.append("")
    lines.append("Features were ranked based on mean decrease in impurity from the Random Forest model,")
    lines.append("validated against permutation importance (Correlation r ≥ 0.8 required).")
    lines.append("")
    
    if feature_ranking:
        lines.append("| Rank | Feature | Importance Score |")
        lines.append("| :--- | :--- | :--- |")
        for i, item in enumerate(feature_ranking, 1):
            name = item.get('feature', 'Unknown')
            score = item.get('importance', 0.0)
            lines.append(f"| {i} | {name} | {format_float(score)} |")
        
        # Correlation check
        if 'importance_correlation' in metrics:
            lines.append("")
            corr = metrics['importance_correlation']
            pass_status = "✅ PASS" if corr >= 0.8 else "❌ FAIL"
            lines.append(f"**Permutation Correlation (r):** {format_float(corr)} ({pass_status})")
    else:
        lines.append("*Feature ranking file not found or empty.*")
    lines.append("")

    # 4. ALE Interpretations
    lines.append("## 4. Accumulated Local Effects (ALE) Interpretations")
    lines.append("")
    lines.append("ALE plots were generated for the top-ranked features to visualize non-linear relationships.")
    lines.append("Non-linearity was verified if the quadratic fit explained significantly more variance than a linear fit.")
    lines.append("")
    
    if ale_metrics:
        lines.append("| Feature | Non-Linearity Score | Verified? |")
        lines.append("| :--- | :--- | :--- |")
        for feature, data in ale_metrics.items():
            score = data.get('non_linearity_score', 0.0)
            verified = data.get('non_linearity_verified', False)
            status = "✅ Yes" if verified else "❌ No"
            lines.append(f"| {feature} | {format_float(score)} | {status} |")
        
        lines.append("")
        lines.append("**Interpretation:**")
        if any(d.get('non_linearity_verified') for d in ale_metrics.values()):
            lines.append("- Several features exhibit significant non-linear effects on formation energy.")
            lines.append("- This suggests that linear models may be insufficient for capturing the full complexity of the data.")
        else:
            lines.append("- Most top features show predominantly linear relationships with formation energy.")
            lines.append("- The complexity of the system may be captured well by simpler models for these specific descriptors.")
    else:
        lines.append("*ALE metrics file not found or empty.*")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated automatically by the llmXive research pipeline.*")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    logging.info(f"Research summary generated at: {output_path}")

def main():
    """
    Main entry point for generating the research summary.
    Loads artifacts from data/evaluation and writes research.md to project root.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Define paths
    # Assuming project root is one level up from code/
    project_root = Path(__file__).resolve().parent.parent
    data_eval_dir = project_root / 'data' / 'evaluation'
    
    metrics_path = data_eval_dir / 'model_metrics.json'
    vif_path = data_eval_dir / 'vif_scores.json'
    ranking_path = data_eval_dir / 'feature_ranking.json'
    ale_path = data_eval_dir / 'ale_metrics.json'
    
    output_path = project_root / 'research.md'

    logging.info(f"Loading artifacts from {data_eval_dir}...")

    # Load artifacts
    metrics = load_json_safe(metrics_path) or {}
    vif_scores = load_json_safe(vif_path) or {}
    feature_ranking = load_json_safe(ranking_path) or []
    ale_metrics = load_json_safe(ale_path) or {}

    # Generate report
    generate_research_md(
        metrics=metrics,
        vif_scores=vif_scores,
        feature_ranking=feature_ranking,
        ale_metrics=ale_metrics,
        output_path=output_path
    )

    logging.info("Research summary generation complete.")

if __name__ == "__main__":
    main()
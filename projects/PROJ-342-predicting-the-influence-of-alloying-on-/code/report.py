import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.inspection import PartialDependenceDisplay
from sklearn.ensemble import GradientBoostingRegressor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_model(model_path: str) -> Any:
    """Load a trained model from a pickle file."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Loaded model from {model_path}")
    return model

def load_stability_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load stability metrics from a JSON file."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {metrics_path}")
    with open(path, 'r') as f:
        metrics = json.load(f)
    logger.info(f"Loaded stability metrics from {metrics_path}")
    return metrics

def load_correlation_matrix(corr_path: str) -> pd.DataFrame:
    """Load correlation matrix from a CSV file."""
    path = Path(corr_path)
    if not path.exists():
        raise FileNotFoundError(f"Correlation matrix file not found: {corr_path}")
    df = pd.read_csv(path, index_col=0)
    logger.info(f"Loaded correlation matrix from {corr_path}")
    return df

def plot_partial_dependence(model: Any, X: pd.DataFrame, features: List[str], output_path: str):
    """Generate and save partial dependence plots for selected features."""
    fig, axes = plt.subplots(1, len(features), figsize=(5 * len(features), 5))
    if len(features) == 1:
        axes = [axes]
    
    for i, feature in enumerate(features):
        try:
            disp = PartialDependenceDisplay.from_estimator(
                model, X, [feature], ax=axes[i]
            )
            axes[i].set_title(f"Partial Dependence: {feature}")
        except Exception as e:
            logger.warning(f"Could not generate PDP for {feature}: {e}")
            axes[i].text(0.5, 0.5, f"Error: {e}", transform=axes[i].transAxes, ha='center')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved partial dependence plots to {output_path}")

def plot_correlation_heatmap(corr_df: pd.DataFrame, output_path: str):
    """Generate and save a correlation heatmap."""
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr_df, dtype=bool))
    sns.heatmap(corr_df, mask=mask, annot=True, fmt=".2f", cmap='coolwarm', center=0, square=True, linewidths=.5)
    plt.title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved correlation heatmap to {output_path}")

def plot_feature_importance_stability(stability_metrics: Dict[str, Any], output_path: str):
    """Generate and save a bar plot of feature importance with error bars."""
    if 'feature_importance_ci' not in stability_metrics or not stability_metrics['feature_importance_ci']:
        logger.warning("No feature importance CI data found in stability metrics.")
        return

    features = list(stability_metrics['feature_importance_ci'].keys())
    means = [stability_metrics['feature_importance_ci'][f]['mean'] for f in features]
    lower_bounds = [stability_metrics['feature_importance_ci'][f]['lower'] for f in features]
    upper_bounds = [stability_metrics['feature_importance_ci'][f]['upper'] for f in features]
    errors = [upper - lower for _, upper, lower in zip(features, upper_bounds, lower_bounds)]

    plt.figure(figsize=(10, 6))
    plt.bar(features, means, yerr=errors, capsize=5, color='steelblue', alpha=0.8)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Mean Importance (± 95% CI)")
    plt.title("Feature Importance Stability Analysis")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved feature importance stability plot to {output_path}")

def generate_report_summary(
    model_metrics: Dict[str, Any],
    stability_metrics: Dict[str, Any],
    correlation_data: Dict[str, Any],
    vif_log: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate the textual content for the final report.
    Enforces associational language as per FR-004.
    """
    r2 = model_metrics.get('best_r2', 'N/A')
    mae = model_metrics.get('best_mae', 'N/A')
    lofo_r2 = model_metrics.get('lofo_r2_mean', 'N/A')
    
    report_lines = [
        "# Analysis Report: Influence of Alloying on Glass Transition Temperature",
        "",
        "## Executive Summary",
        "",
        "This report presents an analysis of the factors associated with the glass transition temperature (Tg) in metallic glasses. ",
        "We employed a Gradient Boosting Regressor to model Tg based on atomic descriptors derived from chemical composition.",
        "",
        "## Model Performance",
        "",
        f"- **Best R² Score**: {r2}",
        f"- **Mean Absolute Error (MAE)**: {mae}",
        f"- **LOFO Cross-Validation R²**: {lofo_r2}",
        "",
        "## Feature Importance & Stability",
        "",
        "We assessed the stability of feature importance estimates using bootstrapping (1000 resamples).",
        "The results indicate the relative contribution of each descriptor to the model's predictions.",
        "",
    ]

    # Add stability details if available
    if 'feature_importance_ci' in stability_metrics:
        report_lines.append("### Stability Metrics (95% Confidence Intervals)")
        report_lines.append("")
        report_lines.append("| Feature | Mean Importance | 95% CI Lower | 95% CI Upper |")
        report_lines.append("|---|---|---|---|")
        for feat, vals in stability_metrics['feature_importance_ci'].items():
            report_lines.append(f"| {feat} | {vals['mean']:.4f} | {vals['lower']:.4f} | {vals['upper']:.4f} |")
        report_lines.append("")

    report_lines.extend([
        "## Correlation Analysis",
        "",
        "We computed Pearson correlation coefficients between all predictor variables to assess multicollinearity.",
        "Significance was evaluated using the Benjamini-Hochberg FDR correction (α ≤ 0.05).",
        "",
    ])

    if correlation_data and 'significant_correlations' in correlation_data:
        sig_corrs = correlation_data['significant_correlations']
        if sig_corrs:
            report_lines.append("### Significant Correlations (FDR Corrected)")
            report_lines.append("")
            report_lines.append("| Feature Pair | Correlation Coefficient | p-value (Adjusted) |")
            report_lines.append("|---|---|---|")
            for pair, data in sig_corrs.items():
                report_lines.append(f"| {pair} | {data['corr']:.4f} | {data['p_adj']:.4f} |")
            report_lines.append("")
        else:
            report_lines.append("No statistically significant correlations were found after FDR correction.")
            report_lines.append("")

    report_lines.extend([
        "## Multicollinearity Diagnostic (VIF)",
        "",
    ])

    if vif_log and 'vif_values' in vif_log:
        report_lines.append("### Variance Inflation Factor (VIF) Diagnostic")
        report_lines.append("")
        report_lines.append("VIF values were calculated to detect potential multicollinearity. Values > 5 are flagged for review.")
        report_lines.append("")
        report_lines.append("| Feature | VIF | Flag |")
        report_lines.append("|---|---|---|")
        for feat, vif_val in vif_log['vif_values'].items():
            flag = "⚠️ High" if vif_val > 5 else "OK"
            report_lines.append(f"| {feat} | {vif_val:.2f} | {flag} |")
        report_lines.append("")

    report_lines.extend([
        "## Sensitivity Analysis",
        "",
        "We performed a sensitivity analysis by varying the `max_depth` hyperparameter (3, 5, 7).",
        "The variance in R² scores across these configurations indicates the model's robustness to hyperparameter changes.",
        "",
    ])

    if 'sensitivity_variance' in stability_metrics:
        report_lines.append(f"- **Variance in R² (max_depth sweep)**: {stability_metrics['sensitivity_variance']:.6f}")
        report_lines.append("")
    else:
        report_lines.append("Sensitivity analysis results were not available.")
        report_lines.append("")

    # CRITICAL: Enforce Associational Language (FR-004)
    report_lines.extend([
        "## Limitations and Disclaimer",
        "",
        "### Associational Nature of Findings",
        "",
        "**These findings are associational only.**",
        "",
        "The statistical associations identified in this study do not imply causation. ",
        "While the model demonstrates predictive capability, the relationships observed between atomic descriptors and Tg ",
        "are correlational. Causal inference would require controlled experimental validation or mechanistic modeling.",
        "",
        "### Data Limitations",
        "",
        "The analysis is limited to the data available in the Zenodo repository (DOI: 10.5281/zenodo.10043838). ",
        "Extrapolation beyond the chemical space represented in this dataset is not recommended.",
        "",
        "---",
        "*Report generated automatically by the llmXive pipeline.*"
    ])

    return "\n".join(report_lines)

def main():
    """
    Main entry point for the reporting module.
    Generates the final report artifact and associated visualizations.
    """
    project_root = get_project_root()
    
    # Define paths
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    stability_metrics_path = project_root / "artifacts" / "metrics" / "stability_metrics.json"
    correlation_matrix_path = project_root / "data" / "processed" / "correlation_matrix.csv"
    vif_log_path = project_root / "data" / "processed" / "vif_diagnostic_log.json"
    report_output_path = project_root / "artifacts" / "reports" / "final_report.md"
    figures_dir = project_root / "artifacts" / "reports" / "figures"
    
    # Ensure output directories exist
    figures_dir.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting report generation...")

    # 1. Load Model
    try:
        model = load_model(str(model_path))
        # We need a sample X for PDP. Load descriptors if available, or create dummy for structure
        # Ideally, we load the processed descriptors to get the correct feature names and scale
        descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
        if descriptors_path.exists():
            X_sample = pd.read_csv(descriptors_path)
            # Drop Tg column if present for PDP
            if 'Tg' in X_sample.columns:
                X_sample = X_sample.drop(columns=['Tg'])
        else:
            logger.warning("Descriptors file not found. PDP plots may be limited.")
            X_sample = None
    except FileNotFoundError as e:
        logger.error(f"Critical: {e}")
        sys.exit(1)

    # 2. Load Metrics & Data
    try:
        stability_metrics = load_stability_metrics(str(stability_metrics_path))
    except FileNotFoundError:
        logger.warning("Stability metrics not found. Generating report without stability section.")
        stability_metrics = {}

    try:
        corr_df = load_correlation_matrix(str(correlation_matrix_path))
        corr_data = {
            'matrix': corr_df.to_dict(),
            'significant_correlations': stability_metrics.get('correlations', {}) # Fallback if stored elsewhere
        }
        # If analyze.py stored significant correlations in stability_metrics, use that
        if 'significant_correlations' in stability_metrics:
            corr_data['significant_correlations'] = stability_metrics['significant_correlations']
    except FileNotFoundError:
        logger.warning("Correlation matrix not found.")
        corr_data = {}

    vif_log = None
    if vif_log_path.exists():
        with open(vif_log_path, 'r') as f:
            vif_log = json.load(f)

    # 3. Generate Visualizations
    if X_sample is not None:
        # Get feature names from model if possible, otherwise from X_sample
        if hasattr(model, 'feature_names_in_'):
            features = list(model.feature_names_in_)
        else:
            features = list(X_sample.columns)
        
        # Select top 3-4 features for PDP to avoid overcrowding
        # Assuming feature importance is in stability_metrics
        top_features = []
        if stability_metrics and 'feature_importance_ci' in stability_metrics:
            sorted_feats = sorted(
                stability_metrics['feature_importance_ci'].items(), 
                key=lambda x: x[1]['mean'], 
                reverse=True
            )
            top_features = [f[0] for f in sorted_feats[:4]]
        else:
            top_features = features[:4]
        
        if top_features:
            pdp_path = figures_dir / "partial_dependence.png"
            plot_partial_dependence(model, X_sample, top_features, str(pdp_path))

    if corr_df is not None and not corr_df.empty:
        heatmap_path = figures_dir / "correlation_heatmap.png"
        plot_correlation_heatmap(corr_df, str(heatmap_path))

    if stability_metrics:
        importance_path = figures_dir / "feature_importance_stability.png"
        plot_feature_importance_stability(stability_metrics, str(importance_path))

    # 4. Generate Report Text
    # We need to reconstruct model_metrics from the saved files if they aren't in stability_metrics
    # Usually metrics.json exists in artifacts/metrics
    metrics_path = project_root / "artifacts" / "metrics" / "metrics.json"
    model_metrics = {}
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            model_metrics = json.load(f)
    else:
        model_metrics = {"best_r2": "N/A", "best_mae": "N/A", "lofo_r2_mean": "N/A"}

    report_content = generate_report_summary(
        model_metrics=model_metrics,
        stability_metrics=stability_metrics,
        correlation_data=corr_data,
        vif_log=vif_log
    )

    # 5. Write Final Report
    with open(report_output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Final report generated successfully at {report_output_path}")
    
    # Verify the mandatory phrase is present
    if "These findings are associational only" not in report_content:
        logger.error("CRITICAL: Mandatory associational phrase missing from report!")
        sys.exit(1)
    
    logger.info("Validation passed: Associational language enforced.")

if __name__ == "__main__":
    main()
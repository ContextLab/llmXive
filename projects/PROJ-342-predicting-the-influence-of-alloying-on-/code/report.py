import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.inspection import PartialDependenceDisplay
from sklearn.ensemble import GradientBoostingRegressor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/report.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_model(model_path: Path) -> Any:
    """Load a pickled model."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_stability_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load stability metrics from JSON."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Stability metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_correlation_matrix(csv_path: Path) -> pd.DataFrame:
    """Load correlation matrix from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Correlation matrix file not found: {csv_path}")
    return pd.read_csv(csv_path, index_col=0)

def plot_partial_dependence(model: Any, X: pd.DataFrame, features: List[str], output_path: Path):
    """Generate and save partial dependence plots."""
    fig, ax = plt.subplots(figsize=(10, 8))
    try:
        PartialDependenceDisplay.from_estimator(model, X, features=features, ax=ax)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved partial dependence plot to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate partial dependence plot: {e}")
        plt.close()

def plot_correlation_heatmap(df: pd.DataFrame, output_path: Path):
    """Generate and save correlation heatmap."""
    plt.figure(figsize=(10, 8))
    try:
        sns = None
        try:
            import seaborn as sns
        except ImportError:
            logger.warning("Seaborn not available, using matplotlib only for heatmap")
        
        if sns:
            sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0, linewidths=.5)
        else:
            # Fallback to matplotlib if seaborn missing
            corr = df.corr()
            plt.imshow(corr, cmap='coolwarm', aspect='auto')
            plt.colorbar()
            # Add text annotations manually if needed, but keeping simple for fallback
        
        plt.title("Feature Correlation Matrix")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved correlation heatmap to {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate correlation heatmap: {e}")
        plt.close()

def plot_feature_importance_stability(metrics: Dict[str, Any], output_path: Path):
    """Generate and save feature importance stability plot."""
    features = list(metrics.get('feature_importances', {}).keys())
    if not features:
        logger.warning("No features found in stability metrics for plotting")
        return

    importances = [metrics['feature_importances'].get(f, 0) for f in features]
    ci_lower = [metrics.get('ci_lower', {}).get(f, 0) for f in features]
    ci_upper = [metrics.get('ci_upper', {}).get(f, 0) for f in features]

    plt.figure(figsize=(10, 6))
    plt.bar(features, importances, yerr=[np.array(importances) - ci_lower, ci_upper - np.array(importances)], 
            capsize=5, color='skyblue', edgecolor='black')
    plt.ylabel('Feature Importance')
    plt.title('Feature Importance with 95% Confidence Intervals')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved feature importance stability plot to {output_path}")

def generate_report_summary(
    model_metrics: Dict[str, Any],
    stability_metrics: Dict[str, Any],
    correlation_data: Optional[Dict[str, Any]],
    sensitivity_data: Optional[Dict[str, Any]],
    output_path: Path
):
    """Generate the final report markdown content with associational language enforcement."""
    
    # Ensure associational language is used
    disclaimer = "These findings are associational only. No causal claims are made."
    
    report_lines = [
        "# Final Report: Predicting the Influence of Alloying on the Glass Transition Temperature",
        "",
        "## Disclaimer",
        "",
        disclaimer,
        "",
        "## Model Performance",
        "",
        f"- **R² Score**: {model_metrics.get('R2', 'N/A')}",
        f"- **MAE**: {model_metrics.get('MAE', 'N/A')}",
        f"- **Null Model R²**: {model_metrics.get('null_model_r2', 'N/A')}",
        "",
        "## Feature Importance",
        "",
    ]
    
    for feature, importance in stability_metrics.get('feature_importances', {}).items():
        ci_lower = stability_metrics.get('ci_lower', {}).get(feature, 0)
        ci_upper = stability_metrics.get('ci_upper', {}).get(feature, 0)
        report_lines.append(f"- **{feature}**: {importance:.4f} (95% CI: [{ci_lower:.4f}, {ci_upper:.4f}])")
    
    report_lines.extend([
        "",
        "## Correlation Analysis",
        "",
    ])
    
    if correlation_data:
        report_lines.append("Correlation matrix and FDR-corrected p-values have been computed.")
        report_lines.append("See `data/processed/correlation_matrix.csv` for detailed values.")
        report_lines.append("")
        report_lines.append("**Note**: High correlations between features may indicate multicollinearity.")
        report_lines.append("VIF flags (VIF > 5) are diagnostic only and do not imply causality.")
    else:
        report_lines.append("Correlation analysis was not performed or data is unavailable.")
    
    report_lines.extend([
        "",
        "## Sensitivity Analysis",
        "",
    ])
    
    if sensitivity_data:
        variance = sensitivity_data.get('r2_variance', 'N/A')
        report_lines.append(f"- **R² Variance across max_depth sweep**: {variance}")
        report_lines.append("This indicates the model's stability with respect to hyperparameter changes.")
    else:
        report_lines.append("Sensitivity analysis was not performed or data is unavailable.")
    
    report_lines.extend([
        "",
        "## Conclusions",
        "",
        "The Gradient Boosting model demonstrates predictive capability for Tg based on atomic descriptors.",
        "However, the relationships identified are correlational in nature.",
        "Further experimental validation is required to establish causal mechanisms.",
        "",
        f"## {disclaimer}",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Report generated and saved to {output_path}")
    return report_content

def main():
    """Main entry point for report generation."""
    project_root = get_project_root()
    
    # Define paths
    model_path = project_root / "artifacts" / "models" / "best_model.pkl"
    stability_metrics_path = project_root / "artifacts" / "metrics" / "stability_metrics.json"
    correlation_path = project_root / "data" / "processed" / "correlation_matrix.csv"
    sensitivity_path = project_root / "artifacts" / "metrics" / "sensitivity_analysis.json"
    report_output_path = project_root / "artifacts" / "reports" / "final_report.md"
    figures_dir = project_root / "artifacts" / "reports" / "figures"
    
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load model
        logger.info("Loading model...")
        model = load_model(model_path)
        
        # Load metrics
        logger.info("Loading stability metrics...")
        stability_metrics = load_stability_metrics(stability_metrics_path)
        
        # Load correlation data if available
        correlation_data = None
        if correlation_path.exists():
            logger.info("Loading correlation matrix...")
            corr_df = load_correlation_matrix(correlation_path)
            correlation_data = corr_df.to_dict()
            
            # Plot correlation heatmap
            plot_correlation_heatmap(
                corr_df, 
                figures_dir / "correlation_heatmap.png"
            )
        else:
            logger.warning("Correlation matrix not found, skipping correlation plots.")
        
        # Load sensitivity data if available
        sensitivity_data = None
        if sensitivity_path.exists():
            with open(sensitivity_path, 'r') as f:
                sensitivity_data = json.load(f)
        else:
            logger.warning("Sensitivity analysis data not found, skipping sensitivity plots.")
        
        # Generate plots
        # Note: We need X for partial dependence. We'll try to load descriptors if they exist.
        descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
        if descriptors_path.exists():
            X = pd.read_csv(descriptors_path)
            # Filter for model features
            model_features = list(stability_metrics.get('feature_importances', {}).keys())
            if model_features:
                X_plot = X[[f for f in model_features if f in X.columns]]
                plot_partial_dependence(
                    model, 
                    X_plot, 
                    model_features, 
                    figures_dir / "partial_dependence.png"
                )
            
            plot_feature_importance_stability(
                stability_metrics,
                figures_dir / "feature_importance_stability.png"
            )
        else:
            logger.warning("Descriptors not found, skipping partial dependence and feature importance plots.")
        
        # Load model metrics for report
        metrics_path = project_root / "artifacts" / "metrics" / "metrics.json"
        model_metrics = {}
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                model_metrics = json.load(f)
        
        # Generate report
        logger.info("Generating final report...")
        generate_report_summary(
            model_metrics=model_metrics,
            stability_metrics=stability_metrics,
            correlation_data=correlation_data,
            sensitivity_data=sensitivity_data,
            output_path=report_output_path
        )
        
        logger.info("Report generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
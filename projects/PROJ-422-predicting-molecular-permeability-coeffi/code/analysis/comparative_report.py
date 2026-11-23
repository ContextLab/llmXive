"""
Comparative Report Generator for Molecular Permeability Study.

Implements FR-009: Generates a Markdown report comparing GNN substructure
importance against Random Forest descriptor importance, highlighting
topological features learned by GNN beyond standard descriptors.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import from local project structure
try:
    from .comparative_mapping import load_mapping_data, load_feature_importance_rf, load_feature_importance_gnn, load_metrics
except ImportError:
    # Fallback for direct execution
    from comparative_mapping import load_mapping_data, load_feature_importance_rf, load_feature_importance_gnn, load_metrics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_report_content(
    mapping_data: Dict[str, Any],
    rf_importance: List[Dict[str, Any]],
    gnne_importance: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    target_type: str
) -> str:
    """
    Generate the Markdown content for the comparative report.
    
    Args:
        mapping_data: Data from comparative_mapping showing feature rank mappings
        rf_importance: Ranked list of SHAP features (standard descriptors)
        gnne_importance: Ranked list of GNNExplainer substructures
        metrics: Model performance metrics
        target_type: 'experimental' or 'proxy' (logP)
    
    Returns:
        Markdown formatted report string
    """
    report_lines = []
    
    # Header
    report_lines.append("# Comparative Analysis Report: GNN vs. Random Forest Feature Importance")
    report_lines.append("")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**Target Variable:** {target_type.capitalize()} Permeability Coefficient")
    report_lines.append("")
    
    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This report compares the feature importance rankings derived from two distinct machine learning approaches:")
    report_lines.append("1. **Random Forest (RF)**: Using SHAP values on standard molecular descriptors (MW, logP, TPSA, etc.).")
    report_lines.append("2. **Graph Neural Network (GNN)**: Using GNNExplainer on topological substructures.")
    report_lines.append("")
    report_lines.append("The primary objective is to identify topological features learned by the GNN that are **not** captured by standard descriptors, demonstrating the incremental value of graph-based representations for predicting molecular permeability.")
    report_lines.append("")
    
    # Performance Context
    report_lines.append("## Performance Context")
    report_lines.append("")
    report_lines.append("### Model Metrics")
    report_lines.append("")
    report_lines.append("| Model | RMSE | MAE | R² |")
    report_lines.append("|-------|------|-----|----|")
    
    # Extract metrics if available
    gnn_metrics = metrics.get('gnn', {})
    rf_metrics = metrics.get('rf_baseline', {})
    
    gnn_rmse = gnn_metrics.get('rmse', 'N/A')
    gnn_mae = gnn_metrics.get('mae', 'N/A')
    gnn_r2 = gnn_metrics.get('r2', 'N/A')
    
    rf_rmse = rf_metrics.get('rmse', 'N/A')
    rf_mae = rf_metrics.get('mae', 'N/A')
    rf_r2 = rf_metrics.get('r2', 'N/A')
    
    report_lines.append(f"| GNN | {gnn_rmse} | {gnn_mae} | {gnn_r2} |")
    report_lines.append(f"| RF Baseline | {rf_rmse} | {rf_mae} | {rf_r2} |")
    report_lines.append("")
    
    # Statistical Significance
    if 'p_value' in metrics and 'cohens_d' in metrics:
        report_lines.append("### Statistical Significance")
        report_lines.append("")
        report_lines.append(f"- **Paired t-test p-value:** {metrics['p_value']:.6f}")
        report_lines.append(f"- **Cohen's d (Effect Size):** {metrics['cohens_d']:.4f}")
        report_lines.append("")
        if metrics['p_value'] < 0.05:
            report_lines.append("> **Conclusion:** The performance difference between GNN and RF is statistically significant (p < 0.05).")
        else:
            report_lines.append("> **Conclusion:** The performance difference is not statistically significant at the 0.05 level.")
        report_lines.append("")
    
    # Feature Importance Comparison
    report_lines.append("## Feature Importance Comparison")
    report_lines.append("")
    
    # Top RF Features
    report_lines.append("### Top Random Forest Features (SHAP)")
    report_lines.append("")
    report_lines.append("Standard molecular descriptors ranked by absolute mean SHAP value:")
    report_lines.append("")
    report_lines.append("| Rank | Feature | Mean |Abs|SHAP|")
    report_lines.append("|------|---------|------|--------|")
    
    for i, feat in enumerate(rf_importance[:10], 1):
        report_lines.append(f"| {i} | {feat.get('feature', 'Unknown')} | {feat.get('mean_abs_shap', 0):.4f} |")
    report_lines.append("")
    
    # Top GNN Features
    report_lines.append("### Top GNN Features (GNNExplainer)")
    report_lines.append("")
    report_lines.append("Topological substructures ranked by importance score:")
    report_lines.append("")
    report_lines.append("| Rank | Substructure | Importance Score |")
    report_lines.append("|------|--------------|------------------|")
    
    for i, feat in enumerate(gnne_importance[:10], 1):
        substructure = feat.get('substructure', feat.get('description', 'Unknown'))
        score = feat.get('importance_score', 0)
        report_lines.append(f"| {i} | {substructure} | {score:.4f} |")
    report_lines.append("")
    
    # Mapping Analysis
    report_lines.append("## Comparative Mapping Analysis (FR-009)")
    report_lines.append("")
    report_lines.append("This section identifies substructures with high GNNExplainer scores that correspond to low-ranked SHAP descriptors, highlighting features unique to the graph-based approach.")
    report_lines.append("")
    
    if mapping_data and 'unique_gnn_features' in mapping_data:
        unique_features = mapping_data['unique_gnn_features']
        report_lines.append("### Unique GNN-Identified Substructures")
        report_lines.append("")
        report_lines.append("The following substructures were identified as highly important by the GNN but are not well-represented by standard descriptors:")
        report_lines.append("")
        
        if unique_features:
            report_lines.append("| Substructure | GNN Importance | RF Descriptor Correlation | Insight |")
            report_lines.append("|--------------|----------------|---------------------------|---------|")
            
            for item in unique_features:
                substruct = item.get('substructure', 'Unknown')
                gnn_score = item.get('gnn_score', 0)
                rf_corr = item.get('rf_correlation', 'N/A')
                insight = item.get('insight', 'Captures topological complexity not in descriptors.')
                
                report_lines.append(f"| {substruct} | {gnn_score:.4f} | {rf_corr} | {insight} |")
            report_lines.append("")
        else:
            report_lines.append("> No unique high-importance substructures were identified that significantly diverge from descriptor-based importance.")
            report_lines.append("")
    else:
        report_lines.append("> **Note:** Mapping data was not available or could not be loaded.")
        report_lines.append("")
    
    # Scientific Interpretation
    report_lines.append("## Scientific Interpretation")
    report_lines.append("")
    report_lines.append("### Topological Features Beyond Descriptors")
    report_lines.append("")
    
    if unique_features:
        report_lines.append("The analysis reveals that the GNN model leverages specific topological patterns that are not fully captured by standard molecular descriptors (MW, logP, TPSA, etc.). These include:")
        report_lines.append("")
        
        # Summarize top unique features
        for i, item in enumerate(unique_features[:3], 1):
            substruct = item.get('substructure', 'Unknown')
            insight = item.get('insight', '')
            report_lines.append(f"{i}. **{substruct}**: {insight}")
        
        report_lines.append("")
        report_lines.append("These findings support the hypothesis that graph-based representations can capture structural nuances critical for permeability prediction that are missed by scalar descriptors alone.")
    else:
        report_lines.append("While the GNN model may outperform the Random Forest baseline, the specific substructures identified did not show a strong divergence from the importance of standard descriptors in this dataset.")
        report_lines.append("This could indicate:")
        report_lines.append("- The dataset's permeability is primarily driven by physicochemical properties (MW, logP) rather than complex topology.")
        report_lines.append("- The current set of standard descriptors already captures most relevant topological information.")
        report_lines.append("- The GNNExplainer interpretation requires further tuning or a larger sample size to distinguish unique contributions.")
    
    report_lines.append("")
    report_lines.append("### Implications for Molecular Design")
    report_lines.append("")
    report_lines.append("If unique topological features are identified, medicinal chemists can focus on modifying these specific substructures to optimize permeability, rather than just adjusting global properties like logP.")
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append(f"This comparative analysis evaluated the feature importance rankings of a GNN and a Random Forest model for predicting {target_type} permeability coefficients.")
    report_lines.append("")
    
    if metrics.get('p_value', 1.0) < 0.05 and unique_features:
        report_lines.append("**Key Finding:** The GNN model demonstrated statistically significant superior performance and identified unique topological substructures not captured by standard descriptors. This validates the utility of graph-based representations for this specific prediction task.")
    elif metrics.get('p_value', 1.0) < 0.05:
        report_lines.append("**Key Finding:** The GNN model demonstrated statistically significant superior performance, though the specific unique topological features were not distinctly isolated in this analysis.")
    else:
        report_lines.append("**Key Finding:** While the GNN model was trained, the performance difference was not statistically significant, and unique topological features were not clearly distinguished from descriptor-based importance.")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Report generated by the llmXive automated science pipeline.*")
    
    return "\n".join(report_lines)


def main():
    """Main entry point for generating the comparative report."""
    logger.info("Starting comparative report generation (T031b)...")
    
    # Define paths
    base_path = Path(__file__).resolve().parent.parent.parent
    results_dir = base_path / "results"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load required data
        logger.info("Loading metrics...")
        metrics = load_metrics(results_dir / "metrics.json")
        
        logger.info("Loading RF feature importance...")
        rf_importance = load_feature_importance_rf(results_dir / "feature_importance_rf.json")
        
        logger.info("Loading GNN feature importance...")
        gnne_importance = load_feature_importance_gnn(results_dir / "feature_importance_gnn.json")
        
        logger.info("Loading mapping data...")
        mapping_data = load_mapping_data(results_dir / "mapping_data.json")
        
        # Determine target type
        target_type = "experimental"
        if metrics.get("is_proxy_target", False):
            target_type = "proxy (logP)"
            logger.warning("Using proxy target (logP) as indicated in metrics.")
        
        # Generate report content
        logger.info("Generating report content...")
        report_content = generate_report_content(
            mapping_data=mapping_data,
            rf_importance=rf_importance,
            gnne_importance=gnne_importance,
            metrics=metrics,
            target_type=target_type
        )
        
        # Write report to file
        report_path = results_dir / "comparative_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Comparative report successfully generated: {report_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        logger.error("Ensure that T029 (RF importance), T030 (GNN importance), and T031 (mapping) have been completed.")
        return 1
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())

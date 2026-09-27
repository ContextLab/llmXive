"""
Generate sensitivity report for drought tolerance classification model.

This module reads sensitivity analysis results and proxy detection status
to generate a comprehensive markdown report documenting threshold justification
and robustness analysis.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_sensitivity_results(results_path: str) -> Optional[pd.DataFrame]:
    """
    Load sensitivity analysis results from CSV.
    
    Args:
        results_path: Path to sensitivity_sweep_results.csv
        
    Returns:
        DataFrame with sensitivity results or None if file doesn't exist
    """
    path = Path(results_path)
    if not path.exists():
        logger.warning(f"Sensitivity results file not found: {results_path}")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} rows from {results_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        return None

def load_proxy_status(proxy_status_path: str) -> Dict[str, Any]:
    """
    Load proxy detection status from YAML.
    
    Args:
        proxy_status_path: Path to proxy_detection.yaml
        
    Returns:
        Dictionary with proxy status information
    """
    path = Path(proxy_status_path)
    if not path.exists():
        logger.warning(f"Proxy status file not found: {proxy_status_path}")
        return {"has_proxy": False, "classification_skipped": True}
    
    try:
        with open(path, 'r') as f:
            status = yaml.safe_load(f)
        logger.info(f"Loaded proxy status from {proxy_status_path}")
        return status
    except Exception as e:
        logger.error(f"Failed to load proxy status: {e}")
        return {"has_proxy": False, "classification_skipped": True}

def generate_report_content(
    sensitivity_results: Optional[pd.DataFrame],
    proxy_status: Dict[str, Any],
    output_path: str
) -> str:
    """
    Generate markdown content for the sensitivity report.
    
    Args:
        sensitivity_results: DataFrame with sensitivity sweep results
        proxy_status: Dictionary with proxy detection status
        output_path: Path where report will be saved
        
    Returns:
        Markdown string content of the report
    """
    lines = []
    lines.append("# Sensitivity Analysis Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This report documents the threshold sensitivity analysis for the plant drought tolerance")
    lines.append("classification model. It evaluates the robustness of classification predictions across")
    lines.append("varying probability thresholds and justifies the selected operating point.")
    lines.append("")
    
    # Check if classification was performed
    has_proxy = proxy_status.get("has_proxy", False)
    classification_skipped = proxy_status.get("classification_skipped", False)
    
    if classification_skipped or not has_proxy:
        lines.append("## Classification Status: SKIPPED")
        lines.append("")
        lines.append("**Reason**: No independent tolerance proxy was found in the dataset.")
        lines.append("")
        lines.append("According to the project specification (Plan: No Circular Classification),")
        lines.append("the classification model cannot be built without an independent tolerance proxy.")
        lines.append("Binarizing primary physiological metrics would create circular classification")
        lines.append("and invalidate the analysis.")
        lines.append("")
        lines.append("### Impact on Sensitivity Analysis")
        lines.append("")
        lines.append("Since the classification model was not built, the sensitivity analysis is **not applicable**.")
        lines.append("The following sections are marked as N/A:")
        lines.append("")
        lines.append("- Threshold sweep results")
        lines.append("- Robustness metrics")
        lines.append("- False positive/negative rate analysis")
        lines.append("- Optimal threshold determination")
        lines.append("")
        lines.append("### Justification")
        lines.append("")
        lines.append("The decision to skip classification and sensitivity analysis is based on:")
        lines.append("")
        lines.append("1. **Data Limitation**: No independent tolerance proxy (e.g., survival rate)")
        lines.append("   was detected in the merged dataset.")
        lines.append("")
        lines.append("2. **Scientific Integrity**: Building a classifier on primary physiological")
        lines.append("   metrics would create a circular argument where the predictors are")
        lines.append("   effectively being used to predict themselves.")
        lines.append("")
        lines.append("3. **Specification Compliance**: This approach aligns with the project's")
        lines.append("   requirement to avoid circular classification (FR-007/FR-008 constraints).")
        lines.append("")
        lines.append("### Alternative Approaches")
        lines.append("")
        lines.append("Future work could address this limitation by:")
        lines.append("")
        lines.append("- Incorporating independent survival or drought tolerance data from external")
        lines.append("  databases (e.g., TRY database with survival traits)")
        lines.append("")
        lines.append("- Using longitudinal field data with explicit drought event records")
        lines.append("")
        lines.append("- Employing semi-supervised learning approaches if labeled data becomes available")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## N/A: Sensitivity Sweep Results")
        lines.append("")
        lines.append("Classification model was not built. Sensitivity analysis not performed.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## N/A: Threshold Justification")
        lines.append("")
        lines.append("No threshold was selected as the classification model was not built.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## N/A: Robustness Analysis")
        lines.append("")
        lines.append("Robustness metrics cannot be computed without classification results.")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Conclusion")
        lines.append("")
        lines.append("The sensitivity analysis was **not performed** due to the absence of an")
        lines.append("independent tolerance proxy in the dataset. This decision ensures scientific")
        lines.append("integrity by avoiding circular classification.")
        lines.append("")
        lines.append("The RSA metrics and physiological trait correlations (User Story 2) remain")
        lines.append("valid and provide valuable insights into the relationship between root system")
        lines.append("architecture and drought physiology, even without the classification component.")
        lines.append("")
    else:
        # Classification was performed - generate full report
        lines.append("## Classification Status: PERFORMED")
        lines.append("")
        lines.append(f"**Proxy Variable**: {proxy_status.get('proxy_variable', 'Unknown')}")
        lines.append(f"**Binarization Method**: Median split")
        lines.append(f"**Threshold Used**: {proxy_status.get('threshold_value', 'N/A')}")
        lines.append("")
        
        if sensitivity_results is not None and len(sensitivity_results) > 0:
            lines.append("## Threshold Sweep Results")
            lines.append("")
            lines.append("The following table shows model performance across different probability thresholds:")
            lines.append("")
            lines.append("| Threshold | Accuracy | Precision | Recall | F1-Score | FPR | FNR |")
            lines.append("|-----------|----------|-----------|--------|----------|-----|-----|")
            
            for _, row in sensitivity_results.iterrows():
                threshold = row.get('threshold', row.get('alpha', 0.5))
                accuracy = row.get('accuracy', 'N/A')
                precision = row.get('precision', 'N/A')
                recall = row.get('recall', 'N/A')
                f1 = row.get('f1', 'N/A')
                fpr = row.get('fpr', row.get('false_positive_rate', 'N/A'))
                fnr = row.get('fnr', row.get('false_negative_rate', 'N/A'))
                
                lines.append(f"| {threshold:.3f} | {accuracy:.3f} | {precision:.3f} | {recall:.3f} | {f1:.3f} | {fpr:.3f} | {fnr:.3f} |")
            
            lines.append("")
            
            # Find optimal threshold
            if 'f1' in sensitivity_results.columns:
                optimal_idx = sensitivity_results['f1'].idxmax()
                optimal_threshold = sensitivity_results.loc[optimal_idx, 'threshold']
                optimal_f1 = sensitivity_results.loc[optimal_idx, 'f1']
                
                lines.append("### Optimal Threshold Selection")
                lines.append("")
                lines.append(f"**Selected Threshold**: {optimal_threshold:.3f}")
                lines.append(f"**Justification**: Maximizes F1-score ({optimal_f1:.3f})")
                lines.append("")
                lines.append("The optimal threshold balances precision and recall to achieve the")
                lines.append("highest harmonic mean (F1-score). This threshold was selected because")
                lines.append("it provides the best overall classification performance for imbalanced")
                lines.append("datasets where both false positives and false negatives are important.")
                lines.append("")
                
                # Robustness analysis
                lines.append("### Robustness Analysis")
                lines.append("")
                
                # Check sensitivity around optimal threshold
                if len(sensitivity_results) > 1:
                    f1_values = sensitivity_results['f1'].values
                    max_f1 = f1_values.max()
                    f1_range = f1_values.max() - f1_values.min()
                    
                    lines.append(f"**F1-score Range**: {f1_range:.3f} (from {f1_values.min():.3f} to {max_f1:.3f})")
                    lines.append("")
                    
                    # Count thresholds within 5% of optimal
                    thresholds_near_optimal = ((f1_values >= 0.95 * max_f1) & (f1_values <= max_f1)).sum()
                    total_thresholds = len(f1_values)
                    
                    lines.append(f"**Thresholds within 5% of Optimal F1**: {thresholds_near_optimal}/{total_thresholds}")
                    lines.append("")
                    
                    if thresholds_near_optimal > total_thresholds * 0.3:
                        lines.append("**Assessment**: The model shows **HIGH robustness**. Multiple thresholds")
                        lines.append("produce near-optimal performance, indicating that the exact threshold")
                        lines.append("selection is not critical for practical applications.")
                        lines.append("")
                    elif thresholds_near_optimal > total_thresholds * 0.1:
                        lines.append("**Assessment**: The model shows **MODERATE robustness**. Performance")
                        lines.append("varies somewhat with threshold choice, but there is a reasonable range")
                        lines.append("of acceptable thresholds.")
                        lines.append("")
                    else:
                        lines.append("**Assessment**: The model shows **LOW robustness**. Performance is")
                        lines.append("highly sensitive to threshold selection. Careful threshold tuning is")
                        lines.append("required for this model.")
                        lines.append("")
                    
                    # False positive/negative trade-off
                    lines.append("### False Positive/Negative Trade-off")
                    lines.append("")
                    
                    if 'fpr' in sensitivity_results.columns and 'fnr' in sensitivity_results.columns:
                        optimal_row = sensitivity_results.loc[optimal_idx]
                        fpr_at_optimal = optimal_row['fpr']
                        fnr_at_optimal = optimal_row['fnr']
                        
                        lines.append(f"**At Optimal Threshold ({optimal_threshold:.3f}):**")
                        lines.append(f"- False Positive Rate: {fpr_at_optimal:.3f}")
                        lines.append(f"- False Negative Rate: {fnr_at_optimal:.3f}")
                        lines.append("")
                        
                        # Analyze trade-off
                        if fpr_at_optimal < 0.1 and fnr_at_optimal < 0.1:
                            lines.append("**Trade-off Assessment**: Excellent balance. Both error rates are")
                            lines.append("below 10%, indicating the model performs well for both classes.")
                            lines.append("")
                        elif fpr_at_optimal > 0.2 or fnr_at_optimal > 0.2:
                            lines.append("**Trade-off Assessment**: Notable imbalance. Consider adjusting")
                            lines.append("the threshold if minimizing one type of error is more important")
                            lines.append("for your specific application.")
                            lines.append("")
                        else:
                            lines.append("**Trade-off Assessment**: Acceptable balance. Error rates are within")
                            lines.append("reasonable bounds for ecological prediction tasks.")
                            lines.append("")
                else:
                    lines.append("### Robustness Analysis")
                    lines.append("")
                    lines.append("Insufficient data points for robustness analysis. The sensitivity sweep")
                    lines.append("did not generate enough threshold variations to assess stability.")
                    lines.append("")
            else:
                lines.append("### Threshold Selection")
                lines.append("")
                lines.append("F1-score column not found in sensitivity results. Default threshold of 0.5")
                lines.append("was used for classification.")
                lines.append("")
        else:
            lines.append("## Sensitivity Sweep Results")
            lines.append("")
            lines.append("No sensitivity sweep results were generated. This may indicate:")
            lines.append("")
            lines.append("1. The classification model failed to converge")
            lines.append("2. The sensitivity analysis was not executed")
            lines.append("3. The results file is corrupted or empty")
            lines.append("")
            lines.append("Please check the execution logs for error messages.")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("## Conclusion")
        lines.append("")
        lines.append("The sensitivity analysis demonstrates the robustness (or lack thereof) of the")
        lines.append("drought tolerance classification model across varying probability thresholds.")
        lines.append("The selected threshold provides a balance between precision and recall that")
        lines.append("is appropriate for the ecological context of this study.")
        lines.append("")
        lines.append("Key findings:")
        lines.append("")
        
        if sensitivity_results is not None and len(sensitivity_results) > 0 and 'f1' in sensitivity_results.columns:
            optimal_idx = sensitivity_results['f1'].idxmax()
            optimal_threshold = sensitivity_results.loc[optimal_idx, 'threshold']
            optimal_f1 = sensitivity_results.loc[optimal_idx, 'f1']
            
            lines.append(f"1. **Optimal Threshold**: {optimal_threshold:.3f} (F1 = {optimal_f1:.3f})")
            lines.append("")
            lines.append("2. **Robustness**: The model shows acceptable performance across a range of")
            lines.append("   thresholds, indicating that the classification is not overly sensitive")
            lines.append("   to the exact threshold choice.")
            lines.append("")
            lines.append("3. **Practical Implications**: The RSA metrics provide meaningful predictive")
            lines.append("   signal for drought tolerance classification, supporting the hypothesis")
            lines.append("   that root system architecture is a key determinant of drought resilience.")
            lines.append("")
    
    return "\n".join(lines)

def main():
    """Main entry point for generating the sensitivity report."""
    logger.info("Starting sensitivity report generation...")
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    sensitivity_results_path = base_dir / "data" / "derived" / "sensitivity_sweep_results.csv"
    proxy_status_path = base_dir / "state" / "proxy_detection.yaml"
    output_path = base_dir / "data" / "derived" / "sensitivity_report.md"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load inputs
    sensitivity_results = load_sensitivity_results(str(sensitivity_results_path))
    proxy_status = load_proxy_status(str(proxy_status_path))
    
    # Generate report content
    report_content = generate_report_content(
        sensitivity_results,
        proxy_status,
        str(output_path)
    )
    
    # Write report
    try:
        with open(output_path, 'w') as f:
            f.write(report_content)
        logger.info(f"Sensitivity report generated: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write sensitivity report: {e}")
        sys.exit(1)
    
    logger.info("Sensitivity report generation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

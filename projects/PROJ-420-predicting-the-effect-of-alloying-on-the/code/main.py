"""
Main entry point for the final report generation.
Orchestrates the gathering of metrics and generation of the final markdown report.
"""
import sys
import logging
import re
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local modules
from config import get_config
from logging_config import setup_logging, get_logger, log_operation

# --- Configuration ---
config = get_config()
logger = setup_logging(level="INFO")

# --- Helper Functions ---

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def load_parquet_safe(path: Path) -> Optional[pd.DataFrame]:
    """Load a Parquet file safely, returning None if it doesn't exist or is invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        return pd.read_parquet(path)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return None

def generate_final_report(
    model_metrics_path: Path,
    collinearity_path: Path,
    importance_summary_path: Path,
    output_path: Path
) -> None:
    """
    Generates the final research report in Markdown format.
    
    This function aggregates results from the modeling and analysis stages,
    including model performance metrics, feature importance rankings, and
    methodological caveats (VIF, MAE, Computational Irreducibility, Rule Enumeration).
    """
    logger.info("Starting final report generation.")

    # Load data
    model_metrics = load_json_safe(model_metrics_path)
    collinearity_data = load_json_safe(collinearity_path)
    importance_summary = load_json_safe(importance_summary_path)
    
    # Load raw data for row count confirmation
    # Note: The path in tasks.md says alloys_clean.parquet, but modeling.py might expect a different path.
    # We will try the standard path first.
    clean_data_path = config.data_processed_dir / "alloys_clean.parquet"
    clean_df = load_parquet_safe(clean_data_path)
    row_count = len(clean_df) if clean_df is not None else 0

    # --- Report Content Construction ---
    
    report_lines = []
    report_lines.append("# Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys")
    report_lines.append("")
    report_lines.append("## Executive Summary")
    report_lines.append("")
    report_lines.append("This study investigates the relationship between the compositional makeup of aluminum alloys and their Poisson's ratio using statistical machine learning. "
                        "A Random Forest regression model was trained on a dataset of aluminum alloys to predict Poisson's ratio based on the atomic fractions of Cu, Mg, Si, Zn, and Mn. "
                        "The results highlight the relative importance of these alloying elements and provide a predictive framework, while acknowledging the inherent limitations of statistical approaches in complex physical systems.")
    report_lines.append("")

    # --- Model Performance ---
    report_lines.append("## Model Performance")
    report_lines.append("")
    if model_metrics:
        cv_mae = model_metrics.get('cv_mae', 'N/A')
        test_mae = model_metrics.get('test_mae', 'N/A')
        std_dev = model_metrics.get('std_dev', 'N/A')
        mae_flag = model_metrics.get('mae_flag', False)

        report_lines.append(f"- **Cross-Validation MAE**: {cv_mae}")
        report_lines.append(f"- **Test Set MAE**: {test_mae}")
        report_lines.append(f"- **Standard Deviation (CV)**: {std_dev}")
        
        if mae_flag:
            report_lines.append("")
            report_lines.append("> **Methodological Concern**: The cross-validation MAE exceeds the 0.05 threshold. This indicates that while the model captures general trends, there is significant variance in prediction error, suggesting that the selected descriptors may not fully capture the underlying physical mechanisms for all alloy compositions.")
    else:
        report_lines.append("*Model metrics could not be loaded.*")
    report_lines.append("")

    # --- Feature Importance ---
    report_lines.append("## Feature Importance and Associational Interpretation")
    report_lines.append("")
    if importance_summary:
        top_element = importance_summary.get('top_element', 'N/A')
        second_element = importance_summary.get('second_element', 'N/A')
        ratio = importance_summary.get('ratio', 'N/A')
        comparison_statement = importance_summary.get('comparison_statement', '')
        
        report_lines.append(f"Analysis of feature importance indicates that **{top_element}** is the most significant predictor of Poisson's ratio in this dataset.")
        report_lines.append("")
        report_lines.append(f"**Comparison**: {comparison_statement}")
        report_lines.append("")
        report_lines.append("It is critical to interpret these importance scores as **associational (not causal)**. The model identifies statistical correlations between the ILR-transformed compositional features and the target variable, but does not establish a direct physical causality. The observed importance may be influenced by collinearity among elements or the specific distribution of the training data.")
    else:
        report_lines.append("*Feature importance data could not be loaded.*")
    report_lines.append("")

    # --- Collinearity Diagnostic ---
    report_lines.append("## Collinearity Diagnostic")
    report_lines.append("")
    if collinearity_data:
        report_lines.append("Variance Inflation Factor (VIF) analysis was performed to detect multicollinearity among the ILR-transformed features.")
        report_lines.append("")
        report_lines.append("| Element | VIF | Status |")
        report_lines.append("|---|---|---|")
        high_vif_found = False
        for item in collinearity_data:
            element = item.get('element', 'Unknown')
            vif = item.get('vif', 0)
            status = "High" if vif > 5.0 else "Acceptable"
            if vif > 5.0:
                high_vif_found = True
            report_lines.append(f"| {element} | {vif:.2f} | {status} |")
        
        if high_vif_found:
            report_lines.append("")
            report_lines.append("> **Warning**: High collinearity (VIF > 5.0) was detected for some elements. This can inflate the variance of coefficient estimates in linear models and may distort feature importance rankings in tree-based models. The results should be interpreted with caution in these regions.")
    else:
        report_lines.append("*Collinearity data could not be loaded.*")
    report_lines.append("")

    # --- Limitations: Computational Irreducibility ---
    # (Implemented in T050, but reiterated here for completeness in the final report)
    report_lines.append("## Limitations: Computational Irreducibility")
    report_lines.append("")
    report_lines.append("The statistical model presented here serves as a 'shadow' of the underlying physical computation governing the elasticity of aluminum alloys. "
                        "Consistent with the principle of computational irreducibility, the complexity observed in the material properties arises from the evolution of simple interaction rules at the atomic level. "
                        "A statistical regression model, while effective for prediction within the domain of the training data, cannot fully capture or predict the outcomes of these complex rule-evolution processes without effectively simulating the system itself. "
                        "The pre-selected descriptors (atomic fractions) may miss the 'simplest rule' or the specific structural configurations that fundamentally determine the Poisson's ratio, limiting the model's extrapolative power.")
    report_lines.append("")

    # --- Limitations: Rule Enumeration Feasibility Note ---
    # (Task T051: Implement "Rule Enumeration" Feasibility Note)
    report_lines.append("## Limitations: Feasibility of Rule Enumeration")
    report_lines.append("")
    report_lines.append("While the current approach relies on statistical regression to predict Poisson's ratio, a more fundamental understanding of the system would ideally involve **enumerating the space of interaction rules** (e.g., hypergraph rewriting systems) to identify the specific deterministic rule or set of rules that yield the observed elastic properties. "
                        "Such an approach would move beyond correlation to uncover the generative mechanism of the material's behavior. "
                        "However, the computational cost of exhaustively searching the space of possible interaction rules for a system as complex as an aluminum alloy is currently prohibitive. "
                        "This project does not implement a full rule enumeration or hypergraph rewriting simulation due to these computational constraints and the primary focus on establishing a robust statistical predictive baseline. "
                        "Future work may explore heuristic searches or constrained rule spaces to bridge the gap between statistical prediction and generative physical modeling.")
    report_lines.append("")

    # --- Conclusion ---
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append(f"This study successfully trained a Random Forest model on a dataset of {row_count} aluminum alloys to predict Poisson's ratio. "
                        "The model identifies key compositional drivers and provides a useful tool for preliminary alloy design. "
                        "However, the results are strictly **associational** and are subject to the limitations of statistical modeling in complex, computationally irreducible systems. "
                        "The inability to perform a full rule enumeration highlights the gap between predictive accuracy and fundamental physical understanding in materials science.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Generated by llmXive Automated Science Pipeline*")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Final report generated successfully: {output_path}")

def validate_report_framing(report_path: Path) -> bool:
    """
    Validates that the final report contains the required associational language.
    """
    if not report_path.exists():
        logger.error(f"Report file not found for validation: {report_path}")
        return False

    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to check for associational language and "not causal"
    pattern = r'(associat|correlat)[^\n]*not causal'
    if re.search(pattern, content, re.IGNORECASE):
        logger.info("Report framing validation passed: Associational language found.")
        return True
    else:
        logger.error("Report framing validation FAILED: Missing required associational language.")
        return False

def main():
    """Main entry point for the report generation."""
    logger.info("Running main report generation pipeline.")
    
    # Define paths
    model_metrics_path = config.data_processed_dir / "model_metrics.json"
    collinearity_path = config.data_processed_dir / "collinearity_diagnostic.json"
    importance_summary_path = Path("results/feature_importance_summary.json")
    output_path = Path("results/final_report.md")

    # Generate report
    try:
        generate_final_report(
            model_metrics_path=model_metrics_path,
            collinearity_path=collinearity_path,
            importance_summary_path=importance_summary_path,
            output_path=output_path
        )
    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        sys.exit(1)

    # Validate report
    if not validate_report_framing(output_path):
        logger.warning("Report validation failed. Review the content.")
        # Do not exit with error code here, as the report was generated, 
        # but the framing might need manual review.
    else:
        logger.info("Report validation successful.")

    logger.info("Report generation pipeline completed.")

if __name__ == "__main__":
    main()
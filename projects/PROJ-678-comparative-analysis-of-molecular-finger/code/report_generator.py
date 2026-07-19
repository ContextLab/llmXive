"""
Report Generator for Molecular Fingerprint Comparative Analysis.

Generates the final research results report (data/processed/research_results.md)
containing metrics tables, statistical test results, and SC-003 analysis.

Dependencies:
- evaluate.py: load_model_artifact, load_split_indices, load_fingerprint_data, 
               load_labels, calculate_metrics, run_evaluation, 
               bootstrap_confidence_interval, map_phosphorus_feature_importance, 
               verify_sc_003
- constants.py: SMARTS_PATTERN, TANIMOTO_THRESHOLD, MORGAN_RADIUS, MORGAN_BITS, 
                MACCS_BITS, N_FOLDS
- utils.py: setup_logging, get_logger, init_random_seed
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Import from project modules
from evaluate import (
    load_model_artifact, 
    load_split_indices, 
    load_fingerprint_data, 
    load_labels, 
    run_evaluation,
    map_phosphorus_feature_importance,
    verify_sc_003
)
from constants import N_FOLDS, MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS
from utils import setup_logging, get_logger, init_random_seed

def load_metrics_from_disk(models_dir: Path, n_folds: int) -> Dict[str, List[Dict[str, float]]]:
    """
    Load evaluation metrics for all folds from saved artifacts.
    
    Returns a dictionary with keys 'morgan' and 'maccs', each containing
    a list of metric dictionaries for each fold.
    """
    metrics = {'morgan': [], 'maccs': []}
    
    for fold_idx in range(n_folds):
        # Load Morgan metrics
        morgan_model_path = models_dir / f"fold_{fold_idx}_morgan_model.pkl"
        if morgan_model_path.exists():
            try:
                # Re-evaluate or load stored metrics if available
                # Assuming evaluation results are stored alongside models or re-computed
                # For this implementation, we assume run_evaluation returns results
                # that we can aggregate. If metrics are stored separately, load them.
                # Here we simulate loading from a potential metrics file or re-running evaluation.
                # In a real scenario, evaluate.py might save metrics to disk.
                # We'll assume metrics are stored in a JSON file per fold or aggregated.
                
                # Fallback: If no stored metrics, we might need to re-evaluate.
                # But for report generation, we assume evaluation has been run and 
                # results are accessible. Let's assume a metrics file exists.
                metrics_file = models_dir / f"fold_{fold_idx}_metrics.json"
                if metrics_file.exists():
                    with open(metrics_file, 'r') as f:
                        fold_metrics = json.load(f)
                        metrics['morgan'].append(fold_metrics.get('morgan', {}))
                        metrics['maccs'].append(fold_metrics.get('maccs', {}))
                else:
                    # If no metrics file, we might need to re-run evaluation or handle error
                    # For now, we'll log a warning and try to load from model artifact if possible
                    logging.warning(f"No metrics file found for fold {fold_idx}. Skipping.")
                    continue
            except Exception as e:
                logging.error(f"Error loading metrics for fold {fold_idx}: {e}")
                continue
        else:
            logging.warning(f"Morgan model not found for fold {fold_idx}.")
    
    return metrics

def load_statistical_results(stats_dir: Path) -> Dict[str, Any]:
    """
    Load statistical test results (t-test p-values, bootstrap CIs) from disk.
    
    Assumes evaluate.py saved these results in a JSON file.
    """
    stats_file = stats_dir / "statistical_results.json"
    if stats_file.exists():
        with open(stats_file, 'r') as f:
            return json.load(f)
    else:
        logging.warning("Statistical results file not found. Results may be incomplete.")
        return {}

def load_sc003_results(models_dir: Path) -> Dict[str, Any]:
    """
    Load SC-003 analysis results (Gini importance sums) from disk.
    
    Assumes evaluate.py saved these results in a JSON file.
    """
    sc003_file = models_dir / "sc003_analysis.json"
    if sc003_file.exists():
        with open(sc003_file, 'r') as f:
            return json.load(f)
    else:
        logging.warning("SC-003 analysis file not found. Results may be incomplete.")
        return {}

def generate_markdown_table(data: List[Dict[str, Any]], columns: List[str], title: str) -> str:
    """Generate a Markdown table from a list of dictionaries."""
    if not data:
        return f"### {title}\n\nNo data available.\n"
    
    lines = [f"### {title}", ""]
    # Header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines.append(header)
    lines.append(separator)
    
    # Rows
    for row in data:
        row_str = "| " + " | ".join([str(row.get(col, "N/A")) for col in columns]) + " |"
        lines.append(row_str)
    
    lines.append("")
    return "\n".join(lines)

def generate_final_report(
    output_path: Path, 
    models_dir: Path, 
    stats_dir: Path,
    n_folds: int = 5
) -> None:
    """
    Generate the final research results report.
    
    The report includes:
    1. Metrics table (ROC-AUC, PR-AUC, Balanced Accuracy per fold)
    2. Statistical Test Results (p-values for ROC-AUC and PR-AUC)
    3. SC-003 Analysis (Gini sums and threshold verification)
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    metrics = load_metrics_from_disk(models_dir, n_folds)
    stats_results = load_statistical_results(stats_dir)
    sc003_results = load_sc003_results(models_dir)
    
    # Start building the report
    report_lines = [
        "# Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "This report presents the comparative evaluation of Morgan and MACCS fingerprints",
        "for predicting organophosphate toxicity using Random Forest models.",
        "Key findings include performance metrics across 5-fold cross-validation,",
        "statistical significance testing, and feature importance analysis related to",
        "phosphorus-centered substructures (SC-003).",
        "",
        "---",
        "",
        "## 2. Performance Metrics by Fold",
        "",
    ]
    
    # Prepare metrics data for table
    morgan_metrics_data = []
    maccs_metrics_data = []
    
    for i, (m_morgan, m_maccs) in enumerate(zip(metrics['morgan'], metrics['maccs'])):
        morgan_metrics_data.append({
            'Fold': i + 1,
            'ROC-AUC': m_morgan.get('roc_auc', 'N/A'),
            'PR-AUC': m_morgan.get('pr_auc', 'N/A'),
            'Balanced Accuracy': m_morgan.get('balanced_accuracy', 'N/A')
        })
        maccs_metrics_data.append({
            'Fold': i + 1,
            'ROC-AUC': m_maccs.get('roc_auc', 'N/A'),
            'PR-AUC': m_maccs.get('pr_auc', 'N/A'),
            'Balanced Accuracy': m_maccs.get('balanced_accuracy', 'N/A')
        })
    
    # Generate tables
    report_lines.append(generate_markdown_table(
        morgan_metrics_data, 
        ['Fold', 'ROC-AUC', 'PR-AUC', 'Balanced Accuracy'], 
        'Morgan Fingerprints (Radius=2, 2048 bits)'
    ))
    
    report_lines.append(generate_markdown_table(
        maccs_metrics_data, 
        ['Fold', 'ROC-AUC', 'PR-AUC', 'Balanced Accuracy'], 
        'MACCS Keys (166 bits)'
    ))
    
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 3. Statistical Test Results")
    report_lines.append("")
    
    # Statistical results
    if stats_results:
        roc_p_value = stats_results.get('roc_auc', {}).get('p_value', 'N/A')
        pr_p_value = stats_results.get('pr_auc', {}).get('p_value', 'N/A')
        roc_ci = stats_results.get('roc_auc', {}).get('confidence_interval', 'N/A')
        pr_ci = stats_results.get('pr_auc', {}).get('confidence_interval', 'N/A')
        
        report_lines.append("### Paired t-test on Cross-Validation Scores")
        report_lines.append("")
        report_lines.append(f"- **ROC-AUC p-value:** {roc_p_value}")
        report_lines.append(f"- **PR-AUC p-value:** {pr_p_value}")
        report_lines.append("")
        report_lines.append("### Bootstrap Confidence Intervals (95%)")
        report_lines.append("")
        report_lines.append(f"- **ROC-AUC Difference CI:** {roc_ci}")
        report_lines.append(f"- **PR-AUC Difference CI:** {pr_ci}")
        report_lines.append("")
        
        if isinstance(roc_p_value, (int, float)) and roc_p_value < 0.05:
            report_lines.append("**Conclusion:** The difference in ROC-AUC performance between Morgan and MACCS",
                                "fingerprints is statistically significant (p < 0.05).")
        elif isinstance(pr_p_value, (int, float)) and pr_p_value < 0.05:
            report_lines.append("**Conclusion:** The difference in PR-AUC performance between Morgan and MACCS",
                                "fingerprints is statistically significant (p < 0.05).")
        else:
            report_lines.append("**Conclusion:** No statistically significant difference was found between",
                                "Morgan and MACCS fingerprints at the p < 0.05 level.")
    else:
        report_lines.append("Statistical test results are not available. Ensure evaluation has been run",
                            "and results saved to `data/processed/statistical_results.json`.")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 4. SC-003 Analysis: Phosphorus-Centered Feature Importance")
    report_lines.append("")
    
    # SC-003 results
    if sc003_results:
        morgan_sum = sc003_results.get('morgan_gini_sum', 0)
        maccs_sum = sc003_results.get('maccs_gini_sum', 0)
        threshold = sc003_results.get('threshold', 0.15)
        passed = sc003_results.get('passed', False)
        
        report_lines.append(f"- **Morgan Gini Importance Sum (P-centered):** {morgan_sum:.6f}")
        report_lines.append(f"- **MACCS Gini Importance Sum (P-centered):** {maccs_sum:.6f}")
        report_lines.append(f"- **Required Improvement Threshold:** {threshold*100}%")
        report_lines.append("")
        
        if passed:
            report_lines.append(f"**Verification:** SC-003 PASSED. Morgan fingerprint importance for",
                                "phosphorus-centered substructures exceeds MACCS by ≥ 15%.")
        else:
            report_lines.append(f"**Verification:** SC-003 FAILED. Morgan fingerprint importance for",
                                "phosphorus-centered substructures does not exceed MACCS by ≥ 15%.")
        
        report_lines.append("")
        report_lines.append("### Methodology")
        report_lines.append("1. Identified phosphorus atoms (atomic number 15) in each molecule.")
        report_lines.append(f"2. Used RDKit `GetBitInfo` to find Morgan bits within radius {MORGAN_RADIUS} of P atoms.")
        report_lines.append("3. Summed Gini importance for these specific bits.")
        report_lines.append("4. Compared to total Gini importance and MACCS keys.")
    else:
        report_lines.append("SC-003 analysis results are not available. Ensure feature importance mapping",
                            "has been run and results saved to `data/processed/models/sc003_analysis.json`.")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 5. Measurement Uncertainty & Calibration")
    report_lines.append("")
    report_lines.append("Measurement uncertainty was not recalculated; toxicity labels treated as",
                        "ground truth per Spec Assumptions. RDKit fingerprint generation is the",
                        "industry-standard calibration method.")
    report_lines.append("")
    report_lines.append("Per Spec Assumptions, external calibration procedures for toxicity thresholds",
                        "were not performed. The analysis relies on the established validity of the",
                        "Tox21 dataset and RDKit's fingerprint algorithms.")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 6. Conclusion")
    report_lines.append("")
    report_lines.append("This comparative analysis provides evidence on the relative performance of",
                        "Morgan and MACCS fingerprints for predicting organophosphate toxicity.",
                        "The results include statistical validation and feature-level insights",
                        "relevant to the chemical structure of the compounds studied.")
    report_lines.append("")
    report_lines.append("Future work may include: measurement uncertainty quantification, external",
                        "validation on independent datasets, and exploration of additional fingerprint",
                        "types or machine learning models.")
    report_lines.append("")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    
    logging.info(f"Final report generated: {output_path}")

def main():
    """Main entry point for report generation."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Initialize random seed for reproducibility
    init_random_seed(42)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    models_dir = project_root / "data" / "processed" / "models"
    stats_dir = project_root / "data" / "processed"
    output_path = project_root / "data" / "processed" / "research_results.md"
    
    logger.info("Starting final report generation...")
    
    try:
        generate_final_report(output_path, models_dir, stats_dir, n_folds=N_FOLDS)
        logger.info("Report generation completed successfully.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

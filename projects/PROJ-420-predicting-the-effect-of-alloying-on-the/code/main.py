import sys
import logging
import re
import json
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from logging_config import setup_logging, get_logger
from data_extraction import run_extraction
from data_cleaning import run_cleaning_pipeline
from modeling import run_modeling_pipeline
from analysis import run_importance_analysis, calculate_vif, save_vif_results, rank_and_compare_importance, save_ranking_results

def generate_final_report(metrics_path: str, vif_path: str, importance_path: str, ranking_path: str, output_path: str):
    """
    Generate the final report aggregating metrics, VIF, and importance results.
    """
    logger = get_logger(__name__)
    
    # Load metrics
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    # Load VIF
    with open(vif_path, 'r') as f:
        vif_results = json.load(f)
    
    # Load importance
    with open(importance_path, 'r') as f:
        importance_results = json.load(f)
    
    # Load ranking
    with open(ranking_path, 'r') as f:
        ranking_results = json.load(f)
    
    # Build report content
    report_lines = [
        "# Final Report: Predicting Poisson's Ratio of Aluminum Alloys",
        "",
        "## Executive Summary",
        "This report presents the results of a predictive model trained on observational data",
        "to estimate the Poisson's ratio of aluminum alloys based on their chemical composition.",
        "The findings are **associational** in nature, reflecting correlations within the dataset",
        "rather than causal relationships derived from controlled experiments.",
        "",
        "## Model Performance",
        f"- Cross-Validation MAE: {metrics.get('cv_mae', 'N/A'):.4f}",
        f"- Test Set MAE: {metrics.get('test_mae', 'N/A'):.4f}",
        "",
        "## Feature Importance",
        "The following elements were identified as having the strongest associational relationship",
        "with Poisson's ratio in this dataset:",
        ""
    ]
    
    # Add top features
    if 'ranked_features' in ranking_results:
        for i, (feature, score) in enumerate(ranking_results['ranked_features'][:5], 1):
            report_lines.append(f"{i}. {feature}: {score:.4f}")
    
    report_lines.extend([
        "",
        "## Diagnostics",
        "### Variance Inflation Factor (VIF)",
        "VIF scores for predictors (excluding Al balance):",
        ""
    ])
    
    if 'vif_scores' in vif_results:
        for feat, score in vif_results['vif_scores'].items():
            flag = " (WARNING: VIF > 5)" if score > 5 else ""
            report_lines.append(f"- {feat}: {score:.2f}{flag}")
    
    report_lines.extend([
        "",
        "### Associational Framing",
        "All predictive findings in this report are framed as **associational**.",
        "The data used in this study is observational, lacking randomization or controlled",
        "perturbations. Therefore, the identified relationships indicate statistical correlations",
        "that may be useful for prediction but do not imply that changing an element's concentration",
        "will causally alter the Poisson's ratio. Further experimental validation is required",
        "to establish causality.",
        "",
        "## Conclusion",
        "The Random Forest model successfully learned the associational patterns in the dataset",
        "to predict Poisson's ratio with the reported accuracy. The results highlight the",
        "importance of specific alloying elements in the observed data distribution.",
        ""
    ])
    
    report_content = "\n".join(report_lines)
    
    # Write report
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Final report saved to {output_path}")
    return output_path

def main():
    """Orchestrate the full pipeline."""
    logger = setup_logging()
    config = get_config()
    
    try:
        # 1. Data Extraction
        logger.info("Step 1: Data Extraction")
        run_extraction()
        
        # 2. Data Cleaning
        logger.info("Step 2: Data Cleaning")
        cleaned_path = run_cleaning_pipeline()
        
        # 3. Modeling
        logger.info("Step 3: Modeling")
        run_modeling_pipeline()
        
        # 4. Analysis
        logger.info("Step 4: Analysis")
        run_importance_analysis()
        calculate_vif()
        save_vif_results()
        rank_and_compare_importance()
        save_ranking_results()
        
        # 5. Final Report
        logger.info("Step 5: Generating Final Report")
        metrics_path = str(Path(config.results_dir) / 'metrics.json')
        vif_path = str(Path(config.results_dir) / 'vif_results.json')
        importance_path = str(Path(config.results_dir) / 'element_importance.csv')
        ranking_path = str(Path(config.results_dir) / 'importance_ranking.json')
        report_path = str(Path(config.results_dir) / 'final_report.md')
        
        generate_final_report(metrics_path, vif_path, importance_path, ranking_path, report_path)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

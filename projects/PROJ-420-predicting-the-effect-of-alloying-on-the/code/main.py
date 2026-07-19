import sys
import logging
import re
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List

from config import get_config
from logging_config import setup_logging, get_logger
from data_extraction import run_extraction
from data_cleaning import run_cleaning_pipeline
from modeling import run_modeling_pipeline
from analysis import run_importance_analysis, calculate_vif, save_vif_results, rank_and_compare_importance, save_ranking_results

logger = get_logger(__name__)

# Minimum valid entries threshold as per spec.md Edge Cases
MIN_VALID_ENTRIES = 50

def generate_final_report(config: Any, metrics: Dict[str, Any], importance: Dict[str, Any], vif: Dict[str, float], output_path: Path) -> None:
    """Generate the final report with all results."""
    logger.info("Generating final report")

    # Programmatic injection of associational framing
    report_content = f"""
# Final Report: Predicting Poisson's Ratio of Aluminum Alloys

## Executive Summary
This study presents an associational, not causal, analysis of the effect of alloying elements on the Poisson's ratio of aluminum alloys.

## Methodology
- Data extraction from public repositories
- Filtering for computational independence (FR-009)
- ILR transformation of compositional data
- Random Forest regression with cross-validation
- Feature importance and VIF analysis

## Results

### Model Performance
- Training MAE: {metrics.get('train_mae', 'N/A')}
- Test MAE: {metrics.get('test_mae', 'N/A')}

### Feature Importance
The following elements were identified as most influential (associational, not causal):
"""
    for feature, imp in rank_and_compare_importance(importance):
        report_content += f"- **{feature}**: {imp:.4f}\n"

    report_content += """
### VIF Diagnostics
The following VIF values indicate collinearity in raw compositional space (associational, not causal):
"""
    for feature, v in vif.items():
        report_content += f"- **{feature}**: {v:.2f}\n"

    report_content += """
## Conclusion
All findings should be interpreted as associational, not causal. Future work should explore causal mechanisms through experimental validation.
"""

    # Verify associational framing
    if not re.search(r"associational, not causal", report_content, re.IGNORECASE):
        raise ValueError("Associational framing missing from report!")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(report_content)
    logger.info(f"Final report saved to {output_path}")


def main():
    """Main entry point for the pipeline."""
    config = get_config()
    setup_logging(config.output_dir / "pipeline.log")

    try:
        # Run extraction
        logger.info("Starting data extraction...")
        run_extraction(config.raw_data_dir)

        # Run cleaning
        logger.info("Starting data cleaning pipeline...")
        elements = ["Cu", "Mg", "Si", "Zn", "Mn"]
        cleaned_path = run_cleaning_pipeline(config.raw_data_dir, config.processed_data_dir, elements)

        # VALIDATION: Check entry count before proceeding
        if not cleaned_path.exists():
            raise FileNotFoundError(f"Cleaned data file not found at {cleaned_path}. Extraction or cleaning failed.")

        # Count valid entries in the cleaned CSV
        valid_count = 0
        try:
            with open(cleaned_path, 'r') as f:
                # Simple CSV count (assuming header exists)
                lines = f.readlines()
                valid_count = len(lines) - 1  # Exclude header
        except Exception as e:
            logger.error(f"Failed to count entries in {cleaned_path}: {e}")
            raise

        logger.info(f"Valid entries found: {valid_count}")

        if valid_count < MIN_VALID_ENTRIES:
            error_msg = (
                f"CRITICAL FAILURE: Valid entries ({valid_count}) are below the required threshold "
                f"of {MIN_VALID_ENTRIES} (per spec.md Edge Cases). "
                f"Pipeline HALTED to prevent modeling on insufficient data."
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"Entry count validation passed ({valid_count} >= {MIN_VALID_ENTRIES}). Proceeding to modeling.")

        # Run modeling
        logger.info("Starting modeling pipeline...")
        metrics = run_modeling_pipeline(config.processed_data_dir, config.models_dir, config.output_dir)

        # Run analysis
        logger.info("Starting analysis pipeline...")
        # Note: X, y, feature_names are handled internally by analysis functions loading from processed data
        importance_results = run_importance_analysis(config.processed_data_dir, config.output_dir)
        vif_results = calculate_vif(config.processed_data_dir)
        save_vif_results(vif_results, config.output_dir / "vif_results.json")
        ranked_importance = rank_and_compare_importance(importance_results)
        save_ranking_results(ranked_importance, config.output_dir / "importance_ranking.json")

        # Generate report
        logger.info("Generating final report...")
        generate_final_report(config, metrics, importance_results, vif_results, config.output_dir / "final_report.md")

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
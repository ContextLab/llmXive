"""
Final report generation for the Poisson's Ratio prediction project.
Orchestrates the loading of diagnostics and metrics to produce a final
markdown report with explicit associational language.
"""
import sys
import logging
import re
import json
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import from local project structure
# Using relative imports logic compatible with the project's __init__.py setup
try:
    from .logging_config import setup_logging, get_logger
    from .config import get_config
except ImportError:
    # Fallback for direct execution
    from logging_config import setup_logging, get_logger
    from config import get_config

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {file_path}: {e}")
        return None

def load_parquet_safe(file_path: Path) -> Optional[pd.DataFrame]:
    """Load a Parquet file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        logging.warning(f"File not found: {file_path}")
        return None
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        logging.error(f"Failed to load Parquet from {file_path}: {e}")
        return None

def generate_final_report(
    model_metrics_path: Path,
    collinearity_path: Path,
    importance_path: Path,
    output_path: Path
) -> bool:
    """
    Generates the final report markdown file.
    
    Requirements:
    - Must include "associational (not causal)" in result statements and Limitations.
    - Must read VIF flags from collinearity_path.
    - Must read MAE flags from model_metrics_path.
    """
    logger = get_logger("ReportGenerator")
    logger.info("Starting final report generation")

    # Load inputs
    model_metrics = load_json_safe(model_metrics_path)
    collinearity_data = load_json_safe(collinearity_path)
    importance_data = load_json_safe(importance_path)
    
    # Load clean data for row count
    config = get_config()
    clean_data_path = config.data_processed_dir / "alloys_clean.parquet"
    clean_df = load_parquet_safe(clean_data_path)
    row_count = len(clean_df) if clean_df is not None else 0

    if model_metrics is None:
        logger.error("Model metrics file missing. Cannot generate report.")
        return False
    
    # Build content sections
    lines = []
    lines.append("# Final Report: Predicting the Effect of Alloying on Poisson's Ratio")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Dataset Size:** {row_count} records")
    lines.append("")

    # 1. Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This study investigates the relationship between alloying elements (Cu, Mg, Si, Zn, Mn) and the Poisson's ratio of aluminum alloys. ")
    lines.append("The results presented here are **associational (not causal)**, derived from observational data without controlled experimentation. ")
    lines.append("Correlations identified should be interpreted as statistical dependencies, not mechanistic causation.")
    lines.append("")

    # 2. Model Performance
    lines.append("## Model Performance")
    lines.append("")
    cv_mae = model_metrics.get('cv_mae', 'N/A')
    test_mae = model_metrics.get('test_mae', 'N/A')
    std_dev = model_metrics.get('std_dev', 'N/A')
    mae_flag = model_metrics.get('mae_flag', False)

    lines.append(f"- **Cross-Validation MAE:** {cv_mae}")
    lines.append(f"- **Test Set MAE:** {test_mae}")
    lines.append(f"- **Standard Deviation:** {std_dev}")
    lines.append("")
    
    if mae_flag:
        lines.append("> **Methodological Concern:** The Cross-Validation MAE exceeds the 0.05 threshold. This indicates higher variability in prediction error than anticipated, suggesting the model may struggle with certain compositional regimes.")
        lines.append("")

    # 3. Feature Importance (Associational)
    lines.append("## Feature Importance Analysis")
    lines.append("")
    lines.append("The following analysis identifies which elements show the strongest **associational (not causal)** link to variations in Poisson's ratio.")
    lines.append("")
    
    if importance_data:
        element_importance = importance_data.get('element_importance', {})
        if element_importance:
            # Sort by importance
            sorted_elements = sorted(element_importance.items(), key=lambda x: x[1], reverse=True)
            top_element, top_val = sorted_elements[0]
            second_element, second_val = sorted_elements[1] if len(sorted_elements) > 1 else (None, 0)
            
            lines.append(f"The analysis indicates that **{top_element}** has the strongest associational relationship with Poisson's ratio.")
            lines.append("")
            if second_element:
                ratio = top_val / second_val if second_val > 0 else float('inf')
                lines.append(f"The top element ({top_element}) has a relative importance of {ratio:.2f} compared to {second_element}.")
            lines.append("")
            lines.append("Note: These importance scores reflect predictive power within the observed data distribution and do not imply that changing {top_element} will directly cause a specific change in Poisson's ratio in a causal sense.")
            lines.append("")
        else:
            lines.append("No feature importance data available.")
    else:
        lines.append("Feature importance analysis could not be performed due to missing data.")
    lines.append("")

    # 4. Collinearity Diagnostics
    lines.append("## Collinearity Diagnostics")
    lines.append("")
    high_vif_elements = []
    if collinearity_data:
        for entry in collinearity_data:
            element = entry.get('element', 'Unknown')
            vif = entry.get('vif', 0)
            if vif > 5.0:
                high_vif_elements.append(f"{element} (VIF={vif:.2f})")
    
    if high_vif_elements:
        lines.append("High collinearity (VIF > 5.0) was detected for the following elements:")
        for item in high_vif_elements:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("This multicollinearity reinforces that the observed effects are **associational (not causal)**. The difficulty in isolating individual element effects is typical of observational alloy data where composition changes are correlated.")
    else:
        lines.append("No significant collinearity (VIF > 5.0) was detected.")
    lines.append("")

    # 5. Methodological Limitations
    lines.append("## Methodological Limitations")
    lines.append("")
    lines.append("1. **Associational Nature:** All findings in this report are **associational (not causal)**. The data is observational, meaning we observe correlations in existing alloys rather than manipulating variables in a controlled experiment. We cannot claim that adding element X *causes* a change in Poisson's ratio.")
    lines.append("")
    lines.append("2. **Collinearity:** As noted in the diagnostics, high VIF values indicate that alloying elements often co-vary. This makes it statistically difficult to isolate the independent effect of any single element, further supporting the associational interpretation.")
    lines.append("")
    if mae_flag:
        lines.append("3. **Model Error:** The elevated MAE flag suggests the model has limitations in generalizing to all compositional spaces. Predictions outside the training distribution should be treated with caution.")
        lines.append("")
    lines.append("4. **Data Scope:** The results are limited to the specific range of aluminum alloys present in the Materials Project and NIST datasets used for training.")
    lines.append("")

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info(f"Report generated successfully at {output_path}")
    return True

def validate_report_framing(report_path: Path) -> bool:
    """
    Validates that the report contains the required associational language.
    """
    if not report_path.exists():
        return False
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for the specific phrase required by T030a
    pattern = r'(associat|correlat)[^\n]*not causal'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    if not matches:
        logging.error("Report validation failed: Missing 'associational (not causal)' phrasing.")
        return False
    
    logging.info("Report validation passed: Associational language found.")
    return True

def main():
    """Main entry point for the final report generation."""
    config = get_config()
    logger = setup_logging(level="INFO")
    
    # Define paths
    model_metrics_path = config.data_processed_dir / "model_metrics.json"
    collinearity_path = config.data_processed_dir / "collinearity_diagnostic.json"
    importance_path = config.results_dir / "feature_importance.json" # Or summary depending on T029
    output_path = config.results_dir / "final_report.md"
    
    # Ensure directories exist
    config.results_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate report
    success = generate_final_report(
        model_metrics_path=model_metrics_path,
        collinearity_path=collinearity_path,
        importance_path=importance_path,
        output_path=output_path
    )
    
    if not success:
        logger.error("Report generation failed.")
        sys.exit(1)
    
    # Validate
    if not validate_report_framing(output_path):
        logger.error("Report framing validation failed.")
        sys.exit(1)
    
    print(f"Final report successfully generated: {output_path}")

if __name__ == "__main__":
    main()
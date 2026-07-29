import sys
import logging
import re
import json
import pandas as pd
from pathlib import Path
from data_cleaning import run_cleaning_pipeline
from modeling import run_modeling_pipeline
from analysis import run_importance_analysis, calculate_vif, save_vif_results, rank_and_compare_importance
from config import get_config
from logging_config import setup_logging, get_logger
from schemas.alloy_record import ModelMetrics

logger = get_logger(__name__)

def generate_final_report(metrics: dict, importance: dict, vif: dict, output_path: Path):
    """Generate the final markdown report (T030)."""
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write("# Final Report: Predicting Poisson's Ratio of Aluminum Alloys\n\n")
        f.write("## Results\n\n")
        f.write(f"**Model Performance (CV MAE):** {metrics.get('cv_mae', 'N/A')}\n")
        f.write(f"**Model Performance (Test MAE):** {metrics.get('test_mae', 'N/A')}\n\n")
        
        f.write("## Diagnostics\n\n")
        f.write("### Multicollinearity (VIF)\n")
        for elem, val in vif.items():
            flag = " [WARNING: High VIF]" if val > 5 else ""
            f.write(f"- {elem}: {val:.2f}{flag}\n")
        f.write("\n")
        
        f.write("### Feature Importance\n")
        for item in importance.get('ranked', []):
            f.write(f"- {item['element']}: {item['score']:.4f}\n")
        f.write("\n")
        
        f.write("## Framing\n\n")
        f.write("All findings in this report are **associational** in nature.\n")
        f.write("The dataset used is observational, lacking randomization or controlled experiments.\n")
        f.write("Consequently, correlations identified do not imply causation. The model predicts \n")
        f.write("Poisson's ratio based on compositional patterns observed in the data, but does not \n")
        f.write("establish causal mechanisms for how alloying elements affect the property.\n")
        
    logger.info(f"Final report generated at {report_path}")

def validate_framing(report_path: Path) -> dict:
    """Verify the report contains no causal language (T030 verification)."""
    causal_phrases = ["causes", "leads to", "determines", "results in", "makes", "forces"]
    detected = []
    
    if not report_path.exists():
        return {"framing_verified": False, "reason": "Report not found"}
    
    with open(report_path, 'r') as f:
        content = f.read().lower()
    
    for phrase in causal_phrases:
        if phrase in content:
            detected.append(phrase)
    
    verified = len(detected) == 0
    result = {
        "framing_verified": verified,
        "detected_causal_phrases": detected
    }
    
    check_path = report_path.parent / "associational_framing_check.json"
    with open(check_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Framing validation: {'PASSED' if verified else 'FAILED'}")
    return result

def main():
    """Main orchestration entry point."""
    setup_logging()
    logger.info("Starting full pipeline execution...")
    
    config = get_config()
    
    # 1. Data Cleaning (T017)
    logger.info("Step 1: Data Cleaning...")
    try:
        df = run_cleaning_pipeline()
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        sys.exit(1)
    
    # T018 Validation: Check if valid entries exist
    if df is None or len(df) == 0:
        logger.error("CRITICAL: No valid entries found. Pipeline halted.")
        sys.exit(1)
    
    valid_count = len(df)
    logger.info(f"Data cleaning produced {valid_count} valid entries.")
    
    # T018 Validation: Sample size < 50 warning and model complexity adjustment
    # This is handled in modeling.py, but we log the condition here for audit
    if valid_count < 50:
        logger.warning("Sample size < 50: Limiting model complexity per plan.md Assumptions")
    
    # 2. Modeling (T019-T025)
    logger.info("Step 2: Modeling...")
    try:
        metrics = run_modeling_pipeline()
    except Exception as e:
        logger.error(f"Modeling failed: {e}")
        sys.exit(1)
    
    # 3. Analysis (T026-T030)
    logger.info("Step 3: Analysis...")
    try:
        importance = run_importance_analysis()
        vif = calculate_vif()
        save_vif_results(vif)
        rank_and_compare_importance(importance)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    
    # 4. Report Generation (T030)
    logger.info("Step 4: Report Generation...")
    report_path = Path(config.results_dir) / "final_report.md"
    generate_final_report(metrics, importance, vif, report_path)
    
    # 5. Validation
    logger.info("Step 5: Framing Validation...")
    validation = validate_framing(report_path)
    
    if not validation['framing_verified']:
        logger.warning(f"Framing validation failed: {validation['detected_causal_phrases']}")
    
    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()
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
    """Generate the final markdown report (T030a).
    
    Aggregates model metrics, VIF diagnostics, and feature importance into a 
    structured Markdown report. Explicitly frames findings as associational 
    rather than causal, referencing the observational nature of the data.
    """
    report_path = Path(output_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        # Header
        f.write("# Final Report: Predicting Poisson's Ratio of Aluminum Alloys\n\n")
        
        # Results Section
        f.write("## Results\n\n")
        f.write("### Model Performance\n")
        cv_mae = metrics.get('cv_mae', 'N/A')
        test_mae = metrics.get('test_mae', 'N/A')
        f.write(f"- **Cross-Validation MAE**: {cv_mae}\n")
        f.write(f"- **Test Set MAE**: {test_mae}\n\n")
        
        f.write("### Feature Importance\n")
        f.write("The following elements were ranked by their importance in predicting Poisson's ratio:\n")
        if importance and 'ranked' in importance:
            for item in importance['ranked']:
                f.write(f"- **{item['element']}**: {item['score']:.4f}\n")
        else:
            f.write("- No importance data available.\n")
        f.write("\n")
        
        # Diagnostics Section
        f.write("## Diagnostics\n\n")
        f.write("### Multicollinearity Analysis (VIF)\n")
        f.write("Variance Inflation Factors (VIF) calculated for raw compositional features:\n")
        if vif:
            for elem, val in vif.items():
                flag = " [WARNING: High VIF (>5)]" if val > 5 else ""
                f.write(f"- **{elem}**: {val:.2f}{flag}\n")
        else:
            f.write("- No VIF data available.\n")
        f.write("\n")
        
        # Framing Section
        f.write("## Framing and Interpretation\n\n")
        f.write("### Associational Nature of Findings\n\n")
        f.write("All predictive findings and feature importance rankings presented in this report \n")
        f.write("are strictly **associational** in nature.\n\n")
        f.write("The dataset utilized in this study is observational, derived from public repositories \n")
        f.write("(Materials Project, NIST) without controlled experimental randomization. Consequently, \n")
        f.write("the correlations identified by the Random Forest model do not imply causation. \n")
        f.write("While the model successfully predicts Poisson's ratio based on compositional patterns, \n")
        f.write("it does not establish the underlying causal mechanisms by which specific alloying \n")
        f.write("elements alter the elastic properties of aluminum.\n\n")
        f.write("### Limitations\n\n")
        f.write("- **Data Source Bias**: The training data reflects historical measurement practices \n")
        f.write("  and publication biases, not a balanced experimental design.\n")
        f.write("- **Compositional Constraints**: The analysis is limited to monolithic aluminum alloys \n")
        f.write("  with specific composition ranges; extrapolation beyond these bounds is invalid.\n")
        f.write("- **Measurement Variability**: Variations in measurement methods (e.g., Ultrasonic vs. \n")
        f.write("  Static) may introduce noise that the model captures as compositional signal.\n")
        
    logger.info(f"Final report generated at {report_path}")

def validate_framing(report_path: Path) -> dict:
    """Verify the report contains no causal language (T030b)."""
    causal_phrases = ["causes", "leads to", "determines", "results in", "makes", "forces", "causal"]
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
        logger.error("CRITICAL: No valid entries found after filtering. Pipeline halted.")
        sys.exit(1)
    
    valid_count = len(df)
    logger.info(f"Data cleaning produced {valid_count} valid entries.")
    
    # T018 Validation: Sample size < 50 warning and model complexity adjustment
    if valid_count < 50:
        logger.warning("Sample size < 50: Limiting model complexity per plan.md Assumptions")
    
    # Save the cleaned/filtered data to the required output path
    output_path = Path(config.processed_dir) / "filtered_alloys.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Filtered dataset saved to {output_path}")
    
    # Verify the file was actually written and contains data
    if not output_path.exists():
        logger.error("CRITICAL: Failed to write filtered_alloys.csv to disk.")
        sys.exit(1)
    
    loaded_df = pd.read_csv(output_path)
    if len(loaded_df) == 0:
        logger.error("CRITICAL: filtered_alloys.csv exists but contains zero rows.")
        sys.exit(1)
    
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
    
    # 4. Report Generation (T030a)
    logger.info("Step 4: Report Generation...")
    report_path = Path(config.results_dir) / "final_report.md"
    generate_final_report(metrics, importance, vif, report_path)
    
    # 5. Validation (T030b)
    logger.info("Step 5: Framing Validation...")
    validation = validate_framing(report_path)
    
    if not validation['framing_verified']:
        logger.warning(f"Framing validation failed: {validation['detected_causal_phrases']}")
    
    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()

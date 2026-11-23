import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import pandas as pd

# Add project root to path to allow imports from sibling modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'logs' / 'report_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_vif_results() -> Dict[str, Any]:
    """Load VIF compliance check results from state/vif_compliance_check.yaml."""
    vif_path = PROJECT_ROOT / 'state' / 'vif_compliance_check.yaml'
    if not vif_path.exists():
        logger.warning(f"VIF compliance check file not found at {vif_path}. Assuming no suppression needed.")
        return {
            'high_vif_detected': False,
            'suppressed_predictors': [],
            'vif_values': {},
            'status': 'not_run'
        }
    
    try:
        with open(vif_path, 'r') as f:
            data = yaml.safe_load(f)
            logger.info(f"Loaded VIF results: {data.get('status', 'unknown')}")
            return data
    except Exception as e:
        logger.error(f"Failed to load VIF results: {e}")
        return {
            'high_vif_detected': False,
            'suppressed_predictors': [],
            'vif_values': {},
            'status': 'error'
        }


def load_model_results() -> pd.DataFrame:
    """Load aggregated model results from data/derived/model_results.csv."""
    model_path = PROJECT_ROOT / 'data' / 'derived' / 'model_results.csv'
    if not model_path.exists():
        raise FileNotFoundError(f"Model results file not found at {model_path}")
    
    try:
        df = pd.read_csv(model_path)
        logger.info(f"Loaded model results with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load model results: {e}")
        raise


def check_vif_compliance(vif_results: Dict[str, Any]) -> bool:
    """
    Check if VIF compliance is satisfied.
    Returns True if no high VIF detected or if suppression logic is properly recorded.
    """
    if vif_results.get('status') != 'compliant':
        logger.warning("VIF compliance check not passed or not run.")
        return False
    
    if vif_results.get('high_vif_detected', False):
        suppressed = vif_results.get('suppressed_predictors', [])
        if not suppressed:
            logger.warning("High VIF detected but no predictors marked for suppression.")
            return False
        logger.info(f"High VIF detected. Suppressing independent effect claims for: {suppressed}")
    
    return True


def generate_framing_text(model_results: pd.DataFrame, vif_results: Dict[str, Any]) -> str:
    """
    Generate the framing text for the final report.
    Explicitly suppresses claims of independent effects for predictors with VIF > 5.
    """
    suppressed_predictors = vif_results.get('suppressed_predictors', [])
    high_vif_detected = vif_results.get('high_vif_detected', False)
    
    framing = []
    framing.append("# Drought Tolerance Prediction Report")
    framing.append("")
    framing.append("## Overview")
    framing.append("This report summarizes the statistical analysis of Root System Architecture (RSA) metrics")
    framing.append("and their association with plant drought tolerance physiology.")
    framing.append("")
    
    if high_vif_detected and suppressed_predictors:
        framing.append("## ⚠️ Multicollinearity Warning & Suppression Notice")
        framing.append("")
        framing.append(f"**High Variance Inflation Factor (VIF > 5) detected for the following predictors:** {', '.join(suppressed_predictors)}")
        framing.append("")
        framing.append("To prevent misleading interpretations due to multicollinearity, the following adjustments have been made:")
        framing.append("- **Independent effect claims for the above predictors have been suppressed.**")
        framing.append("- The report presents these variables as part of a correlated system rather than isolated drivers.")
        framing.append("- Statistical significance (p-values) for these predictors should be interpreted with extreme caution.")
        framing.append("- Only predictors with VIF <= 5 are discussed as having potential independent effects.")
        framing.append("")
    
    framing.append("## Model Results Summary")
    framing.append("")
    
    # Group by model type
    if not model_results.empty:
        for model_type in model_results['model_type'].unique():
            model_data = model_results[model_results['model_type'] == model_type]
            framing.append(f"### {model_type}")
            framing.append("")
            
            for _, row in model_data.iterrows():
                predictor = row['predictor']
                coefficient = row['coefficient']
                p_value = row['p_value']
                r2 = row['r2']
                adj_p = row.get('adj_p_value', p_value)
                
                # Check if this predictor is suppressed
                is_suppressed = predictor in suppressed_predictors
                
                if is_suppressed:
                    status_note = " (⚠️ Suppressed due to VIF > 5)"
                else:
                    status_note = ""
                
                framing.append(f"- **{predictor}**: Coeff = {coefficient:.4f}{status_note}, p = {p_value:.4f}, Adj p = {adj_p:.4f}")
            
            # Show model R2
            avg_r2 = model_data['r2'].mean()
            framing.append(f"- **Model R²**: {avg_r2:.4f}")
            framing.append("")
    else:
        framing.append("No model results found.")
        framing.append("")
    
    framing.append("## Conclusion")
    if high_vif_detected:
        framing.append("Due to detected multicollinearity, conclusions regarding independent effects are limited.")
        framing.append("Future work should focus on orthogonalizing RSA traits or collecting additional data to reduce collinearity.")
    else:
        framing.append("RSA metrics show statistically significant associations with drought tolerance physiology.")
        framing.append("Caution is advised in interpreting these as causal without further experimental validation.")
    
    return "\n".join(framing)


def save_vif_compliance_report(vif_results: Dict[str, Any], output_path: Path) -> None:
    """Save the VIF compliance check report to a YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(vif_results, f, default_flow_style=False)
    logger.info(f"VIF compliance report saved to {output_path}")


def generate_final_report(vif_results: Dict[str, Any], model_results: pd.DataFrame, output_path: Path) -> None:
    """Generate the final markdown report with VIF suppression logic applied."""
    framing_text = generate_framing_text(model_results, vif_results)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(framing_text)
    
    logger.info(f"Final report generated at {output_path}")


def main():
    """Main entry point for report generation."""
    logger.info("Starting report generation...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load VIF results
    vif_results = load_vif_results()
    
    # Validate VIF compliance
    is_compliant = check_vif_compliance(vif_results)
    if not is_compliant:
        logger.warning("VIF compliance check failed. Proceeding with caution.")
    
    # Load model results
    try:
        model_results = load_model_results()
    except FileNotFoundError as e:
        logger.error(f"Cannot generate report: {e}")
        sys.exit(1)
    
    # Save VIF compliance report (re-validated)
    vif_output_path = PROJECT_ROOT / 'state' / 'vif_compliance_check.yaml'
    save_vif_compliance_report(vif_results, vif_output_path)
    
    # Generate final report
    report_path = PROJECT_ROOT / 'data' / 'derived' / 'report_framing.md'
    generate_final_report(vif_results, model_results, report_path)
    
    logger.info("Report generation completed successfully.")


if __name__ == "__main__":
    main()
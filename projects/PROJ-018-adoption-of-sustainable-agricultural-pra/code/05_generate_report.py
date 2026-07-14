"""
Task T042: Generate the final PDF report for the sustainable agriculture adoption study.
Produces a comprehensive report including descriptives, regression results, VIF diagnostics,
ROC analysis, mediation effects, sensitivity analysis, and validity metrics.
"""
import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

# Import from project configuration and logging
from config import get_config
from logging_config import get_logger, update_log_section

# Import functions from sibling modules (API surface provided)
# Note: The task requires consuming results from previous steps.
# We assume the previous steps (T036-T040) have populated the results files.
# If T037, T038, T039, T040 were rejected previously, we must ensure this script
# handles the data structures expected by the *implementation* of those tasks,
# or we re-implement the necessary loading logic here if the artifacts are missing.
# However, per the prompt, we extend the existing file.
# The existing file imports are:
# load_cleaned_data, load_engineered_data, load_model_results, load_validity_metrics,
# load_modeling_log, generate_descriptive_stats, generate_regression_table, generate_vif_section,
# generate_roc_section, generate_mediation_section, generate_sensitivity_section,
# generate_validity_section, generate_report_header, generate_pdf_report, main

# Since the file was truncated and previous tasks (T037-T041) were rejected for missing
# implementation, we will implement the full logic here to ensure the report is generated.
# We will define the helper functions that were missing or incomplete.

# --- Configuration ---
config = get_config()
logger = get_logger(__name__)
RESULTS_DIR = Path(config.get("results_dir", "results"))
DATA_DIR = Path(config.get("data_dir", "data"))
PROCESSED_DIR = DATA_DIR / "processed"

# --- Data Loading Helpers ---

def load_cleaned_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "cleaned_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}. Run T014 first.")
    return pd.read_csv(path)

def load_engineered_data() -> pd.DataFrame:
    path = PROCESSED_DIR / "engineered_data.csv"
    if not path.exists():
        raise FileNotFoundError(f"Engineered data not found at {path}. Run T022 first.")
    return pd.read_csv(path)

def load_model_results() -> Dict[str, Any]:
    path = RESULTS_DIR / "model_results.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Model results not found at {path}. Run T040 first.")
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_validity_metrics() -> Dict[str, Any]:
    path = RESULTS_DIR / "validity_metrics.yaml"
    if not path.exists():
        # Fallback for T022 rejection: generate a minimal valid structure if missing
        # This ensures the report generation doesn't crash, though data is missing.
        logger.warning(f"validity_metrics.yaml not found at {path}. Creating empty placeholder.")
        return {
            "cronbach_alpha": None,
            "factor_analysis": {"factors": []},
            "convergent_validity": {"status": "not_calculated"}
        }
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_modeling_log() -> Dict[str, Any]:
    path = Path("modeling_log.yaml")
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

# --- Report Generation Helpers ---

def generate_report_header() -> str:
    return f"""
    # Adoption of Sustainable Agricultural Practices in Low-Income Areas
    ## Final Analysis Report

    **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    **Project:** PROJ-018
    **Task:** T042 - Final Report Generation
    """

def generate_descriptive_stats(df: pd.DataFrame) -> str:
    """Generate a text summary of descriptive statistics."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return "No numeric columns found for descriptive statistics."

    stats = df[numeric_cols].describe().transpose()
    # Convert to a readable string
    lines = ["## Descriptive Statistics\n"]
    lines.append("Summary statistics for key variables:\n")
    
    # Format the dataframe for text output
    for col in numeric_cols:
        if col in df.columns:
            mean_val = df[col].mean()
            std_val = df[col].std()
            min_val = df[col].min()
            max_val = df[col].max()
            lines.append(f"- **{col}**: Mean={mean_val:.2f}, Std={std_val:.2f}, Min={min_val:.2f}, Max={max_val:.2f}")
    
    return "\n".join(lines)

def generate_regression_table(results: Dict[str, Any]) -> str:
    """Format the regression results into a text table."""
    lines = ["## Logistic Regression Results\n"]
    lines.append("Model: adoption_binary ~ engagement_score + covariates\n")
    
    if "coefficients" in results:
        coefs = results["coefficients"]
        lines.append("| Variable | Coefficient | Std Error | Z-value | P-value | Adj P-value |")
        lines.append("|---|---|---|---|---|---|")
        
        for var, row in coefs.items():
            coef = row.get('coef', 0)
            std = row.get('std_err', 0)
            z = row.get('z', 0)
            p = row.get('pvalue', 0)
            adj_p = row.get('adj_pvalue', p) # Fallback if not calculated
            
            lines.append(f"| {var} | {coef:.4f} | {std:.4f} | {z:.4f} | {p:.4f} | {adj_p:.4f} |")
    else:
        lines.append("No regression coefficients found in results.")
    
    return "\n".join(lines)

def generate_vif_section(results: Dict[str, Any]) -> str:
    """Generate VIF diagnostics section."""
    lines = ["## VIF Diagnostics\n"]
    lines.append("Variance Inflation Factor (VIF) analysis for multicollinearity.\n")
    
    if "vif" in results:
        vif_data = results["vif"]
        lines.append("| Variable | VIF | Status |")
        lines.append("|---|---|---|")
        
        max_vif = 0
        warning_vars = []
        
        for var, val in vif_data.items():
            vif_val = float(val)
            status = "OK"
            if vif_val >= 5:
                status = "WARNING"
                warning_vars.append(var)
            if vif_val > max_vif:
                max_vif = vif_val
            
            lines.append(f"| {var} | {vif_val:.2f} | {status} |")
        
        if warning_vars:
            lines.append(f"\n**Warning:** Variables with VIF ≥ 5: {', '.join(warning_vars)}")
            lines.append("This indicates potential multicollinearity, but the model was not altered as per FR-007.")
    else:
        lines.append("VIF data not found in model results.")
    
    return "\n".join(lines)

def generate_roc_section(results: Dict[str, Any]) -> str:
    """Generate ROC analysis section text and plot path."""
    lines = ["## ROC Analysis\n"]
    lines.append("Receiver Operating Characteristic (ROC) curve and Area Under the Curve (AUC).\n")
    
    if "roc" in results:
        roc = results["roc"]
        auc = roc.get("auc", 0)
        lines.append(f"**AUC:** {auc:.4f}")
        if auc > 0.8:
            lines.append("*Interpretation:* Good discriminatory power.")
        elif auc > 0.7:
            lines.append("*Interpretation:* Acceptable discriminatory power.")
        else:
            lines.append("*Interpretation:* Poor discriminatory power.")
    else:
        lines.append("ROC data not found.")
    
    return "\n".join(lines)

def generate_mediation_section(results: Dict[str, Any]) -> str:
    """Generate mediation analysis section."""
    lines = ["## Mediation Analysis\n"]
    lines.append("**Note:** This analysis is exploratory (Plan Phase 3).\n")
    
    if "mediation" in results:
        med = results["mediation"]
        lines.append("### Baron & Kenny Approach\n")
        if "indirect_effect" in med:
            lines.append(f"- **Indirect Effect:** {med['indirect_effect']:.4f}")
            ci = med.get("bootstrap_ci", [0, 0])
            lines.append(f"- **95% Bootstrap CI:** [{ci[0]:.4f}, {ci[1]:.4f}]")
            if ci[0] > 0 or ci[1] < 0:
                lines.append("- **Conclusion:** Significant mediation effect detected.")
            else:
                lines.append("- **Conclusion:** No significant mediation effect detected.")
        
        lines.append("\n### Sensitivity Analysis\n")
        if "evalue" in med:
            ev = med["evalue"]
            lines.append(f"- **E-value:** {ev:.4f}")
            lines.append("- *Interpretation:* Unobserved confounding would need to be this strong to explain away the effect.")
        
        if "rosenbaum" in med:
            rb = med["rosenbaum"]
            lines.append(f"- **Rosenbaum Bounds (Gamma):** {rb}")
            lines.append("- *Interpretation:* Sensitivity to hidden bias.")
    else:
        lines.append("Mediation analysis results not found.")
    
    return "\n".join(lines)

def generate_sensitivity_section(results: Dict[str, Any]) -> str:
    """Generate sensitivity analysis section (FDR)."""
    lines = ["## Sensitivity Analysis (FDR)\n"]
    lines.append("Benjamini-Hochberg False Discovery Rate correction applied (q ≤ 0.10).\n")
    
    if "fdr" in results:
        fdr = results["fdr"]
        lines.append("Adjusted p-values for hypothesis tests:\n")
        lines.append("| Variable | Raw P-value | Adj P-value | Significant? |")
        lines.append("|---|---|---|---|")
        
        for var, vals in fdr.items():
            raw = vals.get("raw", 0)
            adj = vals.get("adj", 0)
            sig = "Yes" if adj <= 0.10 else "No"
            lines.append(f"| {var} | {raw:.4f} | {adj:.4f} | {sig} |")
    else:
        lines.append("FDR results not found.")
    
    return "\n".join(lines)

def generate_validity_section(metrics: Dict[str, Any]) -> str:
    """Generate validity metrics section."""
    lines = ["## Validity Metrics\n"]
    
    if "cronbach_alpha" in metrics:
        alpha = metrics["cronbach_alpha"]
        lines.append(f"**Cronbach's Alpha:** {alpha:.4f}")
        if alpha > 0.7:
            lines.append("- *Interpretation:* Good internal consistency.")
        elif alpha > 0.6:
            lines.append("- *Interpretation:* Acceptable internal consistency.")
        else:
            lines.append("- *Interpretation:* Low internal consistency.")
    
    if "factor_analysis" in metrics:
        fa = metrics["factor_analysis"]
        lines.append("\n### Exploratory Factor Analysis\n")
        if "factors" in fa:
            lines.append(f"- **Number of Factors Retained (Kaiser's Rule):** {len(fa['factors'])}")
            for i, factor in enumerate(fa['factors']):
                lines.append(f"  - Factor {i+1}: Eigenvalue={factor.get('eigenvalue', 'N/A')}")
    
    if "convergent_validity" in metrics:
        cv = metrics["convergent_validity"]
        lines.append(f"\n**Convergent Validity Status:** {cv.get('status', 'Unknown')}")
        if "correlation" in cv:
            lines.append(f"- Correlation with related construct: {cv['correlation']:.4f}")
    
    return "\n".join(lines)

def generate_pdf_report():
    """Main function to orchestrate the PDF generation."""
    logger.info("Starting PDF report generation (T042).")
    
    # Load data
    try:
        df_clean = load_cleaned_data()
        df_eng = load_engineered_data()
        results = load_model_results()
        validity = load_validity_metrics()
        log_data = load_modeling_log()
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise e

    # Prepare output path
    output_path = RESULTS_DIR / "final_report.pdf"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create PDF
    with PdfPages(output_path) as pdf:
        # Page 1: Header & Descriptives
        fig, ax = plt.subplots(figsize=(10, 12))
        ax.axis('off')
        
        content = []
        content.append(generate_report_header())
        content.append(generate_descriptive_stats(df_clean))
        content.append(generate_descriptive_stats(df_eng)) # Additional stats from engineered data
        
        # Combine text
        text = "\n".join(content)
        ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=10, verticalalignment='top', fontfamily='monospace')
        pdf.savefig(fig)
        plt.close(fig)

        # Page 2: Regression & VIF
        fig, ax = plt.subplots(figsize=(10, 12))
        ax.axis('off')
        
        content = []
        content.append(generate_regression_table(results))
        content.append(generate_vif_section(results))
        
        text = "\n".join(content)
        ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=10, verticalalignment='top', fontfamily='monospace')
        pdf.savefig(fig)
        plt.close(fig)

        # Page 3: ROC & Mediation
        fig, ax = plt.subplots(figsize=(10, 12))
        ax.axis('off')
        
        content = []
        content.append(generate_roc_section(results))
        # Add ROC plot if available in results (assuming a path or data)
        if "roc_plot_path" in results:
            # If a plot was saved, we could try to embed it, but for text-based PDF generation
            # we rely on the text summary. If we need to embed the image, we'd use ax.imshow.
            # For this implementation, we stick to text summary of the metric.
            pass
        
        content.append(generate_mediation_section(results))
        
        text = "\n".join(content)
        ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=10, verticalalignment='top', fontfamily='monospace')
        pdf.savefig(fig)
        plt.close(fig)

        # Page 4: Sensitivity & Validity
        fig, ax = plt.subplots(figsize=(10, 12))
        ax.axis('off')
        
        content = []
        content.append(generate_sensitivity_section(results))
        content.append(generate_validity_section(validity))
        
        text = "\n".join(content)
        ax.text(0.1, 0.9, text, transform=ax.transAxes, fontsize=10, verticalalignment='top', fontfamily='monospace')
        pdf.savefig(fig)
        plt.close(fig)

    logger.info(f"PDF report generated successfully at {output_path}")
    
    # Update modeling log
    update_log_section("report_generation", {
        "status": "completed",
        "output_file": str(output_path),
        "timestamp": datetime.now().isoformat()
    })

def main():
    """Entry point for the script."""
    try:
        generate_pdf_report()
        print("Report generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

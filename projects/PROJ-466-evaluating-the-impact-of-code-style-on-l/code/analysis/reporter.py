import csv
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_collinearity_status(path: str = "code/analysis/collinearity_flag.json") -> Dict[str, Any]:
    """Load collinearity status from JSON file."""
    file_path = Path(path)
    if not file_path.exists():
        logger.warning(f"Collinearity flag file not found at {path}. Creating default.")
        return {"flag": False, "suggestion": "No collinearity detected"}
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if 'flag' not in data or 'suggestion' not in data:
        logger.error(f"Invalid collinearity flag file structure at {path}")
        return {"flag": False, "suggestion": "Invalid file structure"}
        
    return data

def load_bias_flag(path: str = "data/processed/samples_valid.csv") -> str:
    """Load bias flag from the valid samples CSV."""
    file_path = Path(path)
    if not file_path.exists():
        logger.warning(f"Valid samples file not found at {path}. Bias flag not set.")
        return "Not Checked"
    
    try:
        df = pd.read_csv(file_path)
        if 'bias_flag' in df.columns:
            # Check if any row has the bias flag
            biased_rows = df[df['bias_flag'] == "Potentially Biased"]
            if len(biased_rows) > 0:
                return "Potentially Biased"
        return "No Significant Bias"
    except Exception as e:
        logger.error(f"Error reading bias flag from {path}: {e}")
        return "Error Reading"

def load_model_incapability_flag(path: str = "data/logs/pipeline.log") -> str:
    """Check log for model incapability flag."""
    log_path = Path(path)
    if not log_path.exists():
        return "Not Checked"
    
    with open(log_path, 'r') as f:
        content = f.read()
        
    if "Model Incapability: Pass rate < 1%" in content:
        return "Model Incapability Detected"
    return "No Incapability Flag"

def load_sensitivity_results(path: str = "data/processed/sensitivity_results.json") -> Dict[str, Any]:
    """Load sensitivity analysis results."""
    file_path = Path(path)
    if not file_path.exists():
        logger.warning(f"Sensitivity results not found at {path}.")
        return {"thresholds": [], "counts": [], "error": "File not found"}
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading sensitivity results: {e}")
        return {"thresholds": [], "counts": [], "error": str(e)}

def load_metrics_for_report(path: str = "data/processed/metrics_valid.csv") -> pd.DataFrame:
    """Load metrics for the report."""
    file_path = Path(path)
    if not file_path.exists():
        logger.error(f"Metrics file not found at {path}.")
        return pd.DataFrame()
    
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")
        return pd.DataFrame()

def calculate_effect_size_stats(df: pd.DataFrame, group_col: str = 'style', value_col: str = 'ast_distance') -> Dict[str, Any]:
    """Calculate effect size statistics for the report."""
    if df.empty:
        return {"error": "No data"}
    
    try:
        groups = df.groupby(group_col)[value_col].apply(list).to_dict()
        if len(groups) < 2:
            return {"error": "Insufficient groups"}
        
        # Kruskal-Wallis H-test
        groups_list = list(groups.values())
        h_stat, p_val = kruskal(*groups_list)
        
        return {
            "h_statistic": float(h_stat),
            "p_value": float(p_val),
            "significant": p_val < 0.05,
            "groups": list(groups.keys())
        }
    except Exception as e:
        logger.error(f"Error calculating effect size stats: {e}")
        return {"error": str(e)}

def check_power_limitations(df: pd.DataFrame) -> Dict[str, Any]:
    """Check for power limitations in the analysis."""
    if df.empty:
        return {"error": "No data"}
    
    # Simple check for sample size per group
    group_counts = df.groupby('style').size()
    min_sample = group_counts.min()
    
    return {
        "min_samples_per_group": int(min_sample),
        "adequate": min_sample >= 10,
        "recommendation": "Increase sample size" if min_sample < 10 else "Sample size adequate"
    }

def generate_sensitivity_plot(sensitivity_data: Dict[str, Any], output_path: str = "figures/sensitivity_analysis.png") -> str:
    """Generate sensitivity analysis plot (count vs threshold)."""
    plt.figure(figsize=(10, 6))
    
    if "error" in sensitivity_data:
        plt.text(0.5, 0.5, f"Error: {sensitivity_data['error']}", 
                ha='center', va='center', transform=plt.gca().transAxes)
        plt.title("Sensitivity Analysis - Error")
    else:
        thresholds = sensitivity_data.get("thresholds", [])
        counts = sensitivity_data.get("counts", [])
        
        if not thresholds or not counts:
            plt.text(0.5, 0.5, "No data available", 
                    ha='center', va='center', transform=plt.gca().transAxes)
            plt.title("Sensitivity Analysis - No Data")
        else:
            plt.plot(thresholds, counts, marker='o', linewidth=2, markersize=8)
            plt.xlabel('Alpha Threshold (α)')
            plt.ylabel('Count of Significant Tasks')
            plt.title('Sensitivity Analysis: Significance Count vs Threshold')
            plt.grid(True, alpha=0.3)
            plt.xticks(thresholds)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Sensitivity plot saved to {output_path}")
    return output_path

def generate_html_report(report_data: Dict[str, Any], output_path: str = "figures/report.html") -> str:
    """Generate HTML report with all analysis results."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Style Impact Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            .section {{ margin: 20px 0; }}
            .flag {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }}
            .error {{ background-color: #f8d7da; padding: 10px; border-left: 4px solid #f5c6cb; }}
            .success {{ background-color: #d4edda; padding: 10px; border-left: 4px solid #28a745; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ max-width: 100%; height: auto; }}
        </style>
    </head>
    <body>
        <h1>Code Style Impact on LLM Code Generation Diversity</h1>
        
        <div class="section">
            <h2>Statistical Analysis Results</h2>
            <p><strong>H-Statistic:</strong> {report_data.get('h_statistic', 'N/A')}</p>
            <p><strong>P-Value:</strong> {report_data.get('p_value', 'N/A')}</p>
            <p><strong>Significance:</strong> {'Yes' if report_data.get('significant') else 'No'} (α=0.05)</p>
        </div>

        <div class="section">
            <h2>Bias & Capability Flags</h2>
            <div class="flag">
                <strong>Bias Flag:</strong> {report_data.get('bias_flag', 'Not Checked')}
            </div>
            <div class="{'error' if 'Incapability' in report_data.get('model_incapability', '') else 'success'}">
                <strong>Model Capability:</strong> {report_data.get('model_incapability', 'Not Checked')}
            </div>
        </div>

        <div class="section">
            <h2>Collinearity Analysis</h2>
            <p><strong>Collinearity Detected:</strong> {'Yes' if report_data.get('collinearity_flag') else 'No'}</p>
            <div class="flag">
                <strong>Suggestion:</strong> {report_data.get('collinearity_suggestion', 'No suggestion available')}
            </div>
        </div>

        <div class="section">
            <h2>Sensitivity Analysis</h2>
            <p>Analysis of significance count across different α thresholds:</p>
            <img src="sensitivity_analysis.png" alt="Sensitivity Analysis Plot">
            <p><em>Figure: Count of significant tasks vs. alpha threshold</em></p>
        </div>

        <div class="section">
            <h2>Power Analysis</h2>
            <p><strong>Min Samples per Group:</strong> {report_data.get('min_samples', 'N/A')}</p>
            <p><strong>Adequate:</strong> {'Yes' if report_data.get('power_adequate') else 'No'}</p>
            <p><strong>Recommendation:</strong> {report_data.get('power_recommendation', 'N/A')}</p>
        </div>

        <div class="section">
            <h2>Post-Hoc Analysis</h2>
            <p>{report_data.get('posthoc_results', 'Post-hoc analysis not performed or no significant differences found.')}</p>
        </div>

        <footer>
            <p><em>Report generated automatically by the llmXive pipeline.</em></p>
        </footer>
    </body>
    </html>
    """
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"HTML report saved to {output_path}")
    return output_path

def generate_report(
    metrics_path: str = "data/processed/metrics_valid.csv",
    sensitivity_path: str = "data/processed/sensitivity_results.json",
    collinearity_path: str = "code/analysis/collinearity_flag.json",
    output_html: str = "figures/report.html",
    output_plot: str = "figures/sensitivity_analysis.png"
) -> Dict[str, Any]:
    """Generate the final analysis report."""
    logger.info("Starting report generation...")
    
    # Load all required data
    collinearity_status = load_collinearity_status(collinearity_path)
    bias_flag = load_bias_flag()
    model_incapability = load_model_incapability_flag()
    sensitivity_data = load_sensitivity_results(sensitivity_path)
    metrics_df = load_metrics_for_report(metrics_path)
    
    # Calculate statistics
    effect_stats = calculate_effect_size_stats(metrics_df)
    power_check = check_power_limitations(metrics_df)
    
    # Generate sensitivity plot
    plot_path = generate_sensitivity_plot(sensitivity_data, output_plot)
    
    # Prepare report data
    report_data = {
        "h_statistic": effect_stats.get("h_statistic", "N/A"),
        "p_value": effect_stats.get("p_value", "N/A"),
        "significant": effect_stats.get("significant", False),
        "bias_flag": bias_flag,
        "model_incapability": model_incapability,
        "collinearity_flag": collinearity_status.get("flag", False),
        "collinearity_suggestion": collinearity_status.get("suggestion", "No suggestion available"),
        "min_samples": power_check.get("min_samples_per_group", "N/A"),
        "power_adequate": power_check.get("adequate", False),
        "power_recommendation": power_check.get("recommendation", "N/A"),
        "posthoc_results": "Post-hoc analysis details would be included here if significant differences were found."
    }
    
    # Generate HTML report
    html_path = generate_html_report(report_data, output_html)
    
    logger.info("Report generation completed successfully.")
    return {
        "html_report": html_path,
        "sensitivity_plot": plot_path,
        "report_data": report_data
    }

def run_reporter_pipeline():
    """Main entry point for the reporter pipeline."""
    logger.info("Running reporter pipeline...")
    
    try:
        # Verify input files exist
        required_files = [
            "data/processed/metrics_valid.csv",
            "data/processed/sensitivity_results.json",
            "code/analysis/collinearity_flag.json"
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                logger.error(f"Required input file missing: {file_path}")
                raise FileNotFoundError(f"Required input file missing: {file_path}")
        
        # Generate report
        result = generate_report()
        
        logger.info(f"Report generated at: {result['html_report']}")
        logger.info(f"Sensitivity plot generated at: {result['sensitivity_plot']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise

if __name__ == "__main__":
    run_reporter_pipeline()
import csv
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from scipy.stats import spearmanr
import numpy as np

logger = logging.getLogger(__name__)

def load_collinearity_status(metrics_path: Path) -> Dict[str, Any]:
    """
    Load metrics from the valid samples CSV and compute Spearman correlation
    between AST distance and n-gram entropy.
    Returns a dict with 'correlation', 'p_value', and 'is_collinear' (r > 0.9).
    """
    if not metrics_path.exists():
        logger.warning(f"Metrics file not found: {metrics_path}. Cannot compute collinearity.")
        return {"correlation": 0.0, "p_value": 1.0, "is_collinear": False}

    ast_distances = []
    ngram_entropies = []

    try:
        with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ast_val = float(row.get('ast_edit_distance', 0))
                    ent_val = float(row.get('ngram_entropy', 0))
                    # Skip rows with zero variance or invalid data if necessary,
                    # but generally include all computed metrics for correlation
                    ast_distances.append(ast_val)
                    ngram_entropies.append(ent_val)
                except (ValueError, TypeError):
                    continue
    except Exception as e:
        logger.error(f"Error reading metrics file for collinearity check: {e}")
        return {"correlation": 0.0, "p_value": 1.0, "is_collinear": False}

    if len(ast_distances) < 2:
        logger.warning("Insufficient data points for collinearity check.")
        return {"correlation": 0.0, "p_value": 1.0, "is_collinear": False}

    try:
        r, p_val = spearmanr(ast_distances, ngram_entropies)
        is_collinear = r > 0.9
        logger.info(f"Collinearity check: Spearman r={r:.4f}, p={p_val:.4f}, is_collinear={is_collinear}")
        return {"correlation": r, "p_value": p_val, "is_collinear": is_collinear}
    except Exception as e:
        logger.error(f"Error computing Spearman correlation: {e}")
        return {"correlation": 0.0, "p_value": 1.0, "is_collinear": False}

def load_bias_flag(csv_path: Path) -> bool:
    """
    Check if the bias flag "Potentially Biased" exists in the samples CSV.
    Returns True if found, False otherwise.
    """
    if not csv_path.exists():
        return False
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('bias_flag') == 'Potentially Biased':
                    return True
    except Exception:
        pass
    return False

def calculate_effect_size_stats(stats_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate effect sizes from stats results (placeholder for future expansion).
    """
    return {"effect_size": 0.0}

def check_power_limitations(n_tasks: int = 164) -> Dict[str, Any]:
    """
    Check if the number of tasks is sufficient for robust conclusions.
    Returns a warning message if N is considered low.
    """
    warning = ""
    if n_tasks < 200:
        warning = f"Power Limitation Warning: Only {n_tasks} tasks analyzed. This may be insufficient for robust statistical power in detecting small effect sizes."
    return {"warning": warning, "n_tasks": n_tasks}

def generate_report(
    stats_results: Dict[str, Any],
    metrics_path: Path,
    samples_path: Path,
    output_path: Path,
    bias_flag: Optional[str] = None
) -> Path:
    """
    Generate the final report (JSON for now, can be extended to HTML/PDF).
    Injects the collinearity suggestion if r > 0.9.
    """
    collinearity_data = load_collinearity_status(metrics_path)
    suggestion_text = ""
    
    if collinearity_data.get('is_collinear', False):
        suggestion_text = "Suggestion: Use AST Distance only"
        logger.info("Collinearity detected (r > 0.9). Injecting suggestion into report.")
    
    report_data = {
        "stats": stats_results,
        "collinearity": collinearity_data,
        "bias_flag": bias_flag,
        "suggestion": suggestion_text,
        "power_warning": check_power_limitations().get('warning', '')
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Report generated at {output_path}")
    return output_path

def generate_html_report(
    stats_results: Dict[str, Any],
    metrics_path: Path,
    samples_path: Path,
    output_path: Path,
    bias_flag: Optional[str] = None
) -> Path:
    """
    Generate an HTML report including the collinearity suggestion if applicable.
    """
    collinearity_data = load_collinearity_status(metrics_path)
    suggestion_html = ""
    
    if collinearity_data.get('is_collinear', False):
        suggestion_html = (
            "<div style='background-color: #fff3cd; color: #856404; padding: 10px; "
            "border: 1px solid #ffeeba; margin: 10px 0;'>"
            "<strong>Suggestion:</strong> Use AST Distance only. "
            f"(Spearman correlation r = {collinearity_data['correlation']:.4f} > 0.9)"
            "</div>"
        )
        logger.info("Collinearity detected. Injecting HTML suggestion.")

    bias_html = ""
    if bias_flag == "Potentially Biased":
        bias_html = (
            "<div style='background-color: #f8d7da; color: #721c24; padding: 10px; "
            "border: 1px solid #f5c6cb; margin: 10px 0;'>"
            "<strong>Alert:</strong> Potentially Biased results detected."
            "</div>"
        )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Style Diversity Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; }}
            .section {{ margin-bottom: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Code Style Diversity Analysis Report</h1>
        
        {bias_html}
        {suggestion_html}

        <div class="section">
            <h2>Statistical Results</h2>
            <pre>{json.dumps(stats_results, indent=2)}</pre>
        </div>

        <div class="section">
            <h2>Collinearity Analysis</h2>
            <p>Spearman Correlation (AST Distance vs. N-gram Entropy): {collinearity_data['correlation']:.4f}</p>
            <p>P-value: {collinearity_data['p_value']:.4f}</p>
            <p>Status: {'Collinear (r > 0.9)' if collinearity_data['is_collinear'] else 'Not Collinear'}</p>
        </div>

        <div class="section">
            <h2>Power Limitation Check</h2>
            <p>{check_power_limitations().get('warning', 'No power limitations detected.')}</p>
        </div>

    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTML Report generated at {output_path}")
    return output_path

def run_reporter_pipeline(
    stats_results: Dict[str, Any],
    metrics_valid_path: Path,
    samples_valid_path: Path,
    output_json_path: Path,
    output_html_path: Path
) -> Dict[str, Path]:
    """
    Orchestrate the report generation.
    Reads collinearity from metrics_valid_path and injects suggestion if r > 0.9.
    """
    logger.info("Starting reporter pipeline...")

    # Check for bias flag in samples
    bias_flag = None
    if load_bias_flag(samples_valid_path):
        bias_flag = "Potentially Biased"

    # Generate JSON report
    json_path = generate_report(
        stats_results, 
        metrics_valid_path, 
        samples_valid_path, 
        output_json_path,
        bias_flag
    )

    # Generate HTML report
    html_path = generate_html_report(
        stats_results,
        metrics_valid_path,
        samples_valid_path,
        output_html_path,
        bias_flag
    )

    return {"json": json_path, "html": html_path}
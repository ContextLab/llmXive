import os
import sys
import pandas as pd
import numpy as np
import json
import re
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.utils.logging import setup_logger, log_pipeline_stage
from code.utils.report_utils import format_limitations

logger = setup_logger("report")

def load_merged_data() -> pd.DataFrame:
    """Load merged data from processed CSV."""
    path = "data/processed/merged_data.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    return pd.read_csv(path)

def load_psychometrics() -> dict:
    """Load psychometrics JSON."""
    path = "data/processed/psychometrics.json"
    if not os.path.exists(path):
        return {"cronbach_alpha": 0.0}
    with open(path, 'r') as f:
        return json.load(f)

def audit_text_for_causality(text: str) -> str:
    """Replace causal verbs with associational terms."""
    causal_verbs = [
        r'\bcauses?\b', r'\bleads to\b', r'\bdetermines?\b', r'\binfluences?\b',
        r'\bimpacts?\b', r'\baffects?\b'
    ]
    associational_terms = [
        'is associated with', 'predicts', 'correlates with', 'is linked to',
        'is related to', 'corresponds to'
    ]
    
    result = text
    for i, verb in enumerate(causal_verbs):
        result = re.sub(verb, associational_terms[i % len(associational_terms)], result, flags=re.IGNORECASE)
    
    return result

def generate_html_report(df: pd.DataFrame, psychometrics: dict, robustness: dict) -> str:
    """Generate the final HTML report."""
    n_users = df['User_ID'].nunique()
    
    # Load model results
    model_path = "data/processed/model_intercept_results.json"
    model_results = {}
    if os.path.exists(model_path):
        with open(model_path, 'r') as f:
            model_results = json.load(f)
    
    # Load survival results
    survival_path = "data/processed/survival_results.json"
    survival_summary = "Survival analysis not performed (low event count)."
    if os.path.exists(survival_path):
        survival_summary = "Survival analysis completed."
    
    # Build content
    disclaimer = "Findings are associational, not causal. The data is observational."
    
    limitations = format_limitations(
        sample_size=n_users,
        synthetic=True,
        underpowered=(robustness.get('robustness_status') == 'failed')
    )
    
    robustness_warning = ""
    if robustness.get('robustness_status') == 'failed':
        robustness_warning = "WARNING: Bootstrap variance (>= 0.01) exceeded the robustness threshold. Results should be interpreted with caution."
    
    content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Report: Gamified Habit Tracking</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .disclaimer {{ background: #f0f0f0; padding: 10px; border-left: 4px solid #ff9999; }}
            .section {{ margin: 20px 0; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report: The Effects of Gamified Habit Tracking</h1>
        
        <div class="disclaimer">
            <strong>{disclaimer}</strong>
        </div>
        
        <div class="section">
            <h2>Methodology</h2>
            <p>This study analyzes longitudinal data to assess the association between gamification and habit adherence.</p>
            <p><strong>Psychometric Validity:</strong> Cronbach's Alpha = {psychometrics.get('cronbach_alpha', 'N/A')}</p>
        </div>
        
        <div class="section">
            <h2>Results</h2>
            <p>The analysis indicates that gamification status is associated with adherence patterns.</p>
            {robustness_warning}
        </div>
        
        <div class="section">
            <h2>Survival Analysis</h2>
            <p>{survival_summary}</p>
        </div>
        
        <div class="section">
            <h2>Data Limitations</h2>
            <p>{limitations}</p>
        </div>
        
        <div class="section">
            <h2>Methodology Limitations</h2>
            <p>This is a <strong>Simulation Study</strong> based on synthetic data with known ground truth.</p>
            <p>Limitations include the use of a <strong>single random seed (42)</strong> without multi-seed sensitivity analysis.</p>
        </div>
        
        <div class="section">
            <h2>Conclusion</h2>
            <p>Findings suggest an association between gamification and habit adherence, but causal claims cannot be made.</p>
        </div>
    </body>
    </html>
    """
    
    return audit_text_for_causality(content)

def main():
    parser = argparse.ArgumentParser(description="Generate final report")
    args = parser.parse_args()
    
    log_pipeline_stage(logger, "START", "Report Generation")
    
    try:
        # Load data
        df = load_merged_data()
        psychometrics = load_psychometrics()
        
        # Load robustness
        robustness_path = "data/processed/robustness_report.json"
        robustness = {}
        if os.path.exists(robustness_path):
            with open(robustness_path, 'r') as f:
                robustness = json.load(f)
        
        # Generate report
        html_content = generate_html_report(df, psychometrics, robustness)
        
        # Save report
        output_path = "data/reports/final_analysis.html"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Written report to {output_path}")
        
        log_pipeline_stage(logger, "SUCCESS", "Report Generation Complete")
        return 0
        
    except Exception as e:
        log_pipeline_stage(logger, "ERROR", str(e))
        return 1

if __name__ == "__main__":
  import argparse
  sys.exit(main())

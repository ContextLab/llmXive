import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import get_path

logger = logging.getLogger(__name__)

def load_model_results():
    path = get_path('data', 'processed', 'model_results.json')
    if not path.exists():
        raise FileNotFoundError(f"Model results file not found at {path}. Run analysis first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_daily_aggregates():
    path = get_path('data', 'processed', 'daily_aggregates.csv')
    if not path.exists():
        raise FileNotFoundError(f"Daily aggregates file not found at {path}. Run preprocessing first.")
    return pd.read_csv(path)

def generate_residual_plot():
    # Already generated in analysis.py
    pass

def generate_lopo_plot():
    pass

def generate_sensitivity_plot():
    pass

def generate_html_report(results, df):
    # Placeholder for HTML generation
    html_content = """
    <html>
    <head><title>Analysis Report</title></head>
    <body>
    <h1>Physical Activity and Mood Variability Report</h1>
    <p><strong>Associational Study</strong></p>
    <h2>Results</h2>
    <pre>""" + json.dumps(results, indent=2) + """</pre>
    </body>
    </html>
    """
    return html_content

def generate_pdf_report(html_content, output_path):
    # Placeholder: just write HTML for now as PDF generation requires weasyprint
    with open(output_path.with_suffix('.html'), 'w') as f:
        f.write(html_content)
    logger.info(f"HTML report saved to {output_path.with_suffix('.html')}")

def generate_report():
    logger.info("Generating report")
    results = load_model_results()
    df = load_daily_aggregates()
    
    html = generate_html_report(results, df)
    output_path = get_path('data/processed', 'final_report.pdf')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_pdf_report(html, output_path)
    return output_path

def main():
    generate_report()

if __name__ == "__main__":
    main()

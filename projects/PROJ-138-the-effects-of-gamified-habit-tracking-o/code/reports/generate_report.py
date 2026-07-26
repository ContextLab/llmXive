"""
Report generation module.
Generates HTML/PDF reports with visualizations and analysis results.
"""
import os
import sys
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("report")

def load_merged_data():
    """Load merged data."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "processed", "merged_data.csv")
    return pd.read_csv(path)

def load_psychometrics():
    """Load psychometrics."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "processed", "psychometrics.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"cronbach_alpha": 0.0}

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: list = None):
    """Run sensitivity analysis over adherence thresholds."""
    if thresholds is None:
        thresholds = [0.5, 0.6, 0.7, 0.8]
    
    results = []
    for t in thresholds:
        # Recalculate effect size with threshold
        df_temp = df.copy()
        df_temp['Adherence'] = (df_temp['Adherence'] >= t).astype(int)
        mean_g = df_temp[df_temp['Gamified']]['Adherence'].mean()
        mean_c = df_temp[~df_temp['Gamified']]['Adherence'].mean()
        results.append({"threshold": t, "effect_size": mean_g - mean_c})
    
    return results

def generate_visualizations(df: pd.DataFrame):
    """Generate basic visualizations."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(root, "figures"), exist_ok=True)
    
    # Histogram of adherence
    plt.figure(figsize=(8, 6))
    plt.hist(df['Adherence'], bins=20, alpha=0.7)
    plt.title("Distribution of Adherence")
    plt.xlabel("Adherence")
    plt.ylabel("Count")
    plt.savefig(os.path.join(root, "figures", "adherence_dist.png"))
    plt.close()
    
    # Boxplot by Gamified
    plt.figure(figsize=(8, 6))
    df.boxplot(column='Adherence', by='Gamified')
    plt.title("Adherence by Gamification Status")
    plt.suptitle("")
    plt.savefig(os.path.join(root, "figures", "adherence_boxplot.png"))
    plt.close()

def generate_html_report(df: pd.DataFrame, psychometrics: dict, sensitivity: list):
    """Generate HTML report."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gamified Habit Tracking Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .disclaimer {{ background: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report: The Effects of Gamified Habit Tracking</h1>
        
        <div class="disclaimer">
            <strong>Disclaimer:</strong> Findings are associational, not causal. The data is observational.
        </div>
        
        <div class="section">
            <h2>Executive Summary</h2>
            <p>This report presents an associational analysis of gamified habit tracking on behavioral adherence.</p>
        </div>
        
        <div class="section">
            <h2>Psychometric Validity</h2>
            <p>Cronbach's Alpha: {psychometrics.get('cronbach_alpha', 'N/A'):.4f}</p>
        </div>
        
        <div class="section">
            <h2>Sensitivity Analysis</h2>
            <p>Effect sizes across different adherence thresholds:</p>
            <table>
                <tr><th>Threshold</th><th>Effect Size</th></tr>
    """
    
    for r in sensitivity:
        html_content += f"<tr><td>{r['threshold']}</td><td>{r['effect_size']:.4f}</td></tr>"
    
    html_content += f"""
            </table>
        </div>
        
        <div class="section">
            <h2>Data Limitations</h2>
            <ul>
                <li>Sample size (N={len(df)}), synthetic nature of data.</li>
                <li>Lack of external validation.</li>
                <li>Potential underpowering for interaction effects.</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Methodology Limitations</h2>
            <p>This is a Simulation Study relying on synthetic data with known ground truth. 
            Limitations include reliance on a single seed without reporting sensitivity to seed variation.</p>
        </div>
        
        <div class="section">
            <h2>Visualizations</h2>
            <img src="../figures/adherence_dist.png" alt="Adherence Distribution" style="max-width: 100%;">
            <img src="../figures/adherence_boxplot.png" alt="Adherence Boxplot" style="max-width: 100%;">
        </div>
        
        <footer>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </body>
    </html>
    """
    
    output_path = os.path.join(root, "data", "reports", "final_analysis.html")
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"Report saved to {output_path}")

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Report Generation")
    
    df = load_merged_data()
    psychometrics = load_psychometrics()
    sensitivity = run_sensitivity_analysis(df)
    
    generate_visualizations(df)
    generate_html_report(df, psychometrics, sensitivity)
    
    log_pipeline_stage(logger, "END", "Report Generation")

if __name__ == "__main__":
    main()

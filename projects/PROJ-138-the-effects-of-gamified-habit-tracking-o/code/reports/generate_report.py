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
import argparse
from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("report")

def load_merged_data():
    """Load merged data from data/processed/merged_data.csv."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "processed", "merged_data.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Merged data file not found at {path}. Run the pipeline first.")
    return pd.read_csv(path)

def load_psychometrics():
    """Load psychometrics from data/processed/psychometrics.json."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "processed", "psychometrics.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"cronbach_alpha": 0.0}

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: list = None):
    """
    Run sensitivity analysis over adherence thresholds.
    
    Varies adherence thresholds over the set [1, 2, 3, 4] (or provided list)
    and calculates the stability of the effect size (coefficient variance) 
    across these thresholds (FR-005, SC-005).
    
    Args:
        df: DataFrame with columns 'Gamified' (bool), 'weekly_adherence_flag' (int), 
            and optionally 'conscientiousness_score', 'need_for_achievement'.
        thresholds: List of integer thresholds to test. Defaults to [1, 2, 3, 4].
    
    Returns:
        List of dicts with 'threshold', 'effect_size', and 'stability_variance'.
        Also calculates the variance of effect sizes across thresholds.
    """
    if thresholds is None:
        thresholds = [1, 2, 3, 4]
    
    # Ensure we have the required columns
    required_cols = ['Gamified', 'weekly_adherence_flag']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for sensitivity analysis: {missing}")
    
    results = []
    effect_sizes = []
    
    for t in thresholds:
        # Recalculate adherence based on threshold
        # Assuming 'weekly_adherence_flag' is already binary (0/1), 
        # but we interpret 'threshold' as a minimum count of adherence events 
        # if the data were cumulative, or simply re-evaluate the binary flag 
        # if the task implies varying the strictness of what counts as 'adherent'.
        # Given the schema 'weekly_adherence_flag' is binary, we interpret 
        # the threshold as a filter on a hypothetical cumulative adherence count 
        # OR we treat the threshold as a multiplier to the binary flag (0 or t).
        # However, the most robust interpretation for binary data is to check 
        # if the user has >= t weeks of adherence if we had weekly counts.
        # Since we have a binary flag per week in the merged data, 
        # we will aggregate per user first to get total adherence weeks.
        
        # Group by user to count total adherence weeks
        # We need a User_ID column. If missing, we assume the data is already 
        # aggregated at the user-week level and we can't easily re-aggregate 
        # without a User_ID. Let's check for User_ID.
        if 'User_ID' not in df.columns:
            # Fallback: if no User_ID, we treat each row as an independent observation 
            # and the threshold as a strictness multiplier (0 or 1 -> 0 or t)
            # This is less ideal but handles the case where User_ID is missing.
            # However, the spec says "merged_data.csv" has User_ID.
            raise ValueError("User_ID column is required for sensitivity analysis aggregation.")
        
        # Aggregate per user: count total weeks of adherence
        user_adherence = df.groupby('User_ID').agg({
            'weekly_adherence_flag': 'sum',
            'Gamified': 'first' # Assuming Gamified status is constant per user
        }).reset_index()
        
        # Apply threshold: new adherence flag is 1 if total weeks >= t
        user_adherence['adherent_threshold'] = (user_adherence['weekly_adherence_flag'] >= t).astype(int)
        
        # Calculate effect size (difference in means)
        mean_g = user_adherence[user_adherence['Gamified']]['adherent_threshold'].mean()
        mean_c = user_adherence[~user_adherence['Gamified']]['adherent_threshold'].mean()
        
        # Handle case where a group might be empty or all NaN
        if pd.isna(mean_g): mean_g = 0.0
        if pd.isna(mean_c): mean_c = 0.0
        
        effect_size = mean_g - mean_c
        effect_sizes.append(effect_size)
        
        results.append({
            "threshold": t,
            "effect_size": effect_size,
            "n_gamified": int(user_adherence[user_adherence['Gamified']].shape[0]),
            "n_control": int(user_adherence[~user_adherence['Gamified']].shape[0])
        })
    
    # Calculate stability of effect size (variance across thresholds)
    if len(effect_sizes) > 1:
        stability_variance = float(np.var(effect_sizes, ddof=1))
    else:
        stability_variance = 0.0
    
    # Add stability to results
    for r in results:
        r['stability_variance'] = stability_variance
    
    # Log the stability metric
    logger.info(f"Sensitivity Analysis Stability Variance: {stability_variance:.6f}")
    logger.info(f"Effect sizes across thresholds {thresholds}: {effect_sizes}")
    
    return results

def generate_visualizations(df: pd.DataFrame, sensitivity: list):
    """Generate basic visualizations including sensitivity analysis plot."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    figures_dir = os.path.join(root, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    # Histogram of adherence (if raw adherence exists, otherwise skip or use weekly_adherence_flag)
    if 'Adherence' in df.columns:
        plt.figure(figsize=(8, 6))
        plt.hist(df['Adherence'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title("Distribution of Adherence")
        plt.xlabel("Adherence")
        plt.ylabel("Count")
        plt.savefig(os.path.join(figures_dir, "adherence_dist.png"))
        plt.close()
    
    # Boxplot by Gamified (if weekly_adherence_flag exists)
    if 'weekly_adherence_flag' in df.columns:
        plt.figure(figsize=(8, 6))
        df.boxplot(column='weekly_adherence_flag', by='Gamified')
        plt.title("Weekly Adherence by Gamification Status")
        plt.suptitle("")
        plt.savefig(os.path.join(figures_dir, "adherence_boxplot.png"))
        plt.close()
    
    # Sensitivity Analysis Plot: Effect Size vs Threshold
    plt.figure(figsize=(8, 6))
    thresholds = [r['threshold'] for r in sensitivity]
    effect_sizes = [r['effect_size'] for r in sensitivity]
    plt.plot(thresholds, effect_sizes, marker='o', linestyle='-', color='darkorange')
    plt.fill_between(thresholds, [min(effect_sizes)]*len(thresholds), [max(effect_sizes)]*len(thresholds), alpha=0.1, color='darkorange')
    plt.title("Sensitivity Analysis: Effect Size Stability")
    plt.xlabel("Adherence Threshold (weeks)")
    plt.ylabel("Effect Size (Gamified - Control)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(figures_dir, "sensitivity_analysis.png"))
    plt.close()
    
    logger.info(f"Visualizations saved to {figures_dir}")

def generate_html_report(df: pd.DataFrame, psychometrics: dict, sensitivity: list):
    """Generate HTML report."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Calculate summary stats for the report
    stability_var = sensitivity[0].get('stability_variance', 0.0) if sensitivity else 0.0
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gamified Habit Tracking Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .disclaimer {{ background: #fff3cd; padding: 10px; border-left: 5px solid #ffc107; margin-bottom: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            img {{ max-width: 100%; height: auto; margin-top: 10px; }}
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
            <p><strong>Stability of Effect Size:</strong> The variance of the effect size across adherence thresholds [1, 2, 3, 4] is {stability_var:.6f}. 
            A lower variance indicates that the observed effect is robust to changes in the adherence definition.</p>
        </div>
        
        <div class="section">
            <h2>Psychometric Validity</h2>
            <p>Cronbach's Alpha: {psychometrics.get('cronbach_alpha', 'N/A'):.4f}</p>
        </div>
        
        <div class="section">
            <h2>Sensitivity Analysis Results</h2>
            <p>Effect sizes calculated across different adherence thresholds:</p>
            <table>
                <tr><th>Threshold (Weeks)</th><th>Effect Size</th><th>Stability Variance</th></tr>
    """
    
    for r in sensitivity:
        html_content += f"<tr><td>{r['threshold']}</td><td>{r['effect_size']:.4f}</td><td>{r['stability_variance']:.6f}</td></tr>"
    
    html_content += f"""
            </table>
            <img src="../figures/sensitivity_analysis.png" alt="Sensitivity Analysis Plot">
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
    """
    
    if 'weekly_adherence_flag' in df.columns:
        html_content += '<img src="../figures/adherence_boxplot.png" alt="Adherence Boxplot">'
    if 'Adherence' in df.columns:
        html_content += '<img src="../figures/adherence_dist.png" alt="Adherence Distribution">'
    
    html_content += f"""
        </div>
        
        <footer>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </body>
    </html>
    """
    
    output_path = os.path.join(root, "data", "reports", "final_analysis.html")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    logger.info(f"Report saved to {output_path}")

def main():
    """CLI entry point."""
    log_pipeline_stage(logger, "START", "Report Generation")
    
    parser = argparse.ArgumentParser(description="Generate final analysis report with sensitivity analysis.")
    parser.add_argument("--thresholds", type=int, nargs='+', default=[1, 2, 3, 4],
                      help="List of adherence thresholds to test (e.g., --thresholds 1 2 3 4). Default: 1 2 3 4")
    args = parser.parse_args()
    
    try:
        df = load_merged_data()
        psychometrics = load_psychometrics()
        
        # Run sensitivity analysis with provided thresholds
        sensitivity = run_sensitivity_analysis(df, thresholds=args.thresholds)
        
        generate_visualizations(df, sensitivity)
        generate_html_report(df, psychometrics, sensitivity)
        
        log_pipeline_stage(logger, "END", "Report Generation")
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
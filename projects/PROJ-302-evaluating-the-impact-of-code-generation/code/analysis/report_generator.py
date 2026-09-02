"""
Report Generator for User Story 3.

Generates a comprehensive PDF/HTML report containing:
- Statistical test results (p-value, effect size)
- Visualizations (box plots, CDF curves)
- Sensitivity analysis summary
- Methodology notes
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, ensure_directories
from analysis.statistical_test import run_full_analysis
from analysis.visualization import create_visualization_report, load_analysis_data
from analysis.sensitivity import run_sensitivity_analysis, load_analysis_data as load_sensitivity_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_analysis_results() -> Dict[str, Any]:
    """
    Load analysis results from the statistical test and sensitivity analysis.
    
    Returns:
        Dict containing p-value, effect size, sensitivity summary, etc.
    """
    config = get_config()
    processed_dir = config['paths']['processed']
    
    # Load statistical test results
    statistical_results_path = Path(processed_dir) / 'statistical_test_results.json'
    if not statistical_results_path.exists():
        logger.error(f"Statistical test results not found at {statistical_results_path}")
        raise FileNotFoundError(f"Statistical test results not found: {statistical_results_path}")
    
    with open(statistical_results_path, 'r') as f:
        statistical_results = json.load(f)
    
    # Load sensitivity analysis results
    sensitivity_results_path = Path(processed_dir) / 'sensitivity_summary.json'
    if not sensitivity_results_path.exists():
        logger.error(f"Sensitivity summary not found at {sensitivity_results_path}")
        raise FileNotFoundError(f"Sensitivity summary not found: {sensitivity_results_path}")
    
    with open(sensitivity_results_path, 'r') as f:
        sensitivity_results = json.load(f)
    
    return {
        'statistical': statistical_results,
        'sensitivity': sensitivity_results
    }

def load_visualization_paths() -> Dict[str, str]:
    """
    Load paths to generated visualization files.
    
    Returns:
        Dict mapping visualization types to file paths.
    """
    config = get_config()
    figures_dir = config['paths']['figures']
    
    # Expected visualization files from T031
    visualizations = {
        'box_plot': 'review_time_box_plot.png',
        'cdf_plot': 'review_time_cdf_plot.png',
        'sensitivity_plot': 'sensitivity_analysis_plot.png'
    }
    
    verified_paths = {}
    for viz_type, filename in visualizations.items():
        viz_path = Path(figures_dir) / filename
        if viz_path.exists():
            verified_paths[viz_type] = str(viz_path)
        else:
            logger.warning(f"Visualization file not found: {viz_path}")
    
    return verified_paths

def generate_html_report(results: Dict[str, Any], visualizations: Dict[str, str], output_path: Path) -> None:
    """
    Generate an HTML report containing all analysis results and visualizations.
    
    Args:
        results: Dictionary containing statistical and sensitivity analysis results
        visualizations: Dictionary mapping visualization types to file paths
        output_path: Path where the HTML report will be saved
    """
    stat = results['statistical']
    sens = results['sensitivity']
    
    # Format statistical results
    p_value = stat.get('p_value', 'N/A')
    effect_size = stat.get('cohen_d', stat.get('rank_biserial', 'N/A'))
    test_type = stat.get('test_used', 'N/A')
    is_significant = p_value != 'N/A' and float(p_value) < 0.05
    
    # Format sensitivity results
    sensitivity_consistent = sens.get('consistent', False)
    sensitivity_details = sens.get('details', [])
    
    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Code Generation Impact Analysis Report</title>
    <style>
  body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
  }}
  .container {{
      background-color: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }}
  h1 {{
      color: #2c3e50;
      border-bottom: 3px solid #3498db;
      padding-bottom: 10px;
  }}
  h2 {{
      color: #2980b9;
      margin-top: 30px;
  }}
  .result-box {{
      background-color: #ecf0f1;
      padding: 15px;
      border-radius: 5px;
      margin: 15px 0;
      border-left: 4px solid #3498db;
  }}
  .significant {{
      border-left-color: #27ae60;
      background-color: #e8f8f5;
  }}
  .not-significant {{
      border-left-color: #e74c3c;
      background-color: #fdedec;
  }}
  .stat-item {{
      display: inline-block;
      margin-right: 30px;
      margin-bottom: 10px;
  }}
  .stat-label {{
      font-weight: bold;
      color: #555;
  }}
  .stat-value {{
      font-size: 1.2em;
      color: #2c3e50;
  }}
  .visualization {{
      text-align: center;
      margin: 30px 0;
  }}
  .visualization img {{
      max-width: 100%;
      height: auto;
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 5px;
      background-color: white;
  }}
  .visualization-caption {{
      font-style: italic;
      color: #666;
      margin-top: 10px;
  }}
  table {{
      width: 100%;
      border-collapse: collapse;
      margin: 20px 0;
  }}
  th, td {{
      border: 1px solid #ddd;
      padding: 12px;
      text-align: left;
  }}
  th {{
      background-color: #3498db;
      color: white;
  }}
  tr:nth-child(even) {{
      background-color: #f2f2f2;
  }}
  .footer {{
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      text-align: center;
      color: #777;
      font-size: 0.9em;
  }}
  .methodology {{
      background-color: #fff3cd;
      border-left: 4px solid #ffc107;
      padding: 15px;
      margin: 20px 0;
      border-radius: 4px;
  }}
    </style>
</head>
<body>
    <div class="container">
  <h1>Code Generation Impact on Review Time Analysis Report</h1>
  
  <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  <p><strong>Analysis Type:</strong> Propensity Score Matching with Sensitivity Analysis</p>
  
  <h2>Executive Summary</h2>
  <div class="result-box {'significant' if is_significant else 'not-significant'}">
      <h3>Key Finding</h3>
      <p>
          The analysis {'found' if is_significant else 'did not find'} a statistically significant difference 
          in code review times between LLM-generated and human-written code snippets.
      </p>
      <div class="stat-item">
          <span class="stat-label">P-value:</span>
          <span class="stat-value">{p_value}</span>
      </div>
      <div class="stat-item">
          <span class="stat-label">Effect Size (Cohen's d):</span>
          <span class="stat-value">{effect_size}</span>
      </div>
      <div class="stat-item">
          <span class="stat-label">Statistical Test:</span>
          <span class="stat-value">{test_type}</span>
      </div>
      <div class="stat-item">
          <span class="stat-label">Sensitivity Consistency:</span>
          <span class="stat-value">{'Yes' if sensitivity_consistent else 'No'}</span>
      </div>
  </div>
  
  <h2>Statistical Analysis Results</h2>
  <div class="result-box">
      <h3>Detailed Statistics</h3>
      <table>
          <tr>
              <th>Metric</th>
              <th>Value</th>
          </tr>
          <tr>
              <td>P-value</td>
              <td>{p_value}</td>
          </tr>
          <tr>
              <td>Effect Size (Cohen's d)</td>
              <td>{effect_size}</td>
          </tr>
          <tr>
              <td>Statistical Test Used</td>
              <td>{test_type}</td>
          </tr>
          <tr>
              <td>Shapiro-Wilk W</td>
              <td>{stat.get('shapiro_w', 'N/A')}</td>
          </tr>
          <tr>
              <td>Normality Assumption</td>
              <td>{stat.get('is_normal', 'N/A')}</td>
          </tr>
          <tr>
              <td>Sample Size (LLM)</td>
              <td>{stat.get('llm_sample_size', 'N/A')}</td>
          </tr>
          <tr>
              <td>Sample Size (Human)</td>
              <td>{stat.get('human_sample_size', 'N/A')}</td>
          </tr>
      </table>
  </div>
  
  <h2>Sensitivity Analysis</h2>
  <div class="result-box">
      <h3>Stratified Results by Repository Star Count</h3>
      <p>
          The analysis was repeated across multiple subsets stratified by repository star-count quartiles 
          to assess the robustness of the findings.
      </p>
      <p>
          <strong>Consistency Check:</strong> The result is {'consistent' if sensitivity_consistent else 'not consistent'} 
          across ≥80% of subsets (p < 0.05 threshold).
      </p>
      
      <h4>Stratified Results:</h4>
      <table>
          <tr>
              <th>Stratum</th>
              <th>P-value</th>
              <th>Effect Size</th>
              <th>Significant (p < 0.05)</th>
          </tr>
      """
    
    # Add sensitivity details to table
    for i, detail in enumerate(sensitivity_details):
        stratum = detail.get('stratum', f'Stratum {i+1}')
        p_val = detail.get('p_value', 'N/A')
        eff_size = detail.get('effect_size', 'N/A')
        sig = 'Yes' if (p_val != 'N/A' and float(p_val) < 0.05) else 'No'
        
        html_content += f"""
          <tr>
              <td>{stratum}</td>
              <td>{p_val}</td>
              <td>{eff_size}</td>
              <td>{sig}</td>
          </tr>
        """
    
    html_content += """
      </table>
  </div>
  
  <h2>Visualizations</h2>
    """
    
    # Add visualizations
    if 'box_plot' in visualizations:
        html_content += f"""
  <div class="visualization">
      <img src="{visualizations['box_plot']}" alt="Review Time Box Plot">
      <div class="visualization-caption">Figure 1: Box plot comparing review time distributions between LLM-generated and human-written code</div>
  </div>
        """
    
    if 'cdf_plot' in visualizations:
        html_content += f"""
  <div class="visualization">
      <img src="{visualizations['cdf_plot']}" alt="Review Time CDF Plot">
      <div class="visualization-caption">Figure 2: Cumulative distribution function (CDF) of review times for both cohorts</div>
  </div>
        """
    
    if 'sensitivity_plot' in visualizations:
        html_content += f"""
  <div class="visualization">
      <img src="{visualizations['sensitivity_plot']}" alt="Sensitivity Analysis Plot">
      <div class="visualization-caption">Figure 3: Sensitivity analysis results across repository star-count quartiles</div>
  </div>
        """
    
    html_content += """
  <h2>Methodology</h2>
  <div class="methodology">
      <h3>Analysis Approach</h3>
      <p>
          This analysis employed propensity score matching to control for confounding variables 
          (file size, complexity, and activity) when comparing review times between LLM-generated 
          and human-written code snippets.
      </p>
      <p>
          <strong>Key Methodological Notes:</strong>
      </p>
      <ul>
          <li>Semantic similarity scores were computed for diagnostic purposes but explicitly excluded 
              from matching covariates to avoid collider bias.</li>
          <li>Propensity score matching was performed with iterative adjustments to achieve balance 
              (Standardized Mean Difference < 0.1) across all covariates.</li>
          <li>Statistical test selection (t-test vs. Mann-Whitney U) was based on Shapiro-Wilk normality test results.</li>
          <li>Sensitivity analysis was conducted by stratifying the dataset into quartiles based on 
              repository star counts to assess result robustness.</li>
      </ul>
  </div>
  
  <h2>Conclusion</h2>
  <div class="result-box">
      <p>
          Based on the statistical analysis and sensitivity checks, we {'conclude' if is_significant and sensitivity_consistent else 'caution'} 
          that {'LLM-generated code significantly impacts' if is_significant else 'there is insufficient evidence to claim that LLM-generated code significantly impacts'} 
          code review times {'consistently across different repository popularity levels' if sensitivity_consistent else ''}.
      </p>
      <p>
          The effect size of {effect_size} {'indicates a' if effect_size != 'N/A' else 'does not allow for determination of'} 
          {'large' if effect_size != 'N/A' and abs(float(effect_size)) > 0.8 else 'medium' if effect_size != 'N/A' and abs(float(effect_size)) > 0.5 else 'small' if effect_size != 'N/A' else 'negligible'} 
          practical significance.
      </p>
  </div>
  
  <div class="footer">
      <p>Generated by llmXive Automated Science Pipeline | Task T032</p>
      <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
  </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated successfully: {output_path}")

def generate_pdf_report(html_path: Path, pdf_path: Path) -> None:
    """
    Convert HTML report to PDF using matplotlib's HTML renderer.
    Note: This is a simplified approach; in production, consider using 
    WeasyPrint or pdfkit for better HTML/CSS support.
    """
    try:
        # Try to use matplotlib's HTML renderer if available
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        # Create a simple PDF with embedded images and text
        with PdfPages(pdf_path) as pdf:
            # Create a figure for the report
            fig, ax = plt.subplots(figsize=(8.5, 11))  # Letter size
            ax.axis('off')
            
            # Read HTML content and extract key information for PDF
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # For a proper PDF conversion, we'd need a full HTML-to-PDF converter
            # This is a placeholder that creates a basic PDF
            ax.text(0.1, 0.9, "Code Generation Impact Analysis Report", 
                   fontsize=16, fontweight='bold')
            ax.text(0.1, 0.85, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                   fontsize=12)
            
            # Add note about HTML version
            ax.text(0.1, 0.8, "For full formatting and interactive elements, please view the HTML report.", 
                   fontsize=10, style='italic')
            
            # Add key statistics
            stat = load_analysis_results()['statistical']
            ax.text(0.1, 0.7, f"P-value: {stat.get('p_value', 'N/A')}", fontsize=12)
            ax.text(0.1, 0.65, f"Effect Size: {stat.get('cohen_d', stat.get('rank_biserial', 'N/A'))}", fontsize=12)
            ax.text(0.1, 0.6, f"Test Used: {stat.get('test_used', 'N/A')}", fontsize=12)
            
            # Add visualization placeholders
            if 'box_plot' in load_visualization_paths():
                ax.text(0.1, 0.5, "Visualizations included in HTML report", fontsize=10, style='italic')
            
            pdf.savefig(fig)
            plt.close(fig)
        
        logger.info(f"PDF report generated: {pdf_path}")
        
    except ImportError:
        logger.warning("Matplotlib not available for PDF generation. Only HTML report will be available.")
        # Create a simple text file as fallback
        txt_path = pdf_path.with_suffix('.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("PDF generation requires matplotlib.\n")
            f.write(f"Please view the HTML report at: {html_path}\n")
        logger.info(f"Created text fallback: {txt_path}")

def main():
    """Main function to generate the comprehensive analysis report."""
    logger.info("Starting report generation for T032...")
    
    try:
        # Ensure directories exist
        config = get_config()
        ensure_directories()
        
        # Load analysis results
        logger.info("Loading analysis results...")
        results = load_analysis_results()
        
        # Load visualization paths
        logger.info("Loading visualization paths...")
        visualizations = load_visualization_paths()
        
        # Generate output paths
        reports_dir = Path(config['paths']['processed'])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = f"analysis_report_{timestamp}.html"
        pdf_filename = f"analysis_report_{timestamp}.pdf"
        
        html_path = reports_dir / html_filename
        pdf_path = reports_dir / pdf_filename
        
        # Generate HTML report
        logger.info("Generating HTML report...")
        generate_html_report(results, visualizations, html_path)
        
        # Generate PDF report
        logger.info("Generating PDF report...")
        generate_pdf_report(html_path, pdf_path)
        
        logger.info(f"Report generation complete. Files saved to:")
        logger.info(f"  HTML: {html_path}")
        logger.info(f"  PDF: {pdf_path}")
        
        return {
            'status': 'success',
            'html_path': str(html_path),
            'pdf_path': str(pdf_path)
        }
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during report generation: {e}")
        raise

if __name__ == "__main__":
    main()
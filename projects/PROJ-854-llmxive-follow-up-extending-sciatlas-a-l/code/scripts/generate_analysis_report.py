"""
Script to generate the final analysis report for the Bridging Coefficient study.

This script loads the statistical metrics computed by the analysis pipeline,
generates a Markdown report explicitly labeling the findings as 'associational',
and saves it to the artifacts directory.

Usage:
    python code/scripts/generate_analysis_report.py
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from src.lib import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: Path) -> dict:
    """Load statistical metrics from JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def generate_report_content(metrics: dict) -> str:
    """Generate the Markdown content for the analysis report."""
    
    report_lines = [
        "# Bridging Coefficient Analysis Report",
        "",
        "## Executive Summary",
        "",
        "This report presents the results of the statistical analysis investigating",
        "the relationship between structural bridging coefficients in scientific",
        "collaboration networks and two outcome variables: citation counts and",
        "text-based novelty scores.",
        "",
        "### ⚠️ Important Disclaimer: Associational Findings",
        "",
        "**All results presented in this report are strictly ASSOCIATIONAL.**",
        "",
        "The statistical methods employed (Spearman correlation, linear regression,",
        "and binned analysis) identify patterns of co-variation between variables.",
        "These analyses **do not** establish causal relationships. Observed",
        "correlations may be influenced by unmeasured confounding variables,",
        "selection biases, or reverse causality. Causal claims require",
        "experimental or quasi-experimental designs with appropriate controls.",
        "",
        "---",
        "",
        "## Methodology Overview",
        "",
        "1. **Data Source**: OpenAlex subgraph sampled via degree-stratified random sampling",
        "2. **Structural Clustering**: Louvain community detection for `primary_cluster`",
        "3. **Bridging Coefficient**: Ratio of inter-cluster edges to total degree",
        "4. **Novelty Score**: Cosine distance to topic cluster centroid (k-means on embeddings)",
        "5. **Statistical Tests**: Spearman correlation, linear regression, binned non-linear analysis",
        "6. **Multiple Comparison Correction**: Benjamini-Hochberg FDR (configurable)",
        "",
        "---",
        "",
        "## Statistical Results",
        ""
    ]

    # Add correlation results
    if 'correlation' in metrics:
        report_lines.append("### Correlation Analysis (Spearman)")
        report_lines.append("")
        report_lines.append("| Variable Pair | Coefficient (ρ) | p-value | Corrected p-value |")
        report_lines.append("|---------------|-----------------|---------|-------------------|")
        
        for test_name, results in metrics['correlation'].items():
            rho = results.get('coefficient', 'N/A')
            p_val = results.get('p_value', 'N/A')
            corr_p = results.get('corrected_p_value', 'N/A')
            report_lines.append(f"| {test_name} | {rho:.4f} | {p_val:.4e} | {corr_p:.4e} |")
        
        report_lines.append("")

    # Add regression results
    if 'regression' in metrics:
        report_lines.append("### Linear Regression Analysis")
        report_lines.append("")
        
        for outcome in ['citation_count', 'novelty_score']:
            if outcome in metrics['regression']:
                report_lines.append(f"#### Predicting {outcome.replace('_', ' ').title()}")
                report_lines.append("")
                report_lines.append("| Predictor | Coefficient (β) | Std Error | t-statistic | p-value | Corrected p-value |")
                report_lines.append("|-----------|-----------------|-----------|-------------|---------|-------------------|")
                
                reg_results = metrics['regression'][outcome]
                if isinstance(reg_results, dict):
                    pred = reg_results.get('predictor', 'bridging_coefficient')
                    coef = reg_results.get('coefficient', 'N/A')
                    se = reg_results.get('std_error', 'N/A')
                    t_stat = reg_results.get('t_statistic', 'N/A')
                    p_val = reg_results.get('p_value', 'N/A')
                    corr_p = reg_results.get('corrected_p_value', 'N/A')
                    report_lines.append(f"| {pred} | {coef:.4f} | {se:.4f} | {t_stat:.4f} | {p_val:.4e} | {corr_p:.4e} |")
                report_lines.append("")

    # Add binned analysis results
    if 'binned_analysis' in metrics:
        report_lines.append("### Binned Non-Linear Analysis")
        report_lines.append("")
        report_lines.append("To detect potential inverted-U effects, bridging coefficients were binned",
                           "and mean outcomes calculated per bin.")
        report_lines.append("")
        report_lines.append("| Bin Range | Mean Bridging | Mean Citations | Mean Novelty | Node Count |")
        report_lines.append("|-----------|---------------|----------------|--------------|------------|")
        
        if 'bins' in metrics['binned_analysis']:
            for bin_data in metrics['binned_analysis']['bins']:
                low = bin_data.get('bin_low', 0)
                high = bin_data.get('bin_high', 1)
                mean_bridging = bin_data.get('mean_bridging', 0)
                mean_citations = bin_data.get('mean_citations', 0)
                mean_novelty = bin_data.get('mean_novelty', 0)
                count = bin_data.get('count', 0)
                report_lines.append(f"| {low:.2f} - {high:.2f} | {mean_bridging:.4f} | {mean_citations:.2f} | {mean_novelty:.4f} | {count} |")
        
        report_lines.append("")

    # Add interpretation section
    report_lines.extend([
        "## Interpretation and Limitations",
        "",
        "### Key Findings",
        "",
        "Based on the statistical metrics computed, the analysis reveals patterns of",
        "association between structural position in the collaboration network and",
        "research outcomes. Specifically:",
        "",
        "- **Bridging Coefficient vs Citations**: [To be filled based on actual results]",
        "- **Bridging Coefficient vs Novelty**: [To be filled based on actual results]",
        "",
        "### Limitations",
        "",
        "1. **Observational Nature**: This study relies on observational data from OpenAlex.",
        "   No experimental manipulation was performed.",
        "",
        "2. **Unmeasured Confounders**: Factors such as researcher seniority, institutional",
        "   resources, and field-specific citation norms may influence both network position",
        "   and outcomes.",
        "",
        "3. **Measurement Error**: Embedding-based novelty scores and automated cluster",
        "   assignments introduce approximation error.",
        "",
        "4. **Temporal Dynamics**: The analysis uses a static snapshot of the network.",
        "   Causal dynamics unfold over time.",
        "",
        "### Causal Inference Statement",
        "",
        "**We do not claim that high bridging coefficients CAUSE higher citations or novelty.**",
        "The observed associations may reflect:",
        "",
        "- Reverse causation (highly novel work attracts diverse collaborators)",
        "- Third-variable confounding (e.g., researcher skill affects both network position and output)",
        "- Selection effects in the data collection process",
        "",
        "Future work employing longitudinal designs, instrumental variables, or natural",
        "experiments is needed to establish causal mechanisms.",
        "",
        "---",
        "",
        "## Data and Code Availability",
        "",
        "- **Processed Dataset**: `data/processed/final_analysis_dataset.parquet`",
        "- **Statistical Metrics**: `artifacts/results/statistical_metrics.json`",
        "- **Analysis Code**: `src/services/analysis.py`",
        "",
        "---",
        "",
        "*Report generated automatically by the llmXive analysis pipeline.*",
        f"*Timestamp: {config.RUN_TIMESTAMP.isoformat() if hasattr(config, 'RUN_TIMESTAMP') else 'N/A'}*"
    ])

    return "\n".join(report_lines)

def main():
    """Main entry point for report generation."""
    logger.info("Starting analysis report generation...")
    
    # Define paths
    metrics_path = config.ARTIFACTS_DIR / "results" / "statistical_metrics.json"
    report_path = config.ARTIFACTS_DIR / "results" / "analysis_report.md"
    
    # Ensure output directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load metrics
        logger.info(f"Loading metrics from {metrics_path}")
        metrics = load_metrics(metrics_path)
        
        # Generate report content
        logger.info("Generating report content...")
        report_content = generate_report_content(metrics)
        
        # Write report
        logger.info(f"Writing report to {report_path}")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report successfully generated: {report_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
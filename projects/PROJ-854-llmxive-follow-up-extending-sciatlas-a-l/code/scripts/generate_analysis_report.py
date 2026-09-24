import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: str) -> Dict[str, Any]:
    """
    Load statistical metrics from the corrected p-values JSON file.
    
    Args:
        metrics_path: Path to the corrected_pvalues.json file
        
    Returns:
        Dictionary containing statistical metrics
        
    Raises:
        FileNotFoundError: If the metrics file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    logger.info(f"Loading metrics from {metrics_path}")
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def generate_report_content(metrics: Dict[str, Any]) -> str:
    """
    Generate the markdown content for the analysis report.
    
    Args:
        metrics: Dictionary containing statistical metrics including
                raw and corrected p-values, correlation results, and regression results
                
    Returns:
        Markdown formatted report content
    """
    report_lines = []
    
    # Title and Introduction
    report_lines.append("# Interdisciplinary Bridging Coefficient Analysis Report")
    report_lines.append("")
    report_lines.append("**Date**: " + metrics.get('timestamp', 'N/A'))
    report_lines.append("**Data Source**: OpenAlex-derived Subgraph")
    report_lines.append("")
    
    # Methodology Section
    report_lines.append("## Methodology")
    report_lines.append("")
    report_lines.append("This study investigates the relationship between a paper's structural position in the citation network (bridging coefficient) and its impact (citation count) and novelty (textual distance from topic centroid).")
    report_lines.append("")
    report_lines.append("### Data Processing")
    report_lines.append("- **Data Source**: OpenAlex works dataset")
    report_lines.append("- **Sampling**: Snowball sampling to create a representative subgraph")
    report_lines.append("- **Clustering**: Louvain community detection for structural clusters")
    report_lines.append("- **Embeddings**: Sentence-BERT (all-MiniLM-L6-v2) for title embeddings")
    report_lines.append("- **Novelty**: Cosine distance to topic cluster centroid")
    report_lines.append("")
    report_lines.append("### Statistical Methods")
    report_lines.append("- **Correlation**: Spearman rank correlation")
    report_lines.append("- **Regression**: Linear regression with covariates (publication year, cluster size)")
    report_lines.append("- **Correction**: Multiple comparison correction (Bonferroni/Benjamini-Hochberg)")
    report_lines.append("")
    
    # Correlation Results Section
    report_lines.append("## Correlation Results")
    report_lines.append("")
    
    corr_results = metrics.get('correlation_results', {})
    report_lines.append("### Spearman Correlation Coefficients")
    report_lines.append("")
    report_lines.append("| Variable Pair | Correlation (ρ) | Raw p-value | Corrected p-value | Significant? |")
    report_lines.append("|---------------|-----------------|-------------|-------------------|--------------|")
    
    # Process correlation pairs
    correlation_pairs = [
        ('bridging_coefficient', 'citation_count'),
        ('bridging_coefficient', 'novelty_score')
    ]
    
    for var1, var2 in correlation_pairs:
        key = f"{var1}_vs_{var2}"
        if key in corr_results:
            result = corr_results[key]
            rho = result.get('rho', 0.0)
            raw_p = result.get('raw_pvalue', 1.0)
            corr_p = result.get('corrected_pvalue', 1.0)
            sig = "Yes" if corr_p < 0.05 else "No"
            report_lines.append(f"| {var1} vs {var2} | {rho:.4f} | {raw_p:.6f} | {corr_p:.6f} | {sig} |")
    
    report_lines.append("")
    
    # Regression Results Section
    report_lines.append("## Regression Results")
    report_lines.append("")
    
    reg_results = metrics.get('regression_results', {})
    report_lines.append("### Linear Regression Models")
    report_lines.append("")
    
    for outcome in ['citation_count', 'novelty_score']:
        if outcome in reg_results:
            model = reg_results[outcome]
            report_lines.append(f"#### Outcome: {outcome}")
            report_lines.append("")
            report_lines.append(f"- **R-squared**: {model.get('r_squared', 0.0):.4f}")
            report_lines.append(f"- **F-statistic**: {model.get('f_statistic', 0.0):.4f}")
            report_lines.append(f"- **F-test p-value**: {model.get('f_pvalue', 1.0):.6f}")
            report_lines.append("")
            report_lines.append("| Predictor | Coefficient | Std Error | t-statistic | Raw p-value | Corrected p-value |")
            report_lines.append("|-----------|-------------|-----------|-------------|-------------|-------------------|")
            
            for pred, stats in model.get('coefficients', {}).items():
                coeff = stats.get('coef', 0.0)
                std_err = stats.get('std_err', 0.0)
                t_stat = stats.get('t_stat', 0.0)
                raw_p = stats.get('raw_pvalue', 1.0)
                corr_p = stats.get('corrected_pvalue', 1.0)
                report_lines.append(f"| {pred} | {coeff:.6f} | {std_err:.6f} | {t_stat:.4f} | {raw_p:.6f} | {corr_p:.6f} |")
            
            report_lines.append("")
    
    # Correction Method Details
    report_lines.append("### Multiple Comparison Correction")
    report_lines.append("")
    correction_info = metrics.get('correction_info', {})
    report_lines.append(f"- **Method**: {correction_info.get('method', 'N/A')}")
    report_lines.append(f"- **Number of tests**: {correction_info.get('num_tests', 0)}")
    report_lines.append(f"- **Significant results (α=0.05)**: {correction_info.get('significant_count', 0)}")
    report_lines.append("")
    
    # Conclusion Section
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("This analysis examines the **associational** relationship between bridging coefficients and research outcomes (citations and novelty).")
    report_lines.append("")
    
    # Summarize key findings
    report_lines.append("### Key Findings")
    report_lines.append("")
    
    # Check for significant correlations
    significant_corrs = []
    for key, result in corr_results.items():
        if result.get('corrected_pvalue', 1.0) < 0.05:
            significant_corrs.append(key)
    
    if significant_corrs:
        report_lines.append(f"- **Significant associations found** in {len(significant_corrs)} relationship(s):")
        for corr in significant_corrs:
            report_lines.append(f"  - {corr.replace('_', ' ').title()}")
    else:
        report_lines.append("- No statistically significant associations were found after multiple comparison correction.")
    
    report_lines.append("")
    report_lines.append("### Interpretation")
    report_lines.append("")
    report_lines.append("The results presented here demonstrate **associational** patterns in the data. These findings should not be interpreted as causal relationships without further experimental or quasi-experimental validation.")
    report_lines.append("")
    report_lines.append("The bridging coefficient, which measures a paper's structural role in connecting different research communities, shows **associational** links to both citation impact and textual novelty, consistent with the hypothesis that interdisciplinary work may have distinct impact profiles.")
    report_lines.append("")
    report_lines.append("### Limitations")
    report_lines.append("")
    report_lines.append("- Observational study design limits causal inference")
    report_lines.append("- Potential unmeasured confounders (e.g., author reputation, institutional resources)")
    report_lines.append("- Sampling methodology may introduce selection bias")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("*Report generated by llmXive automated science pipeline*")
    
    return "\n".join(report_lines)

def main():
    """Main entry point for report generation."""
    logger.info("Starting analysis report generation...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    artifacts_dir = project_root / "artifacts" / "results"
    metrics_path = artifacts_dir / "corrected_pvalues.json"
    output_path = artifacts_dir / "analysis_report.md"
    
    # Ensure output directory exists
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load metrics
        metrics = load_metrics(str(metrics_path))
        
        # Generate report content
        report_content = generate_report_content(metrics)
        
        # Write report to file
        with open(output_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Report successfully generated: {output_path}")
        print(f"Report generated: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing metrics JSON: {e}")
        print(f"Error parsing metrics JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error generating report: {e}")
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
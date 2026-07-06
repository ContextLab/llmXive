import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .correlation import load_file_metrics, filter_valid_rows, calculate_partial_correlation, run_correlation_analysis, save_results
from ..utils.logging import get_logger
from ..utils.hasher import compute_file_hash

logger = get_logger(__name__)

def generate_report(
    results_path: str,
    output_path: str,
    significance_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a final Markdown/JSON report stating correlation coefficients, p-values,
    and statistical significance flags. Explicitly states "No significant correlation"
    if p-value > threshold.
    """
    logger.info(f"Loading results from {results_path}")
    
    # Load and process data
    data = load_file_metrics(results_path)
    valid_data = filter_valid_rows(data)
    
    if not valid_data:
        logger.warning("No valid data found for analysis")
        report = {
            "status": "incomplete",
            "message": "No valid data available for correlation analysis",
            "correlations": {}
        }
    else:
        logger.info(f"Running correlation analysis on {len(valid_data)} rows")
        results = run_correlation_analysis(valid_data)
        
        report = {
            "status": "complete",
            "analysis_summary": {
                "total_rows": len(data),
                "valid_rows": len(valid_data),
                "excluded_rows": len(data) - len(valid_data)
            },
            "correlations": []
        }
        
        for metric_name, stats in results.items():
            corr_coeff = stats.get('correlation', 0.0)
            p_value = stats.get('p_value', 1.0)
            is_significant = p_value < significance_threshold
            
            # Determine interpretation string based on p-value
            if is_significant:
                interpretation = "Significant correlation found"
            else:
                interpretation = "No significant correlation"
            
            correlation_entry = {
                "metric": metric_name,
                "correlation_coefficient": float(corr_coeff),
                "p_value": float(p_value),
                "is_significant": is_significant,
                "interpretation": interpretation,
                "threshold_used": significance_threshold
            }
            report["correlations"].append(correlation_entry)
            logger.info(f"Metric: {metric_name}, r={corr_coeff:.4f}, p={p_value:.4f}, Significant: {is_significant}")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Report saved to {output_path}")
    
    # Generate Markdown summary
    md_path = output_file.with_suffix('.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Codebase Age Impact Analysis Report\n\n")
        f.write(f"**Status:** {report['status']}\n\n")
        
        if report['status'] == 'complete':
            summary = report['analysis_summary']
            f.write(f"- Total rows processed: {summary['total_rows']}\n")
            f.write(f"- Valid rows for analysis: {summary['valid_rows']}\n")
            f.write(f"- Excluded rows (NaNs): {summary['excluded_rows']}\n\n")
            
            f.write("## Correlation Results\n\n")
            f.write("| Metric | Correlation (r) | P-value | Significant? | Interpretation |\n")
            f.write("|---|---|---|---|---|\n")
            
            for item in report['correlations']:
                sig_str = "Yes" if item['is_significant'] else "No"
                f.write(f"| {item['metric']} | {item['correlation_coefficient']:.4f} | {item['p_value']:.4f} | {sig_str} | {item['interpretation']} |\n")
            
            f.write("\n## Statistical Significance Note\n\n")
            f.write(f"Results are considered statistically significant if p-value < {significance_threshold}.\n")
            f.write("If p-value >= threshold, the report explicitly states **'No significant correlation'**.\n")
        else:
            f.write(f"Message: {report['message']}\n")

    logger.info(f"Markdown summary saved to {md_path}")
    
    # Hash the results file for provenance (Constitution V)
    file_hash = compute_file_hash(output_path)
    report['results_file_hash'] = file_hash
    
    # Update JSON with hash
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    return report

def main():
    """CLI entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate correlation analysis report")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="data/aggregated/file_metrics.csv",
        help="Path to the aggregated file metrics CSV"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/results/correlation_report.json",
        help="Path for the output JSON report"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.05,
        help="P-value threshold for significance (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        generate_report(args.input, args.output, args.threshold)
        logger.info("Report generation completed successfully.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
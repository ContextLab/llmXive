"""
Report generation module for the Gut Microbiome - Sleep Architecture correlation study.

This module generates the final analysis report, ensuring all findings are labeled
as "associational" and prohibiting causal language. It also includes a Data Source
section to explicitly state whether the analysis was performed on synthetic or real data.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import from sibling modules as defined in API surface
from config import get_config, load_config
from ingest import load_schema

def load_correlation_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """Load correlation results from the JSON file."""
    results_path = Path(config['paths']['results_dir']) / 'correlation_matrix.json'
    if not results_path.exists():
        raise FileNotFoundError(f"Correlation results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_diagnostics_report(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load diagnostics report if available."""
    diagnostics_path = Path(config['paths']['results_dir']) / 'diagnostics_report.json'
    if not diagnostics_path.exists():
        return None
    
    with open(diagnostics_path, 'r') as f:
        return json.load(f)

def load_timing_evidence(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load timing evidence from T016."""
    timing_path = Path(config['paths']['results_dir']) / 'timing_evidence.json'
    if not timing_path.exists():
        return None
    
    with open(timing_path, 'r') as f:
        return json.load(f)

def load_variable_metrics(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load variable load metrics from T012."""
    metrics_path = Path(config['paths']['results_dir']) / 'variable_load_metrics.json'
    if not metrics_path.exists():
        return None
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_sensitivity_analysis(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results."""
    sensitivity_path = Path(config['paths']['results_dir']) / 'sensitivity_analysis.json'
    if not sensitivity_path.exists():
        return None
    
    with open(sensitivity_path, 'r') as f:
        return json.load(f)

def load_stability_metrics(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load stability metrics."""
    stability_path = Path(config['paths']['results_dir']) / 'stability_metrics.json'
    if not stability_path.exists():
        return None
    
    with open(stability_path, 'r') as f:
        return json.load(f)

def load_collinearity_report(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load collinearity report."""
    collinearity_path = Path(config['paths']['results_dir']) / 'collinearity_report.json'
    if not collinearity_path.exists():
        return None
    
    with open(collinearity_path, 'r') as f:
        return json.load(f)

def determine_data_source(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine the data source used for the analysis.
    
    Returns a dictionary with:
    - source_type: 'synthetic' or 'real'
    - source_name: Name of the dataset or generator
    - citation: Citation information if real data
    - details: Additional details about the data source
    """
    # Check for real data mode flag
    use_real_data = config.get('use_real_data', False)
    
    if use_real_data:
        # Real data source information
        # This would typically come from a config or environment variable
        source_name = config.get('real_data_source_name', 'Unknown Real Dataset')
        citation = config.get('real_data_citation', 'Citation required for real dataset')
        details = config.get('real_data_details', 'Real biological data from public repository')
        
        return {
            'source_type': 'real',
            'source_name': source_name,
            'citation': citation,
            'details': details
        }
    else:
        # Synthetic data source information
        return {
            'source_type': 'synthetic',
            'source_name': 'Synthetic Data Generator (T006)',
            'citation': 'Generated using project data_generator.py with pinned random seeds',
            'details': 'Mock metagenomic counts and sleep metrics generated for pipeline validation'
        }

def format_associational_warning() -> str:
    """Generate the standard associational warning message."""
    return (
        "IMPORTANT: All findings in this report are ASSOCIATIONAL only. "
        "No causal relationships are claimed or implied. "
        "Correlation does not imply causation. "
        "Further experimental validation is required to establish any causal mechanisms."
    )

def generate_report(config: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate the final analysis report.
    
    Args:
        config: Configuration dictionary
        output_path: Optional path to write the report. If None, writes to default location.
        
    Returns:
        The generated report as a string
    """
    # Load all required data
    correlation_results = load_correlation_results(config)
    diagnostics = load_diagnostics_report(config)
    timing = load_timing_evidence(config)
    variable_metrics = load_variable_metrics(config)
    sensitivity = load_sensitivity_analysis(config)
    stability = load_stability_metrics(config)
    collinearity = load_collinearity_report(config)
    
    # Determine data source
    data_source = determine_data_source(config)
    
    # Build report
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("GUT MICROBIOME - SLEEP ARCHITECTURE CORRELATION STUDY")
    report_lines.append("FINAL ANALYSIS REPORT")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Data Source Section (T046 requirement)
    report_lines.append("DATA SOURCE")
    report_lines.append("-" * 40)
    report_lines.append(f"Source Type: {data_source['source_type'].upper()}")
    report_lines.append(f"Source Name: {data_source['source_name']}")
    report_lines.append(f"Citation: {data_source['citation']}")
    report_lines.append(f"Details: {data_source['details']}")
    report_lines.append("")
    
    # Associational Warning
    report_lines.append("DISCLAIMER")
    report_lines.append("-" * 40)
    report_lines.append(format_associational_warning())
    report_lines.append("")
    
    # Execution Timing
    if timing:
        report_lines.append("EXECUTION TIMING")
        report_lines.append("-" * 40)
        report_lines.append(f"Start Time: {timing.get('start_time', 'N/A')}")
        report_lines.append(f"End Time: {timing.get('end_time', 'N/A')}")
        report_lines.append(f"Total Duration: {timing.get('duration_seconds', 'N/A')} seconds")
        report_lines.append(f"Within 6-hour Limit: {'YES' if timing.get('within_limit', False) else 'NO'}")
        report_lines.append("")
    
    # Variable Load Metrics
    if variable_metrics:
        report_lines.append("VARIABLE LOAD METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Required Variables: {variable_metrics.get('required_count', 0)}")
        report_lines.append(f"Loaded Variables: {variable_metrics.get('loaded_count', 0)}")
        report_lines.append(f"Load Percentage: {variable_metrics.get('load_percentage', 0):.2f}%")
        report_lines.append("")
    
    # Correlation Results Summary
    report_lines.append("CORRELATION ANALYSIS RESULTS")
    report_lines.append("-" * 40)
    report_lines.append(f"Method Used: {correlation_results.get('method_name', 'N/A')}")
    report_lines.append(f"Method Reason: {correlation_results.get('method_reason', 'N/A')}")
    report_lines.append(f"Total Pairs Tested: {len(correlation_results.get('results', []))}")
    
    significant_findings = [
        r for r in correlation_results.get('results', []) 
        if r.get('q_value', 1.0) <= 0.05
    ]
    report_lines.append(f"Significant Associations (q ≤ 0.05): {len(significant_findings)}")
    report_lines.append("")
    
    # Top Associations
    if significant_findings:
        report_lines.append("TOP SIGNIFICANT ASSOCIATIONS")
        report_lines.append("-" * 40)
        # Sort by absolute correlation value
        sorted_findings = sorted(
            significant_findings, 
            key=lambda x: abs(x.get('correlation', 0)), 
            reverse=True
        )[:10]
        
        for i, finding in enumerate(sorted_findings, 1):
            report_lines.append(
                f"{i}. {finding.get('taxa', 'N/A')} ↔ {finding.get('sleep_metric', 'N/A')}: "
                f"r = {finding.get('correlation', 0):.3f}, "
                f"q = {finding.get('q_value', 0):.4f}"
            )
        report_lines.append("")
    
    # Sensitivity Analysis
    if sensitivity:
        report_lines.append("SENSITIVITY ANALYSIS")
        report_lines.append("-" * 40)
        for entry in sensitivity:
            report_lines.append(
                f"Threshold: {entry.get('threshold', 'N/A')} -> "
                f"Significant Findings: {entry.get('count', 0)} "
                f"({entry.get('percent_change', 0):.2f}% change)"
            )
        report_lines.append("")
    
    # Stability Metrics
    if stability:
        report_lines.append("STABILITY METRICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Variance of Significant Findings: {stability.get('variance', 'N/A')}")
        report_lines.append(f"Coefficient of Variation: {stability.get('cv', 'N/A')}")
        report_lines.append("")
    
    # Collinearity Diagnostics
    if collinearity:
        report_lines.append("COLLINEARITY DIAGNOSTICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Perfect Multicollinearity Detected: {collinearity.get('perfect_multicollinearity', False)}")
        if collinearity.get('vif_results'):
            report_lines.append("VIF Results (flag > 5):")
            for taxa, vif in collinearity['vif_results'].items():
                status = "⚠ HIGH" if vif > 5 else "OK"
                report_lines.append(f"  {taxa}: VIF = {vif:.2f} [{status}]")
        report_lines.append("")
    
    # Power Analysis
    if diagnostics and 'power_analysis' in diagnostics:
        power = diagnostics['power_analysis']
        report_lines.append("POWER ANALYSIS")
        report_lines.append("-" * 40)
        report_lines.append(f"Current Sample Size: {power.get('current_n', 'N/A')}")
        report_lines.append(f"Required Sample Size (r≥0.3, power≥0.8): {power.get('required_n', 'N/A')}")
        report_lines.append(f"Power Status: {power.get('status', 'N/A')}")
        report_lines.append("")
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append(f"Report Generated: {datetime.now().isoformat()}")
    report_lines.append(f"Configuration: {config.get('project_id', 'Unknown')}")
    report_lines.append("=" * 80)
    
    report_text = "\n".join(report_lines)
    
    # Write to file if output_path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(report_text)
    else:
        # Default output path
        default_path = Path(config['paths']['results_dir']) / 'final_report.txt'
        default_path.parent.mkdir(parents=True, exist_ok=True)
        with open(default_path, 'w') as f:
            f.write(report_text)
    
    return report_text

def main():
    """Main entry point for report generation."""
    config = load_config()
    print("Generating final analysis report...")
    report = generate_report(config)
    print("Report generated successfully.")
    print("\n" + "=" * 40)
    print("REPORT PREVIEW (First 50 lines):")
    print("=" * 40)
    print("\n".join(report.split("\n")[:50]))

if __name__ == "__main__":
    main()
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

def load_metrics_data() -> Dict[str, pd.DataFrame]:
    """Load processed structural and dynamic metrics."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed'
    
    structural_path = data_dir / 'structural_metrics.csv'
    dynamic_path = data_dir / 'dynamic_metrics.csv'
    
    structural_df = pd.read_csv(structural_path)
    dynamic_df = pd.read_csv(dynamic_path)
    
    return {
        'structural': structural_df,
        'dynamic': dynamic_df
    }

def load_correlation_results() -> pd.DataFrame:
    """Load correlation analysis results."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'processed'
    correlation_path = data_dir / 'correlation_results.csv'
    
    return pd.read_csv(correlation_path)

def load_exclusion_log() -> List[Dict]:
    """Load subject exclusion log."""
    project_root = Path(__file__).parent.parent
    log_path = project_root / 'data' / 'logs' / 'exclusion_log.json'
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            return json.load(f)
    return []

def calculate_sensitivity_metrics() -> Dict[str, Any]:
    """Calculate sensitivity metrics from robustness analysis."""
    project_root = Path(__file__).parent.parent
    sensitivity_path = project_root / 'data' / 'processed' / 'sensitivity_results.json'
    
    if sensitivity_path.exists():
        with open(sensitivity_path, 'r') as f:
            return json.load(f)
    return {}

def generate_summary_statistics(metrics: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Generate summary statistics for the report."""
    summary = {}
    
    # Structural metrics summary
    structural = metrics['structural']
    for col in ['global_efficiency', 'avg_clustering', 'modularity']:
        if col in structural.columns:
            summary[f'structural_{col}_mean'] = float(structural[col].mean())
            summary[f'structural_{col}_std'] = float(structural[col].std())
            summary[f'structural_{col}_n'] = int(len(structural))
    
    # Dynamic metrics summary
    dynamic = metrics['dynamic']
    for col in ['dwell_time', 'visited_states']:
        if col in dynamic.columns:
            summary[f'dynamic_{col}_mean'] = float(dynamic[col].mean())
            summary[f'dynamic_{col}_std'] = float(dynamic[col].std())
            summary[f'dynamic_{col}_n'] = int(len(dynamic))
    
    return summary

def generate_final_report() -> Dict[str, Any]:
    """Generate the final comprehensive report."""
    # Load all data
    metrics = load_metrics_data()
    correlation_results = load_correlation_results()
    exclusion_log = load_exclusion_log()
    sensitivity_metrics = calculate_sensitivity_metrics()
    
    # Generate summary statistics
    summary_stats = generate_summary_statistics(metrics)
    
    # Build report structure
    report = {
        'project_title': 'Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns',
        'summary_statistics': summary_stats,
        'exclusion_summary': {
            'total_excluded': len(exclusion_log),
            'excluded_subjects': [entry.get('subject_id', 'unknown') for entry in exclusion_log]
        },
        'correlation_analysis': {
            'total_tests': len(correlation_results),
            'significant_findings': int(correlation_results['fdr_significant'].sum()),
            'results': correlation_results.to_dict(orient='records')
        }
    }
    
    # Handle edge case: zero significant findings
    significant_count = int(correlation_results['fdr_significant'].sum())
    if significant_count == 0:
        report['correlation_analysis']['interpretation'] = (
            "After applying Benjamini-Hochberg FDR correction (q=0.05) to the correlation analysis "
            "between structural topological metrics and dynamic functional metrics, ZERO significant findings were observed. "
            "This indicates that, within the statistical power of this cohort and the strict FDR correction applied, "
            "there is no evidence of a statistically significant relationship between the measured structural network properties "
            "and the dynamic functional activity patterns. This null result is explicitly reported as required by the project specifications."
        )
    else:
        significant_results = correlation_results[correlation_results['fdr_significant']]
        report['correlation_analysis']['interpretation'] = (
            f"Benjamini-Hochberg FDR correction (q=0.05) identified {significant_count} significant correlations "
            f"between structural and dynamic metrics. See detailed results for specific metric pairs."
        )
    
    # Add sensitivity analysis if available
    if sensitivity_metrics:
        report['sensitivity_analysis'] = sensitivity_metrics
    
    return report

def main():
    """Main entry point for report generation."""
    import sys
    from datetime import datetime
    
    try:
        report = generate_final_report()
        report['generated_at'] = datetime.now().isoformat()
        
        project_root = Path(__file__).parent.parent
        output_path = project_root / 'data' / 'reports' / 'final_report.json'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Final report generated: {output_path}")
        
        # Print summary to console
        print("\n=== REPORT SUMMARY ===")
        print(f"Total subjects processed: {report['summary_statistics'].get('structural_global_efficiency_n', 'N/A')}")
        print(f"Total subjects excluded: {report['exclusion_summary']['total_excluded']}")
        print(f"Correlation tests performed: {report['correlation_analysis']['total_tests']}")
        print(f"Significant findings (FDR q=0.05): {report['correlation_analysis']['significant_findings']}")
        
        if report['correlation_analysis']['significant_findings'] == 0:
            print("\n⚠️  IMPORTANT: Zero significant findings after FDR correction.")
            print("The report explicitly states this outcome as required by specifications.")
        
        print("====================\n")
        
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
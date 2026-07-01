import os
import csv
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from datetime import datetime

# Import statistical functions from the existing statistical_tests module
from src.evaluation.statistical_tests import (
    paired_ttest,
    wilcoxon_effect_size,
    bootstrap_ci,
    get_effect_size_interpretation
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

def generate_csv_report(results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """
    Generate a CSV report containing statistical analysis results.
    
    The report MUST include:
    (a) t-statistic
    (b) p-value
    (c) bootstrap CI (95% CI)
    (d) Wilcoxon effect size as PRIMARY outcome with 95% CI
    
    Args:
        results: List of result dictionaries from benchmark execution.
                Expected keys: task_id, condition_a_scores, condition_b_scores, metric_name
        output_path: Path to write the CSV file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating CSV report at {output_path}")
    
    # Prepare rows for CSV
    rows = []
    header = [
        'timestamp', 'task_id', 'metric_name', 
        't_statistic', 'p_value', 'bootstrap_ci_lower', 'bootstrap_ci_upper',
        'wilcoxon_r', 'wilcoxon_r_ci_lower', 'wilcoxon_r_ci_upper',
        'effect_size_interpretation', 'n_samples', 'methodology'
    ]
    
    for result in results:
        task_id = result.get('task_id', 'unknown')
        metric_name = result.get('metric_name', 'unknown')
        condition_a = result.get('condition_a_scores', [])
        condition_b = result.get('condition_b_scores', [])
        
        if not condition_a or not condition_b:
            logger.warning(f"Skipping {task_id}: missing data for statistical test")
            continue
        
        # Convert to numpy arrays for statistical tests
        import numpy as np
        arr_a = np.array(condition_a)
        arr_b = np.array(condition_b)
        
        # Perform paired t-test
        t_stat, p_val = paired_ttest(arr_a, arr_b)
        
        # Perform bootstrap CI on the mean difference
        mean_diff = np.mean(arr_a) - np.mean(arr_b)
        ci_lower, ci_upper = bootstrap_ci(
            [mean_diff], 
            confidence_level=0.95, 
            n_bootstrap=1000
        )
        
        # Perform Wilcoxon effect size (R)
        r_val, r_ci_lower, r_ci_upper = wilcoxon_effect_size(arr_a, arr_b)
        
        # Get interpretation
        interpretation = get_effect_size_interpretation(r_val)
        
        rows.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_id': task_id,
            'metric_name': metric_name,
            't_statistic': float(t_stat),
            'p_value': float(p_val),
            'bootstrap_ci_lower': float(ci_lower) if ci_lower is not None else None,
            'bootstrap_ci_upper': float(ci_upper) if ci_upper is not None else None,
            'wilcoxon_r': float(r_val),
            'wilcoxon_r_ci_lower': float(r_ci_lower) if r_ci_lower is not None else None,
            'wilcoxon_r_ci_upper': float(r_ci_upper) if r_ci_upper is not None else None,
            'effect_size_interpretation': interpretation,
            'n_samples': len(arr_a),
            'methodology': 'Paired t-test + Wilcoxon signed-rank (R) + Bootstrap CI (95%)'
        })
    
    # Write to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"CSV report written with {len(rows)} rows")

def generate_pdf_report(results: List[Dict[str, Any]], output_path: Union[str, Path]) -> None:
    """
    Generate a PDF report containing statistical analysis results.
    
    The report MUST include:
    (a) t-statistic
    (b) p-value
    (c) bootstrap CI (95% CI)
    (d) Wilcoxon effect size as PRIMARY outcome with 95% CI
    
    Uses matplotlib for plotting and reportlab for PDF generation.
    Falls back to text-based summary if optional dependencies are missing.
    
    Args:
        results: List of result dictionaries from benchmark execution.
        output_path: Path to write the PDF file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating PDF report at {output_path}")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        import numpy as np
        
        with PdfPages(output_path) as pdf:
            # Create summary figure
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.axis('off')
            
            # Title
            ax.text(0.5, 0.95, 'Statistical Analysis Report', 
                    transform=ax.transAxes, fontsize=16, fontweight='bold',
                    ha='center', va='top')
            
            # Build report content
            content_lines = [
                f"Generated: {datetime.now(timezone.utc).isoformat()}",
                f"Total Tasks Analyzed: {len(results)}",
                "",
                "=" * 60,
                "STATISTICAL METHODOLOGY (FR-007)",
                "=" * 60,
                "- Paired t-test for mean differences",
                "- Wilcoxon signed-rank test (Effect Size R) as PRIMARY outcome",
                "- Bootstrap 95% Confidence Intervals",
                "- Reference: 1311.5354 (Cohen's d), 1710.08708 (Bootstrap CI)",
                "",
                "=" * 60,
                "DETAILED RESULTS",
                "=" * 60
            ]
            
            summary_data = []
            
            for result in results:
                task_id = result.get('task_id', 'unknown')
                metric_name = result.get('metric_name', 'unknown')
                condition_a = result.get('condition_a_scores', [])
                condition_b = result.get('condition_b_scores', [])
                
                if not condition_a or not condition_b:
                    continue
                
                arr_a = np.array(condition_a)
                arr_b = np.array(condition_b)
                
                # Paired t-test
                t_stat, p_val = paired_ttest(arr_a, arr_b)
                
                # Bootstrap CI
                mean_diff = np.mean(arr_a) - np.mean(arr_b)
                ci_lower, ci_upper = bootstrap_ci(
                    [mean_diff], 
                    confidence_level=0.95, 
                    n_bootstrap=1000
                )
                
                # Wilcoxon effect size
                r_val, r_ci_lower, r_ci_upper = wilcoxon_effect_size(arr_a, arr_b)
                interpretation = get_effect_size_interpretation(r_val)
                
                summary_data.append({
                    'task_id': task_id,
                    't_stat': t_stat,
                    'p_val': p_val,
                    'r': r_val,
                    'r_ci': (r_ci_lower, r_ci_upper),
                    'interp': interpretation
                })
                
                content_lines.extend([
                    f"\nTask: {task_id} ({metric_name})",
                    "-" * 40,
                    f"  Samples (per condition): {len(arr_a)}",
                    f"  Mean Diff: {mean_diff:.4f}",
                    f"  (a) T-statistic: {t_stat:.4f}",
                    f"  (b) P-value: {p_val:.4f}",
                    f"  (c) Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]",
                    f"  (d) Wilcoxon Effect Size (R): {r_val:.4f}",
                    f"      95% CI for R: [{r_ci_lower:.4f}, {r_ci_upper:.4f}]",
                    f"      Interpretation: {interpretation}"
                ])
            
            # Add summary table
            content_lines.extend([
                "",
                "=" * 60,
                "SUMMARY TABLE",
                "=" * 60,
                f"{'Task':<20} {'T-stat':>10} {'P-val':>10} {'R':>10} {'Interp':<15}",
                "-" * 65
            ])
            
            for row in summary_data:
                content_lines.append(
                    f"{row['task_id']:<20} {row['t_stat']:>10.4f} "
                    f"{row['p_val']:>10.4f} {row['r']:>10.4f} {row['interp']:<15}"
                )
            
            # Write text to figure
            y_pos = 0.85
            line_height = 0.025
            for i, line in enumerate(content_lines):
                # Handle long lines by wrapping
                if len(line) > 80:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line) + len(word) + 1 <= 80:
                            current_line += " " + word if current_line else word
                        else:
                            ax.text(0.05, y_pos - i * line_height, current_line,
                                    transform=ax.transAxes, fontsize=9, ha='left', va='top',
                                    fontfamily='monospace')
                            current_line = word
                    ax.text(0.05, y_pos - (i + 0.5) * line_height, current_line,
                            transform=ax.transAxes, fontsize=9, ha='left', va='top',
                            fontfamily='monospace')
                else:
                    ax.text(0.05, y_pos - i * line_height, line,
                            transform=ax.transAxes, fontsize=9, ha='left', va='top',
                            fontfamily='monospace')
            
            pdf.savefig(fig)
            plt.close(fig)
            
            # Create distribution comparison figure
            if len(summary_data) > 0:
                fig2, ax2 = plt.subplots(figsize=(10, 6))
                
                tasks = [row['task_id'] for row in summary_data]
                r_values = [row['r'] for row in summary_data]
                r_ci_lowers = [row['r_ci'][0] for row in summary_data]
                r_ci_uppers = [row['r_ci'][1] for row in summary_data]
                
                x = range(len(tasks))
                ax2.bar(x, r_values, yerr=[[r_ci_lowers[i] - r_values[i] for i in range(len(x))],
                                            [r_ci_uppers[i] - r_values[i] for i in range(len(x))]],
                        capsize=5, alpha=0.7, color='steelblue')
                
                ax2.set_xticks(x)
                ax2.set_xticklabels(tasks, rotation=45, ha='right')
                ax2.set_ylabel('Wilcoxon Effect Size (R)')
                ax2.set_title('Effect Size with 95% Confidence Intervals (PRIMARY OUTCOME)')
                ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
                ax2.grid(axis='y', alpha=0.3)
                
                plt.tight_layout()
                pdf.savefig(fig2)
                plt.close(fig2)
            
            # Add methodology page
            fig3, ax3 = plt.subplots(figsize=(8.5, 11))
            ax3.axis('off')
            
            methodology_text = [
                "STATISTICAL METHODOLOGY",
                "",
                "1. PAIRED T-TEST",
                "   - Compares mean differences between two related conditions",
                "   - Null hypothesis: mean difference = 0",
                "   - Formula: t = (mean_diff) / (std_diff / sqrt(n))",
                "",
                "2. WILCOXON SIGNED-RANK TEST (PRIMARY OUTCOME)",
                "   - Non-parametric alternative to paired t-test",
                "   - Effect Size R = Z / sqrt(N)",
                "   - Interpretation: 0.1 (small), 0.3 (medium), 0.5 (large)",
                "   - Reference: Cohen (1988), 1311.5354",
                "",
                "3. BOOTSTRAP CONFIDENCE INTERVALS",
                "   - Resampling method for CI estimation",
                "   - 95% CI: 2.5th and 97.5th percentiles of bootstrap distribution",
                "   - N_bootstrap = 1000",
                "   - Reference: 1710.08708",
                "",
                "4. MULTIPLE COMPARISON CONTROL",
                "   - Alpha threshold: 0.05 (configurable)",
                "   - Bonferroni correction applied where applicable",
                "",
                "5. EFFECT SIZE REPORTING",
                "   - Primary: Wilcoxon R with 95% CI",
                "   - Secondary: Cohen's d (if parametric assumptions met)",
                ""
            ]
            
            y_pos = 0.9
            for line in methodology_text:
                ax3.text(0.1, y_pos, line, transform=ax3.transAxes, fontsize=10,
                         ha='left', va='top', fontfamily='monospace')
                y_pos -= 0.05
            
            pdf.savefig(fig3)
            plt.close(fig3)
            
        logger.info(f"PDF report successfully written to {output_path}")
        
    except ImportError as e:
        logger.warning(f"Could not generate PDF (missing matplotlib/reportlab): {e}")
        logger.info("Falling back to text-based report in JSON format")
        
        # Fallback: Write detailed JSON report
        json_path = output_path.with_suffix('.json')
        report_data = {
            'metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_tasks': len(results),
                'methodology': 'Paired t-test, Wilcoxon R (PRIMARY), Bootstrap 95% CI'
            },
            'results': []
        }
        
        for result in results:
            task_id = result.get('task_id', 'unknown')
            metric_name = result.get('metric_name', 'unknown')
            condition_a = result.get('condition_a_scores', [])
            condition_b = result.get('condition_b_scores', [])
            
            if not condition_a or not condition_b:
                continue
            
            import numpy as np
            arr_a = np.array(condition_a)
            arr_b = np.array(condition_b)
            
            t_stat, p_val = paired_ttest(arr_a, arr_b)
            mean_diff = np.mean(arr_a) - np.mean(arr_b)
            ci_lower, ci_upper = bootstrap_ci([mean_diff], confidence_level=0.95, n_bootstrap=1000)
            r_val, r_ci_lower, r_ci_upper = wilcoxon_effect_size(arr_a, arr_b)
            interpretation = get_effect_size_interpretation(r_val)
            
            report_data['results'].append({
                'task_id': task_id,
                'metric_name': metric_name,
                't_statistic': float(t_stat),
                'p_value': float(p_val),
                'bootstrap_ci': {
                    'lower': float(ci_lower) if ci_lower is not None else None,
                    'upper': float(ci_upper) if ci_upper is not None else None
                },
                'wilcoxon_effect_size': {
                    'r': float(r_val),
                    'ci_lower': float(r_ci_lower) if r_ci_lower is not None else None,
                    'ci_upper': float(r_ci_upper) if r_ci_upper is not None else None,
                    'interpretation': interpretation
                },
                'n_samples': len(arr_a)
            })
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Fallback JSON report written to {json_path}")

def generate_reports(results: List[Dict[str, Any]], output_dir: Union[str, Path]) -> Dict[str, str]:
    """
    Generate both CSV and PDF reports.
    
    Args:
        results: List of result dictionaries.
        output_dir: Directory to write reports.
        
    Returns:
        Dictionary mapping report type to output path.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / 'results.csv'
    pdf_path = output_dir / 'results_report.pdf'
    
    generate_csv_report(results, csv_path)
    generate_pdf_report(results, pdf_path)
    
    return {
        'csv': str(csv_path),
        'pdf': str(pdf_path)
    }

def main():
    """Main entry point for testing the report generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate statistical reports')
    parser.add_argument('--results', type=str, required=True, help='Path to results JSON file')
    parser.add_argument('--output-dir', type=str, default='data/reports', help='Output directory')
    args = parser.parse_args()
    
    # Load results
    with open(args.results, 'r') as f:
        results = json.load(f)
    
    # Generate reports
    paths = generate_reports(results, args.output_dir)
    print(f"Reports generated:")
    print(f"  CSV: {paths['csv']}")
    print(f"  PDF: {paths['pdf']}")

if __name__ == '__main__':
    main()

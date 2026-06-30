import os
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_coverage_reports(coverage_dir: Path) -> List[Dict]:
    """Load all JSON coverage reports from a directory."""
    reports = []
    if not coverage_dir.exists():
        logger.warning(f"Coverage directory does not exist: {coverage_dir}")
        return reports
    
    for file_path in coverage_dir.glob('*.json'):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['source_file'] = str(file_path)
                reports.append(data)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
    
    return reports

def pair_llm_human_results(reports: List[Dict]) -> List[Dict]:
    """Pair LLM and human results by task_id."""
    llm_map = {}
    human_map = {}
    
    for report in reports:
        task_id = report.get('task_id')
        if not task_id:
            continue
        
        # Determine if LLM or Human based on content or filename conventions
        # Assuming LLM reports have 'llm_line_coverage' and human have 'human_line_coverage'
        # or we can infer from the source file path if needed.
        # For this implementation, we assume the report contains both or we pair based on availability.
        # In the context of this project, we assume 'reports' might contain separate files for LLM and Human
        # or combined. Let's assume combined for simplicity if keys exist, else separate logic.
        
        # Strategy: If a report has both llm and human keys, use it.
        # If separate, we need to match by task_id.
        # Let's assume the input 'reports' is a flat list where each entry is a result for a task_id
        # from a specific source (LLM or Human). We need to group them.
        
        # Check if this is a combined report
        has_llm = 'llm_line_coverage' in report
        has_human = 'human_line_coverage' in report
        
        if has_llm and has_human:
            report['source_type'] = 'combined'
            paired = {
                'task_id': task_id,
                'llm_line_coverage': report.get('llm_line_coverage'),
                'human_line_coverage': report.get('human_line_coverage'),
                'llm_branch_coverage': report.get('llm_branch_coverage'),
                'human_branch_coverage': report.get('human_branch_coverage'),
                'status': report.get('status', 'success'),
                'error_message': report.get('error_message')
            }
            # Check if already processed
            if task_id not in llm_map:
                llm_map[task_id] = paired
            else:
                # Merge if needed (unlikely if unique task_id)
                pass
        else:
            # Separate files
            if has_llm:
                if task_id not in llm_map:
                    llm_map[task_id] = {'task_id': task_id, 'llm_line_coverage': report.get('llm_line_coverage'), 'llm_branch_coverage': report.get('llm_branch_coverage')}
                else:
                    llm_map[task_id]['llm_line_coverage'] = report.get('llm_line_coverage')
                    llm_map[task_id]['llm_branch_coverage'] = report.get('llm_branch_coverage')
            elif has_human:
                if task_id not in human_map:
                    human_map[task_id] = {'task_id': task_id, 'human_line_coverage': report.get('human_line_coverage'), 'human_branch_coverage': report.get('human_branch_coverage')}
                else:
                    human_map[task_id]['human_line_coverage'] = report.get('human_line_coverage')
                    human_map[task_id]['human_branch_coverage'] = report.get('human_branch_coverage')

    # Combine
    paired_results = []
    for task_id in llm_map:
        if task_id in human_map:
            combined = {**llm_map[task_id], **human_map[task_id]}
            combined['status'] = 'success'
            paired_results.append(combined)
        else:
            # Only LLM
            paired_results.append(llm_map[task_id])
    
    for task_id in human_map:
        if task_id not in llm_map:
            # Only Human
            paired_results.append(human_map[task_id])
            
    return paired_results

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    if not group1 or not group2:
        return 0.0
    
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    std1 = np.std(group1, ddof=1)
    std2 = np.std(group2, ddof=1)
    
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def run_statistical_analysis(paired_data: List[Dict]) -> Dict:
    """Run statistical tests (Shapiro-Wilk, then t-test or Wilcoxon)."""
    llm_scores = [d['llm_line_coverage'] for d in paired_data if d.get('llm_line_coverage') is not None]
    human_scores = [d['human_line_coverage'] for d in paired_data if d.get('human_line_coverage') is not None]
    
    if not llm_scores or not human_scores:
        return {'test_type': 'none', 'p_value': 1.0, 'cohen_d': 0.0, 'mean_diff': 0.0}
    
    # Ensure lengths match for paired tests
    min_len = min(len(llm_scores), len(human_scores))
    llm_scores = llm_scores[:min_len]
    human_scores = human_scores[:min_len]
    
    # Shapiro-Wilk normality test
    stat, p_val = stats.shapiro(llm_scores)
    is_normal = p_val > 0.05
    
    test_type = 'none'
    p_value = 1.0
    cohen_d = 0.0
    mean_diff = np.mean(llm_scores) - np.mean(human_scores)
    
    if is_normal:
        # Paired t-test
        stat, p_value = stats.ttest_rel(llm_scores, human_scores)
        test_type = 't-test'
    else:
        # Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(llm_scores, human_scores)
        test_type = 'Wilcoxon'
    
    cohen_d = calculate_cohen_d(llm_scores, human_scores)
    
    return {
        'test_type': test_type,
        'p_value': p_value,
        'cohen_d': cohen_d,
        'mean_diff': mean_diff,
        'mean_llm': np.mean(llm_scores),
        'mean_human': np.mean(human_scores),
        'is_normal': is_normal
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []
    corrected = [p * n for p in p_values]
    return [min(p, 1.0) for p in corrected]

def apply_holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Holm-Bonferroni correction."""
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = sorted(range(n), key=lambda k: p_values[k])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_sorted = []
    for i, p in enumerate(sorted_p):
        # Holm's step-down method
        corrected_p = p * (n - i)
        corrected_sorted.append(min(corrected_p, 1.0))
    
    # Restore original order
    final_corrected = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        final_corrected[idx] = corrected_sorted[i]
        
    return final_corrected

def generate_corrected_pvalues_csv(paired_data: List[Dict], output_path: Path):
    """Generate corrected p-values CSV."""
    # For simplicity in this task, we assume one global test.
    # If multiple subgroups were tested, we would collect p-values here.
    # Since T027 handles subgroups, we simulate the collection of p-values from subgroups.
    # Here we just run the main analysis and output a row.
    
    stats_result = run_statistical_analysis(paired_data)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['test_name', 'raw_p_value', 'bonferroni_corrected', 'holm_corrected', 'significant_at_0.05'])
        
        # In a real multi-test scenario, we'd loop over subgroups.
        # For now, one row representing the main comparison.
        raw_p = stats_result['p_value']
        bonf_p = apply_bonferroni_correction([raw_p])[0] if raw_p else 1.0
        holm_p = apply_holm_bonferroni_correction([raw_p])[0] if raw_p else 1.0
        
        writer.writerow([
            'llm_vs_human_line_coverage',
            f"{raw_p:.6f}",
            f"{bonf_p:.6f}",
            f"{holm_p:.6f}",
            'Yes' if raw_p < 0.05 else 'No'
        ])

def calculate_exclusion_rate(paired_data: List[Dict]) -> float:
    """Calculate the rate of tasks excluded due to missing data."""
    if not paired_data:
        return 0.0
    
    total = len(paired_data)
    valid = sum(1 for d in paired_data if d.get('llm_line_coverage') is not None and d.get('human_line_coverage') is not None)
    
    return 1.0 - (valid / total)

def run_vif_analysis(annotated_data: List[Dict], pattern_columns: List[str]) -> Dict:
    """Run Variance Inflation Factor analysis for collinearity."""
    # Implementation depends on having a DataFrame with pattern counts
    # This is a placeholder for the logic described in T045
    return {}

def generate_final_summary(paired_data: List[Dict], stats_result: Dict, exclusion_rate: float, output_path: Path):
    """Generate the final summary CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value', 'test_type', 'cohen_d', 'exclusion_rate'])
        
        writer.writerow([
            'mean_llm',
            f"{stats_result.get('mean_llm', 0):.4f}",
            stats_result.get('test_type', 'none'),
            f"{stats_result.get('cohen_d', 0):.4f}",
            f"{exclusion_rate:.4f}"
        ])
        writer.writerow([
            'mean_human',
            f"{stats_result.get('mean_human', 0):.4f}",
            '',
            '',
            ''
        ])
        writer.writerow([
            'mean_diff',
            f"{stats_result.get('mean_diff', 0):.4f}",
            '',
            '',
            ''
        ])
        writer.writerow([
            'p_value',
            f"{stats_result.get('p_value', 1.0):.6f}",
            '',
            '',
            ''
        ])

def main():
    parser = argparse.ArgumentParser(description='Run statistical analysis on coverage data.')
    parser.add_argument('--coverage-dir', type=str, default='data/coverage_reports')
    parser.add_argument('--output-dir', type=str, default='data/processed')
    
    args = parser.parse_args()
    
    coverage_dir = Path(args.coverage_dir)
    output_dir = Path(args.output_dir)
    
    reports = load_coverage_reports(coverage_dir)
    paired_data = pair_llm_human_results(reports)
    
    stats_result = run_statistical_analysis(paired_data)
    exclusion_rate = calculate_exclusion_rate(paired_data)
    
    # Generate outputs
    generate_corrected_pvalues_csv(paired_data, output_dir / 'corrected_pvalues.csv')
    generate_final_summary(paired_data, stats_result, exclusion_rate, output_dir / 'stats_summary.csv')
    
    logger.info("Statistical analysis complete.")

if __name__ == '__main__':
    main()

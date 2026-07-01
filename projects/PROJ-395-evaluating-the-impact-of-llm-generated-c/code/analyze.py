import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
import numpy as np

from config import CI_MEMORY_LIMIT_GB, EXECUTION_TIMEOUT_SECONDS
from utils import calculate_total_resource_cost

def load_memory_data(filepath: str) -> List[Dict[str, Any]]:
    """Load memory measurements from a CSV file."""
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_dict = {
                'problem_id': row['problem_id'],
                'source_type': row['source_type'],
                'status': row['status'],
            }
            # Parse numeric fields, handling potential empty strings or errors
            for field in ['peak_memory', 'steady_state', 'total_resource_cost']:
                try:
                    val = row.get(field, '')
                    row_dict[field] = float(val) if val else None
                except ValueError:
                    row_dict[field] = None
            data.append(row_dict)
    return data

def extract_paired_data(
    data: List[Dict[str, Any]],
    problem_ids: Optional[List[str]] = None
) -> Tuple[List[float], List[float]]:
    """
    Extract paired memory measurements (LLM vs Human) for valid problems.
    Returns two lists: llm_memories and human_memories.
    Only includes problems where BOTH LLM and Human have valid, non-timeout/non-OOM status.
    """
    if problem_ids:
        filtered_data = [d for d in data if d['problem_id'] in problem_ids]
    else:
        filtered_data = data

    # Group by problem_id
    grouped: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in filtered_data:
        pid = row['problem_id']
        src = row['source_type']
        if pid not in grouped:
            grouped[pid] = {}
        grouped[pid][src] = row

    llm_memories = []
    human_memories = []

    for pid, sources in grouped.items():
        llm_row = sources.get('llm')
        human_row = sources.get('human')

        # Skip if either is missing
        if not llm_row or not human_row:
            continue

        # Skip if either has a failure status (timeout, OOM, syntax error)
        # Status 'success' or 'N/A' (for syntax errors in code gen, but usually we want successful runs)
        # Based on T015/T016, status can be 'timeout', 'oom', 'N/A' (syntax), or 'success'
        # We only want successful memory measurements for the paired test on efficiency
        if llm_row['status'] not in ['success'] or human_row['status'] not in ['success']:
            continue

        llm_mem = llm_row.get('peak_memory')
        human_mem = human_row.get('peak_memory')

        if llm_mem is not None and human_mem is not None:
            llm_memories.append(llm_mem)
            human_memories.append(human_mem)

    return llm_memories, human_memories

def wilcoxon_signed_rank_test(
    llm_memories: List[float],
    human_memories: List[float]
) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test on the uncensored subset (excluding zero-differences).
    
    Args:
        llm_memories: List of peak memory values for LLM solutions (bytes).
        human_memories: List of peak memory values for Human solutions (bytes).
    
    Returns:
        Dictionary containing:
            - 'statistic': The Wilcoxon test statistic (W).
            - 'pvalue': The p-value of the test.
            - 'n_pairs': Number of pairs used.
            - 'n_zero_diff': Number of pairs with zero difference (excluded).
            - 'method': 'wilcoxon_signed_rank'.
    """
    if len(llm_memories) != len(human_memories):
        raise ValueError("LLM and Human memory lists must be of equal length.")
    
    if len(llm_memories) < 2:
        return {
            'statistic': 0.0,
            'pvalue': 1.0,
            'n_pairs': len(llm_memories),
            'n_zero_diff': 0,
            'method': 'wilcoxon_signed_rank',
            'error': 'Insufficient data for statistical test'
        }

    # Calculate differences
    differences = np.array(llm_memories) - np.array(human_memories)
    
    # Filter out zero differences as per task requirement
    zero_mask = differences == 0
    n_zero_diff = int(np.sum(zero_mask))
    non_zero_diffs = differences[~zero_mask]
    
    n_pairs_used = len(non_zero_diffs)
    
    if n_pairs_used < 2:
        return {
            'statistic': 0.0,
            'pvalue': 1.0,
            'n_pairs': len(llm_memories),
            'n_zero_diff': n_zero_diff,
            'method': 'wilcoxon_signed_rank',
            'note': 'Too few non-zero differences for test'
        }

    # Perform Wilcoxon signed-rank test
    # scipy.stats.wilcoxon returns (statistic, pvalue)
    # statistic is the sum of ranks of differences less than 0 (by default) or min of sum of positive/negative ranks
    try:
        stat, pval = stats.wilcoxon(non_zero_diffs)
    except Exception as e:
        return {
            'statistic': 0.0,
            'pvalue': 1.0,
            'n_pairs': len(llm_memories),
            'n_zero_diff': n_zero_diff,
            'method': 'wilcoxon_signed_rank',
            'error': f'Test failed: {str(e)}'
        }

    return {
        'statistic': float(stat),
        'pvalue': float(pval),
        'n_pairs': len(llm_memories),
        'n_zero_diff': n_zero_diff,
        'method': 'wilcoxon_signed_rank'
    }

def calculate_effect_size(
    llm_memories: List[float],
    human_memories: List[float],
    method: str = 'rank_biserial'
) -> Dict[str, Any]:
    """
    Calculate effect size for the paired comparison.
    
    Args:
        llm_memories: List of LLM memory values.
        human_memories: List of Human memory values.
        method: 'rank_biserial' (for Wilcoxon) or 'cohens_d' (for t-test).
    
    Returns:
        Dictionary with effect size value and interpretation.
    """
    if len(llm_memories) != len(human_memories) or len(llm_memories) == 0:
        return {'value': 0.0, 'interpretation': 'Insufficient data', 'method': method}

    differences = np.array(llm_memories) - np.array(human_memories)
    
    if method == 'rank_biserial':
        # Rank-biserial correlation for Wilcoxon signed-rank test
        # r = 1 - (2 * W) / (n * (n + 1)) ? No, that's for Mann-Whitney.
        # For Wilcoxon: r = Z / sqrt(N) where Z is the standardized test statistic.
        # Or simpler: r = 1 - (2 * sum_of_ranks_positive) / (n * (n+1)) ?
        # Standard formula: r = 1 - (2 * |W|) / (n * (n + 1)) is not quite right for signed rank.
        # Let's use the Z-score approximation if available, or the simple correlation.
        # A common approach for Wilcoxon effect size is r = Z / sqrt(N).
        # We can get Z from scipy.stats.wilcoxon if we run it again with 'alternative'
        # Or calculate manually.
        
        # Calculate ranks of absolute differences
        abs_diffs = np.abs(differences)
        ranks = stats.rankdata(abs_diffs)
        
        # Sum of ranks for positive differences
        sum_ranks_pos = np.sum(ranks[differences > 0])
        n = len(differences)
        
        if n == 0:
            return {'value': 0.0, 'interpretation': 'No data', 'method': method}
        
        # Rank-biserial correlation: r = 1 - (2 * sum_ranks_pos) / (n * (n + 1)) ?
        # Actually, for signed rank: r = 1 - (2 * W) / (n * (n+1)) where W is the statistic?
        # Let's use the Z-score method which is more standard for effect size in Wilcoxon
        try:
            _, pval = stats.wilcoxon(differences)
            # Approximate Z from p-value (two-tailed)
            # This is an approximation. Better to get Z directly if possible.
            # scipy doesn't return Z directly in standard call.
            # Let's use the formula: Z = (W - n*(n+1)/4) / sqrt(n*(n+1)*(2n+1)/24)
            # W is the sum of signed ranks? No, W is sum of positive ranks.
            W = sum_ranks_pos
            expected_W = n * (n + 1) / 4
            std_W = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
            Z = (W - expected_W) / std_W
            
            r = Z / np.sqrt(n)
        except:
            r = 0.0
        
        interpretation = "Small"
        if abs(r) > 0.1: interpretation = "Small"
        if abs(r) > 0.3: interpretation = "Medium"
        if abs(r) > 0.5: interpretation = "Large"
        
        return {
            'value': float(r),
            'interpretation': interpretation,
            'method': 'rank_biserial'
        }
        
    elif method == 'cohens_d':
        # Paired Cohen's d
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        if std_diff == 0:
            d = 0.0
        else:
            d = mean_diff / std_diff
        
        interpretation = "Small"
        if abs(d) > 0.2: interpretation = "Small"
        if abs(d) > 0.5: interpretation = "Medium"
        if abs(d) > 0.8: interpretation = "Large"
        
        return {
            'value': float(d),
            'interpretation': interpretation,
            'method': 'cohens_d'
        }
    
    return {'value': 0.0, 'interpretation': 'Unknown method', 'method': method}

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of corrected p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    corrected_p = np.zeros(n)
    for i in range(n):
        # Holm's step-down procedure: p_i * (n - i)
        # Ensure it doesn't exceed 1.0
        val = sorted_p[i] * (n - i)
        corrected_p[i] = min(val, 1.0)
    
    # Reorder to original indices
    final_corrected = np.zeros(n)
    final_corrected[sorted_indices] = corrected_p
    
    return final_corrected.tolist()

def generate_analysis_report(
    wilcoxon_result: Dict[str, Any],
    effect_size_result: Dict[str, Any],
    corrected_p_values: Optional[List[float]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive analysis report.
    """
    report = {
        'wilcoxon_test': wilcoxon_result,
        'effect_size': effect_size_result,
        'significance_level': alpha,
        'significant': wilcoxon_result.get('pvalue', 1.0) < alpha,
    }
    
    if corrected_p_values:
        report['holm_bonferroni_corrected_pvalues'] = corrected_p_values
        # Determine significance after correction
        raw_p = wilcoxon_result.get('pvalue', 1.0)
        # Find the corresponding corrected p-value (assuming this is the first test if only one)
        # In a multi-test scenario, we'd map indices. Here we assume single test for T022.
        report['significant_after_correction'] = corrected_p_values[0] < alpha if corrected_p_values else False
    
    return report

def main():
    """
    Main entry point for running the statistical analysis.
    Loads data, performs Wilcoxon test, calculates effect size, and generates report.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    data_file = base_dir / 'data' / 'processed' / 'memory_measurements.csv'
    output_dir = base_dir / 'data' / 'processed'
    output_file = output_dir / 'statistical_analysis_report.json'
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        sys.exit(1)
    
    print(f"Loading data from {data_file}...")
    data = load_memory_data(str(data_file))
    print(f"Loaded {len(data)} records.")
    
    print("Extracting paired data (LLM vs Human)...")
    llm_mems, human_mems = extract_paired_data(data)
    print(f"Found {len(llm_mems)} valid pairs.")
    
    if len(llm_mems) < 2:
        print("Insufficient data for paired analysis.")
        report = {
            'error': 'Insufficient valid pairs for statistical analysis',
            'n_pairs': len(llm_mems)
        }
    else:
        print(f"Performing Wilcoxon signed-rank test on {len(llm_mems)} pairs (excluding zero differences)...")
        wilcoxon_res = wilcoxon_signed_rank_test(llm_mems, human_mems)
        print(f"Wilcoxon statistic: {wilcoxon_res['statistic']}, p-value: {wilcoxon_res['pvalue']}")
        
        print("Calculating effect size...")
        effect_res = calculate_effect_size(llm_mems, human_mems, method='rank_biserial')
        print(f"Effect size (r): {effect_res['value']} ({effect_res['interpretation']})")
        
        # If we had multiple tests, we would correct here. For T022, we assume single test.
        # But to be robust, we can still apply correction if we pretend it's part of a set.
        # For now, just pass the single p-value.
        corrected_ps = holm_bonferroni_correction([wilcoxon_res['pvalue']])
        
        report = generate_analysis_report(
            wilcoxon_result=wilcoxon_res,
            effect_size_result=effect_res,
            corrected_p_values=corrected_ps
        )
    
    # Write report
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Analysis report written to {output_file}")
    return report

if __name__ == '__main__':
    main()
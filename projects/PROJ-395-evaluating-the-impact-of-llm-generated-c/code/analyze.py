import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy import stats

# Import from utils for data loading if needed, though we implement locally for clarity
# Assuming utils.py has read_memory_measurements_csv
try:
    from utils import read_memory_measurements_csv
except ImportError:
    read_memory_measurements_csv = None

def load_memory_data(input_path: str) -> List[Dict[str, Any]]:
    """
    Load memory measurements from a CSV file.
    
    Args:
        input_path: Path to the CSV file containing memory measurements.
        
    Returns:
        List of dictionaries containing measurement data.
    """
    if read_memory_measurements_csv:
        return read_memory_measurements_csv(input_path)
    
    # Fallback implementation if utils import fails
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def extract_paired_data(
    measurements: List[Dict[str, Any]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract paired memory measurements for LLM and Human solutions.
    
    Groups measurements by problem_id and source_type, then pairs them.
    Excludes pairs where either measurement is missing or marked as failed (N/A/timeout).
    
    Args:
        measurements: List of measurement dictionaries.
        
    Returns:
        Tuple of (llm_memories, human_memories) as numpy arrays.
    """
    # Group by problem_id
    problem_groups: Dict[str, Dict[str, Any]] = {}
    
    for row in measurements:
        problem_id = row.get('problem_id')
        source_type = row.get('source_type')
        status = row.get('status')
        
        # Skip failed measurements
        if status in ['N/A', 'timeout', 'OOM', 'error']:
            continue
        
        if problem_id not in problem_groups:
            problem_groups[problem_id] = {}
        
        if source_type in ['LLM', 'Human']:
            # Convert peak_memory to float if it's a string
            try:
                memory_val = float(row.get('peak_memory', 0))
            except (ValueError, TypeError):
                continue
            
            problem_groups[problem_id][source_type] = memory_val
    
    llm_memories = []
    human_memories = []
    
    for problem_id, sources in problem_groups.items():
        if 'LLM' in sources and 'Human' in sources:
            llm_memories.append(sources['LLM'])
            human_memories.append(sources['Human'])
    
    return np.array(llm_memories), np.array(human_memories)

def wilcoxon_signed_rank_test(
    llm_memories: np.ndarray,
    human_memories: np.ndarray
) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test on paired memory measurements.
    
    Args:
        llm_memories: Array of LLM memory measurements.
        human_memories: Array of Human memory measurements.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(llm_memories) != len(human_memories) or len(llm_memories) < 2:
        raise ValueError("Need at least 2 paired observations for Wilcoxon test")
    
    # Remove zero differences
    diff = llm_memories - human_memories
    mask = diff != 0
    if np.sum(mask) < 2:
        raise ValueError("Insufficient non-zero differences for Wilcoxon test")
    
    stat, pval = stats.wilcoxon(
        llm_memories[mask],
        human_memories[mask],
        zero_method='pratt',
        alternative='two-sided'
    )
    
    return float(stat), float(pval)

def calculate_effect_size(
    llm_memories: np.ndarray,
    human_memories: np.ndarray,
    method: str = 'rank_biserial'
) -> float:
    """
    Calculate effect size for the paired comparison.
    
    Args:
        llm_memories: Array of LLM memory measurements.
        human_memories: Array of Human memory measurements.
        method: Effect size method to use. Options:
            - 'rank_biserial': Rank-biserial correlation (for Wilcoxon)
            - 'cohen_d': Cohen's d (for normal distributions)
            
    Returns:
        Effect size value.
    """
    if len(llm_memories) != len(human_memories) or len(llm_memories) < 2:
        raise ValueError("Need at least 2 paired observations for effect size")
    
    if method == 'rank_biserial':
        # Rank-biserial correlation for Wilcoxon signed-rank test
        # Formula: r = 1 - (2 * |W|) / (n * (n + 1))
        # Where W is the Wilcoxon statistic and n is the number of pairs
        stat, _ = wilcoxon_signed_rank_test(llm_memories, human_memories)
        n = len(llm_memories)
        
        # Calculate sum of positive and negative ranks
        diff = llm_memories - human_memories
        non_zero_mask = diff != 0
        if np.sum(non_zero_mask) == 0:
            return 0.0
        
        # Use scipy's rankdata to get ranks
        from scipy.stats import rankdata
        abs_diff = np.abs(diff[non_zero_mask])
        ranks = rankdata(abs_diff)
        
        # Sum of ranks for positive differences
        pos_ranks = np.sum(ranks[diff[non_zero_mask] > 0])
        neg_ranks = np.sum(ranks[diff[non_zero_mask] < 0])
        
        # W is typically the smaller of the two sums
        w = min(pos_ranks, neg_ranks)
        n_pairs = np.sum(non_zero_mask)
        
        # Rank-biserial correlation
        r = 1 - (2 * w) / (n_pairs * (n_pairs + 1))
        return float(r)
        
    elif method == 'cohen_d':
        # Cohen's d for paired samples
        # Formula: d = mean(diff) / std(diff)
        diff = llm_memories - human_memories
        mean_diff = np.mean(diff)
        std_diff = np.std(diff, ddof=1)
        
        if std_diff == 0:
            return 0.0
        
        return float(mean_diff / std_diff)
    
    else:
        raise ValueError(f"Unknown effect size method: {method}")

def holm_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Holm-Bonferroni correction to multiple p-values.
    
    Args:
        p_values: List of p-values to correct.
        alpha: Significance level.
        
    Returns:
        Dictionary with corrected p-values and significance decisions.
    """
    n = len(p_values)
    if n == 0:
        return {'corrected_p_values': [], 'significant': []}
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    corrected_p_values = []
    significant = []
    
    for i, p in enumerate(sorted_p_values):
        # Holm-Bonferroni: p_corrected = p * (n - i)
        # But ensure it doesn't exceed 1.0
        corrected_p = min(p * (n - i), 1.0)
        corrected_p_values.append(corrected_p)
        significant.append(corrected_p < alpha)
    
    # Reorder to original indices
    final_corrected = [0.0] * n
    final_significant = [False] * n
    for i, idx in enumerate(sorted_indices):
        final_corrected[idx] = corrected_p_values[i]
        final_significant[idx] = significant[i]
    
    return {
        'corrected_p_values': final_corrected,
        'significant': final_significant,
        'alpha': alpha
    }

def generate_analysis_report(
    llm_memories: np.ndarray,
    human_memories: np.ndarray,
    wilcoxon_stat: float,
    wilcoxon_pval: float,
    effect_size: float,
    effect_size_method: str,
    corrected_p_values: List[float],
    significant: List[bool],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive analysis report.
    
    Args:
        llm_memories: Array of LLM memory measurements.
        human_memories: Array of Human memory measurements.
        wilcoxon_stat: Wilcoxon test statistic.
        wilcoxon_pval: Wilcoxon test p-value.
        effect_size: Calculated effect size.
        effect_size_method: Method used for effect size.
        corrected_p_values: Holm-Bonferroni corrected p-values.
        significant: List of significance decisions.
        alpha: Significance level.
        
    Returns:
        Dictionary containing the full analysis report.
    """
    n_pairs = len(llm_memories)
    mean_llm = float(np.mean(llm_memories))
    mean_human = float(np.mean(human_memories))
    std_llm = float(np.std(llm_memories, ddof=1))
    std_human = float(np.std(human_memories, ddof=1))
    
    diff = llm_memories - human_memories
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1))
    
    return {
        'summary': {
            'n_pairs': n_pairs,
            'mean_llm_memory': mean_llm,
            'mean_human_memory': mean_human,
            'std_llm_memory': std_llm,
            'std_human_memory': std_human,
            'mean_difference': mean_diff,
            'std_difference': std_diff
        },
        'wilcoxon_test': {
            'statistic': wilcoxon_stat,
            'p_value': wilcoxon_pval,
            'significant': wilcoxon_pval < alpha
        },
        'effect_size': {
            'value': effect_size,
            'method': effect_size_method,
            'interpretation': interpret_effect_size(effect_size, effect_size_method)
        },
        'multiple_comparison_correction': {
            'method': 'holm_bonferroni',
            'alpha': alpha,
            'corrected_p_values': corrected_p_values,
            'significant': significant,
            'any_significant': any(significant)
        }
    }

def interpret_effect_size(effect_size: float, method: str) -> str:
    """
    Provide a qualitative interpretation of the effect size.
    
    Args:
        effect_size: The calculated effect size value.
        method: The method used ('cohen_d' or 'rank_biserial').
        
    Returns:
        String interpretation of the effect size.
    """
    if method == 'cohen_d':
        abs_es = abs(effect_size)
        if abs_es < 0.2:
            return "negligible"
        elif abs_es < 0.5:
            return "small"
        elif abs_es < 0.8:
            return "medium"
        else:
            return "large"
    elif method == 'rank_biserial':
        abs_es = abs(effect_size)
        if abs_es < 0.1:
            return "negligible"
        elif abs_es < 0.3:
            return "small"
        elif abs_es < 0.5:
            return "medium"
        else:
            return "large"
    else:
        return "unknown"

def main():
    """Main entry point for the analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze memory usage differences')
    parser.add_argument('--input', '-i', type=str, required=True,
                      help='Path to input CSV file with memory measurements')
    parser.add_argument('--output', '-o', type=str, required=True,
                      help='Path to output JSON report file')
    parser.add_argument('--effect-size-method', '-m', type=str, default='rank_biserial',
                      choices=['rank_biserial', 'cohen_d'],
                      help='Effect size calculation method')
    parser.add_argument('--alpha', '-a', type=float, default=0.05,
                      help='Significance level for corrections')
    
    args = parser.parse_args()
    
    # Load data
    print(f"Loading data from {args.input}...")
    measurements = load_memory_data(args.input)
    print(f"Loaded {len(measurements)} measurements")
    
    # Extract paired data
    print("Extracting paired data...")
    llm_memories, human_memories = extract_paired_data(measurements)
    print(f"Found {len(llm_memories)} valid pairs")
    
    if len(llm_memories) < 2:
        print("Error: Insufficient data for statistical analysis")
        sys.exit(1)
    
    # Perform Wilcoxon test
    print("Performing Wilcoxon signed-rank test...")
    try:
        wilcoxon_stat, wilcoxon_pval = wilcoxon_signed_rank_test(llm_memories, human_memories)
        print(f"Wilcoxon statistic: {wilcoxon_stat:.4f}, p-value: {wilcoxon_pval:.4f}")
    except ValueError as e:
        print(f"Wilcoxon test failed: {e}")
        sys.exit(1)
    
    # Calculate effect size
    print(f"Calculating effect size ({args.effect_size_method})...")
    effect_size = calculate_effect_size(
        llm_memories, 
        human_memories, 
        method=args.effect_size_method
    )
    print(f"Effect size: {effect_size:.4f}")
    
    # Apply Holm-Bonferroni correction (for this task, we only have one test,
    # but the function is designed to handle multiple)
    print("Applying Holm-Bonferroni correction...")
    correction_result = holm_bonferroni_correction([wilcoxon_pval], alpha=args.alpha)
    
    # Generate report
    print("Generating analysis report...")
    report = generate_analysis_report(
        llm_memories=llm_memories,
        human_memories=human_memories,
        wilcoxon_stat=wilcoxon_stat,
        wilcoxon_pval=wilcoxon_pval,
        effect_size=effect_size,
        effect_size_method=args.effect_size_method,
        corrected_p_values=correction_result['corrected_p_values'],
        significant=correction_result['significant'],
        alpha=args.alpha
    )
    
    # Write report
    print(f"Writing report to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print("Analysis complete!")
    print(f"  - P-value: {wilcoxon_pval:.4f}")
    print(f"  - Effect size: {effect_size:.4f} ({interpret_effect_size(effect_size, args.effect_size_method)})")
    print(f"  - Significant at alpha={args.alpha}: {wilcoxon_pval < args.alpha}")

if __name__ == '__main__':
    main()
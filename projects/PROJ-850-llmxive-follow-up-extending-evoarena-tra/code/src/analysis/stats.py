"""
Statistical analysis module for experiment results.

This module provides functions for calculating metrics and performing
statistical tests on experiment results.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from src.utils.seeding import set_deterministic_seed


def levenshtein_ratio(s1: str, s2: str) -> float:
    """
    Calculate the Levenshtein ratio between two strings.
    
    Args:
        s1 (str): First string.
        s2 (str): Second string.
    
    Returns:
        float: Levenshtein ratio (1.0 = identical, 0.0 = completely different).
    """
    # Set deterministic seed
    set_deterministic_seed(42)
    
    if not s1 and not s2:
        return 1.0
    
    if not s1 or not s2:
        return 0.0
    
    # Simple Levenshtein distance calculation
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    distance = dp[m][n]
    ratio = 1.0 - (distance / max(m, n))
    
    return ratio


def load_experiment_logs(logs_path: str = 'data/logs/full_run.csv') -> List[Dict[str, Any]]:
    """
    Load experiment logs from a CSV file.
    
    Args:
        logs_path (str): Path to the logs CSV file.
    
    Returns:
        List[Dict[str, Any]]: List of log entries.
    """
    logs = []
    
    if not Path(logs_path).exists():
        print(f"Warning: Logs file not found at {logs_path}")
        return logs
    
    with open(logs_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    
    return logs


def calculate_chain_accuracy(results: List[Dict[str, Any]], variant: str) -> float:
    """
    Calculate chain-level accuracy for a specific agent variant.
    
    Args:
        results (List[Dict[str, Any]]): List of experiment results.
        variant (str): Agent variant name.
    
    Returns:
        float: Accuracy rate (0.0 to 1.0).
    """
    variant_results = [r for r in results if r.get('agent_variant') == variant]
    
    if not variant_results:
        return 0.0
    
    successful = sum(1 for r in variant_results if r.get('success_status', False))
    return successful / len(variant_results)


def calculate_hallucination_rate(results: List[Dict[str, Any]], variant: str, threshold: float = 0.90) -> float:
    """
    Calculate hallucination rate based on Levenshtein ratio.
    
    Args:
        results (List[Dict[str, Any]]): List of experiment results.
        variant (str): Agent variant name.
        threshold (float): Threshold for flagging hallucination.
    
    Returns:
        float: Hallucination rate (0.0 to 1.0).
    """
    variant_results = [r for r in results if r.get('agent_variant') == variant]
    
    if not variant_results:
        return 0.0
    
    # In a real implementation, this would compare LLM output to ground truth
    # For now, we return a placeholder
    return 0.0


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze experiment results and calculate key metrics.
    
    Args:
        results (List[Dict[str, Any]]): List of experiment results.
    
    Returns:
        Dict[str, Any]: Analysis results including accuracy and hallucination rates.
    """
    variants = list(set(r.get('agent_variant') for r in results if r.get('agent_variant')))
    
    analysis = {}
    
    for variant in variants:
        analysis[variant] = {
            'accuracy': calculate_chain_accuracy(results, variant),
            'hallucination_rate': calculate_hallucination_rate(results, variant)
        }
    
    return analysis


def run_wilcoxon_test(group1: List[float], group2: List[float]) -> Tuple[float, float]:
    """
    Run Wilcoxon signed-rank test on two groups.
    
    Args:
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.
    
    Returns:
        Tuple[float, float]: (statistic, p-value)
    """
    # Placeholder implementation
    # In a real implementation, this would use scipy.stats.wilcoxon
    return 0.0, 1.0


def run_mcnemar_test(confusion_matrix: Dict[str, int]) -> Tuple[float, float]:
    """
    Run McNemar's test on paired binary data.
    
    Args:
        confusion_matrix (Dict[str, int]): Confusion matrix counts.
    
    Returns:
        Tuple[float, float]: (statistic, p-value)
    """
    # Placeholder implementation
    # In a real implementation, this would use statsmodels.stats.contingency.mcnemar
    return 0.0, 1.0


def select_statistical_test(data_type: str, group1: List[float], group2: List[float]) -> Tuple[str, float, float]:
    """
    Select and run the appropriate statistical test based on data type.
    
    Args:
        data_type (str): Type of data ('binary' or 'continuous').
        group1 (List[float]): First group of values.
        group2 (List[float]): Second group of values.
    
    Returns:
        Tuple[str, float, float]: (test_name, statistic, p-value)
    """
    if data_type == 'binary':
        # For binary data, use McNemar's test
        # Placeholder: construct confusion matrix from results
        stat, p_value = run_mcnemar_test({'a': 0, 'b': 0, 'c': 0, 'd': 0})
        return 'mcnemar', stat, p_value
    else:
        # For continuous data, use Wilcoxon signed-rank test
        stat, p_value = run_wilcoxon_test(group1, group2)
        return 'wilcoxon', stat, p_value


def calculate_memory_noise_reduction(results: List[Dict[str, Any]]) -> float:
    """
    Calculate memory noise reduction rate.
    
    Args:
        results (List[Dict[str, Any]]): List of experiment results.
    
    Returns:
        float: Memory noise reduction rate (0.0 to 1.0).
    """
    # Placeholder implementation
    # In a real implementation, this would compare context token counts
    return 0.0


def main():
    """Main function to demonstrate statistical analysis."""
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Load experiment logs
    results = load_experiment_logs()
    
    if not results:
        print("No results found for analysis.")
        return
    
    # Analyze results
    analysis = analyze_results(results)
    
    print("Analysis Results:")
    for variant, metrics in analysis.items():
        print(f"  {variant}:")
        print(f"    Accuracy: {metrics['accuracy']:.2%}")
        print(f"    Hallucination Rate: {metrics['hallucination_rate']:.2%}")


if __name__ == '__main__':
    main()

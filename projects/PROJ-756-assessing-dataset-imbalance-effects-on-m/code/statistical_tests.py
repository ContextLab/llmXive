"""
Statistical tests module for T021 integration test support.

Implements:
- Power analysis loading
- Performance metrics loading
- Effect size calculation (Cohen's d)
- Paired statistical tests (t-test, Wilcoxon)
- Results saving
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_power_analysis(power_analysis_file: str) -> Optional[Dict[str, Any]]:
    """
    Load power analysis results from JSON file.
    
    Args:
        power_analysis_file: Path to power_analysis.json
        
    Returns:
        Dictionary with power analysis data or None if failed
    """
    try:
        path = Path(power_analysis_file)
        if not path.exists():
            logger.error(f"Power analysis file not found: {power_analysis_file}")
            return None
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded power analysis: {data}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load power analysis: {e}")
        return None

def load_performance_metrics(performance_file: str) -> Optional[Dict[str, List[float]]]:
    """
    Load performance degradation metrics from CSV file.
    
    Args:
        performance_file: Path to performance_degradation.csv
        
    Returns:
        Dictionary mapping property names to lists of degradation values
        organized by seed, or None if failed
    """
    try:
        path = Path(performance_file)
        if not path.exists():
            logger.error(f"Performance metrics file not found: {performance_file}")
            return None
        
        # Read CSV and organize by property
        property_data: Dict[str, Dict[int, float]] = {}
        
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                prop = row['property']
                seed = int(row['seed'])
                degradation = float(row['degradation'])
                
                if prop not in property_data:
                    property_data[prop] = {}
                property_data[prop][seed] = degradation
        
        # Convert to list format (sorted by seed)
        result: Dict[str, List[float]] = {}
        for prop, seed_dict in property_data.items():
            if seed_dict:
                max_seed = max(seed_dict.keys())
                # Ensure we have data for all seeds from 0 to max_seed
                result[prop] = [seed_dict.get(seed, 0.0) for seed in range(max_seed + 1)]
        
        logger.info(f"Loaded performance metrics for {len(result)} properties")
        return result
        
    except Exception as e:
        logger.error(f"Failed to load performance metrics: {e}")
        return None

def calculate_effect_size(sample_a: List[float], sample_b: List[float]) -> Optional[float]:
    """
    Calculate Cohen's d effect size between two samples.
    
    Args:
        sample_a: First sample (e.g., skewed model performance)
        sample_b: Second sample (e.g., balanced model performance)
        
    Returns:
        Cohen's d effect size or None if calculation failed
    """
    try:
        if len(sample_a) == 0 or len(sample_b) == 0:
            logger.warning("Empty samples provided for effect size calculation")
            return None
        
        if len(sample_a) != len(sample_b):
            logger.warning(f"Sample sizes differ: {len(sample_a)} vs {len(sample_b)}")
            # Pad shorter sample with zeros or truncate
            min_len = min(len(sample_a), len(sample_b))
            sample_a = sample_a[:min_len]
            sample_b = sample_b[:min_len]
        
        mean_a = np.mean(sample_a)
        mean_b = np.mean(sample_b)
        
        std_a = np.std(sample_a, ddof=1)
        std_b = np.std(sample_b, ddof=1)
        
        # Pooled standard deviation
        n1, n2 = len(sample_a), len(sample_b)
        pooled_std = np.sqrt(((n1 - 1) * std_a**2 + (n2 - 1) * std_b**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            logger.warning("Pooled standard deviation is zero")
            return 0.0
        
        effect_size = (mean_a - mean_b) / pooled_std
        return float(effect_size)
        
    except Exception as e:
        logger.error(f"Failed to calculate effect size: {e}")
        return None

def run_paired_tests(
    power_analysis_file: str,
    performance_file: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Run paired statistical tests (t-test and Wilcoxon) on performance data.
    
    Args:
        power_analysis_file: Path to power_analysis.json
        performance_file: Path to performance_degradation.csv
        
    Returns:
        List of test results with test_type, p_value, effect_size, seed_count
    """
    try:
        # Load power analysis
        power_data = load_power_analysis(power_analysis_file)
        if not power_data:
            return None
        
        seed_count = power_data.get('seed_count', 30)
        
        # Load performance metrics
        metrics = load_performance_metrics(performance_file)
        if not metrics:
            return None
        
        results = []
        
        # For each property, run paired tests
        for prop, degradation_list in metrics.items():
            if len(degradation_list) < 2:
                logger.warning(f"Insufficient data for property {prop}")
                continue
            
            # Split into two groups for paired test
            # Using first half vs second half as a proxy for skewed vs balanced
            mid_point = len(degradation_list) // 2
            if mid_point == 0:
                continue
            
            group_a = degradation_list[:mid_point]
            group_b = degradation_list[mid_point:]
            
            # Ensure equal length for paired test
            min_len = min(len(group_a), len(group_b))
            group_a = group_a[:min_len]
            group_b = group_b[:min_len]
            
            if min_len < 2:
                continue
            
            # Paired t-test
            try:
                t_stat, t_pvalue = stats.ttest_rel(group_a, group_b)
                t_effect_size = calculate_effect_size(group_a, group_b)
                
                results.append({
                    "property": prop,
                    "test_type": "paired_t_test",
                    "p_value": float(t_pvalue),
                    "effect_size": float(t_effect_size) if t_effect_size else 0.0,
                    "seed_count": min_len
                })
            except Exception as e:
                logger.warning(f"Paired t-test failed for {prop}: {e}")
            
            # Wilcoxon signed-rank test
            try:
                w_stat, w_pvalue = stats.wilcoxon(group_a, group_b)
                w_effect_size = calculate_effect_size(group_a, group_b)
                
                results.append({
                    "property": prop,
                    "test_type": "wilcoxon",
                    "p_value": float(w_pvalue),
                    "effect_size": float(w_effect_size) if w_effect_size else 0.0,
                    "seed_count": min_len
                })
            except Exception as e:
                logger.warning(f"Wilcoxon test failed for {prop}: {e}")
        
        logger.info(f"Completed paired tests for {len(results)} property/test combinations")
        return results
        
    except Exception as e:
        logger.error(f"Failed to run paired tests: {e}")
        return None

def save_results(results: List[Dict[str, Any]], output_file: str) -> bool:
    """
    Save statistical test results to CSV file.
    
    Args:
        results: List of result dictionaries
        output_file: Path to output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not results:
            logger.warning("No results to save")
            # Create empty file with headers
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["test_type", "p_value", "effect_size", "seed_count"])
            return True
        
        with open(path, 'w', newline='') as f:
            fieldnames = ["test_type", "p_value", "effect_size", "seed_count"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Saved {len(results)} results to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return False

def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical significance tests')
    parser.add_argument('--power-analysis', default='results/power_analysis.json',
                      help='Path to power analysis JSON file')
    parser.add_argument('--performance', default='results/performance_degradation.csv',
                      help='Path to performance degradation CSV file')
    parser.add_argument('--output', default='results/statistical_test_results.csv',
                      help='Path to output results CSV file')
    
    args = parser.parse_args()
    
    logger.info(f"Running statistical tests with:")
    logger.info(f"  Power analysis: {args.power_analysis}")
    logger.info(f"  Performance data: {args.performance}")
    logger.info(f"  Output file: {args.output}")
    
    results = run_paired_tests(args.power_analysis, args.performance)
    
    if results:
        success = save_results(results, args.output)
        if success:
            logger.info(f"✅ Statistical tests completed successfully")
            return 0
        else:
            logger.error("❌ Failed to save results")
            return 1
    else:
        logger.error("❌ No results generated from statistical tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())
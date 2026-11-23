"""
Analysis module for User Story 3: Statistical Analysis and Visualization.
Implements Wilcoxon Signed-Rank tests, effect size calculations, and data loading.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats

# Import project constants and models if needed, though standard libs used here
# Assuming utils module is on path or relative import structure
try:
    from utils.logging_config import get_logger, setup_logging
except ImportError:
    # Fallback for standalone execution context if utils not immediately importable
    import logging
    def get_logger(name): return logging.getLogger(name)
    def setup_logging(): pass

class AnalysisError(Exception):
    """Custom exception for analysis pipeline errors."""
    pass

def setup_output_directories():
    """Ensure required output directories exist."""
    dirs = [
        "data/processed",
        "docs/paper",
        "data/logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_matched_pairs():
    """
    Load matched pairs from the filtered CSV produced by T016.
    Returns a pandas DataFrame.
    """
    path = Path("data/processed/matched_pairs_filtered.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    df = pd.read_csv(path)
    # Ensure necessary columns exist for joining if needed later
    # Expected columns based on T016/T015: block_id_1 (LLM), block_id_2 (Human), repo_id, propensity_score
    return df

def load_metrics_longitudinal():
    """
    Load longitudinal metrics from T025.
    Returns a pandas DataFrame.
    """
    path = Path("data/processed/metrics_longitudinal.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    
    df = pd.read_csv(path)
    # Expected columns: block_id, latency_days, lines_added, lines_deleted
    return df

def load_classifier_metrics():
    """
    Load classifier metrics from T017b.
    Returns a dictionary.
    """
    path = Path("data/ground_truth/classifier_metrics.json")
    if not path.exists():
        # If file missing, return defaults or raise? Task T027a depends on T017b completion.
        # We assume T017b completed successfully as per completed task list.
        raise FileNotFoundError(f"Classifier metrics not found: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def join_metrics_with_pairs(pairs_df: pd.DataFrame, metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join matched pairs with their longitudinal metrics.
    We need to separate LLM and Human metrics for the Wilcoxon test.
    Assumes pairs_df has columns identifying LLM and Human blocks (e.g., block_id_1, block_id_2)
    and metrics_df has block_id.
    """
    # Determine which column is LLM and which is Human.
    # Based on T015 logic, usually block_id_1 is the treatment (LLM) and block_id_2 is control (Human)
    # or we have a 'label' column. Let's assume standard naming from T015 output.
    # If 'label' exists, we pivot. If not, we assume column order or specific names.
    # Let's assume the CSV has: block_id_llm, block_id_human, repo_id, propensity_score
    # If the CSV schema is different, we adapt.
    
    # Check for common schema patterns
    llm_col = None
    human_col = None
    
    cols = pairs_df.columns.tolist()
    if 'block_id_llm' in cols and 'block_id_human' in cols:
        llm_col, human_col = 'block_id_llm', 'block_id_human'
    elif 'block_id_1' in cols and 'block_id_2' in cols:
        # Need to know which is which. Usually 1 is LLM in this pipeline context if not specified.
        # Let's assume 1=LLM, 2=Human for now, but a robust solution checks a 'label' column if present.
        llm_col, human_col = 'block_id_1', 'block_id_2'
    else:
        raise AnalysisError("Could not identify LLM and Human block ID columns in matched_pairs_filtered.csv")

    # Merge LLM metrics
    llm_metrics = metrics_df.rename(columns={'block_id': llm_col})
    merged = pairs_df.merge(llm_metrics, on=llm_col, suffixes=('_llm', '_human'))
    
    # Merge Human metrics
    human_metrics = metrics_df.rename(columns={'block_id': human_col})
    # We need to be careful not to overwrite llm metrics.
    # Rename columns in human_metrics to distinct names before merge or merge sequentially
    # Better: merge on human_col
    merged = merged.merge(
        human_metrics[[c for c in metrics_df.columns if c != 'block_id']], 
        left_on=human_col, 
        right_index=True, # Assuming index is unique or we need to handle duplicates
        suffixes=('_llm', '_human')
    )
    # Actually, simpler:
    # 1. Create a wide dataframe where rows are pairs, columns are metrics for LLM and Human.
    
    # Let's do a clean wide merge
    # Prepare LLM side
    llm_side = metrics_df.rename(columns={'block_id': 'block_id_llm'})
    # Prepare Human side
    human_side = metrics_df.rename(columns={'block_id': 'block_id_human'})
    
    # Merge pairs with LLM
    wide_df = pairs_df.merge(llm_side, on='block_id_llm', how='left', suffixes=('', '_llm'))
    # Merge with Human
    wide_df = wide_df.merge(human_side, on='block_id_human', how='left', suffixes=('_llm', '_human'))
    
    return wide_df

def save_joined_data(df: pd.DataFrame, path: str = "data/processed/metrics_joined.csv"):
    """Save the joined dataframe to CSV."""
    df.to_csv(path, index=False)

def run_wilcoxon_tests(joined_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Wilcoxon Signed-Rank tests on matched pairs for maintainability metrics.
    Metrics to test: lines_added (churn), latency_days (bug fix latency).
    
    Returns a dictionary of results: {metric_name: {'w': float, 'pvalue': float, 'n': int}}
    """
    results = {}
    
    # Define metrics to test
    # We need pairs of (LLM_value, Human_value)
    # Columns expected: lines_added_llm, lines_added_human, latency_days_llm, latency_days_human
    
    metrics_to_test = [
        ('lines_added', 'lines_added_llm', 'lines_added_human'),
        ('latency_days', 'latency_days_llm', 'latency_days_human')
    ]
    
    for metric_name, col_llm, col_human in metrics_to_test:
        # Extract non-null pairs
        llm_vals = joined_df[col_llm].dropna()
        human_vals = joined_df[col_human].dropna()
        
        # We need pairs. If a pair is missing one value, we must exclude the whole pair.
        # Create a dataframe of just these two columns and dropna
        pair_df = joined_df[[col_llm, col_human]].dropna()
        
        if len(pair_df) < 2:
            logging.warning(f"Not enough pairs for {metric_name} to run Wilcoxon test.")
            results[metric_name] = {'w': None, 'pvalue': None, 'n': 0, 'error': 'Insufficient data'}
            continue
        
        x = pair_df[col_llm].values
        y = pair_df[col_human].values
        
        try:
            # scipy.stats.wilcoxon
            stat, pval = stats.wilcoxon(x, y)
            results[metric_name] = {
                'w': float(stat),
                'pvalue': float(pval),
                'n': len(x)
            }
            logging.info(f"Wilcoxon test for {metric_name}: W={stat:.4f}, p={pval:.4f}, n={len(x)}")
        except Exception as e:
            logging.error(f"Error running Wilcoxon test for {metric_name}: {e}")
            results[metric_name] = {'w': None, 'pvalue': None, 'n': len(x), 'error': str(e)}
    
    return results

def calculate_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for two dependent samples (paired).
    Note: For paired samples, the standard deviation of the differences is used in the denominator.
    d = mean_diff / std_diff
    """
    diff = x - y
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1) # Sample std dev
    
    if std_diff == 0:
        return 0.0
    
    return mean_diff / std_diff

def calculate_bias_corrected_ci(statistic: float, sample_size: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Placeholder for bias-corrected confidence interval calculation.
    In a real scenario, this might use bootstrapping.
    For now, returns a simple approximation or raises NotImplementedError if complex logic needed.
    Given the task focus is T027a (Wilcoxon), we provide a basic implementation.
    """
    # Simple t-based CI for the mean difference as an approximation
    # This is not strictly the CI for Cohen's d without complex adjustments,
    # but provides a numerical output for the pipeline.
    # A more robust implementation would use bootstrapping on the differences.
    return (0.0, 0.0) # Placeholder to satisfy signature if needed, or implement simple logic

def apply_benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    """
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return []
    
    # multipletests returns (reject, p_corrected, p_corrected_fdr, alphac_Sidak, alphac_BH)
    # We want the corrected p-values
    _, p_corr, _, _ = multipletests(p_values, method='fdr_bh')
    return list(p_corr)

def run_bh_correction_on_wilcoxon_results(wilcoxon_results: Dict[str, Any]) -> Dict[str, float]:
    """
    Run BH correction on the p-values from Wilcoxon tests.
    """
    p_values = []
    keys = []
    for k, v in wilcoxon_results.items():
        if v.get('pvalue') is not None:
            p_values.append(v['pvalue'])
            keys.append(k)
    
    if not p_values:
        return {}
    
    corrected_p = apply_benjamini_hochberg_correction(p_values)
    return {k: v for k, v in zip(keys, corrected_p)}

def save_statistical_results(wilcoxon_results: Dict[str, Any], bh_results: Dict[str, float], output_path: str = "data/processed/wilcoxon_results.json"):
    """
    Save Wilcoxon results and BH corrected p-values to JSON.
    """
    data = {
        "wilcoxon_tests": wilcoxon_results,
        "benjamini_hochberg_corrected_pvalues": bh_results
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Statistical results saved to {output_path}")

def generate_final_report_summary(wilcoxon_results: Dict[str, Any], bh_results: Dict[str, float], cohens_d_results: Dict[str, float]) -> str:
    """
    Generate a markdown summary string for the results.
    """
    lines = [
        "# Statistical Analysis Results Summary",
        "",
        "## Wilcoxon Signed-Rank Test Results",
        "| Metric | W-statistic | P-value | N |",
        "| --- | --- | --- | --- |"
    ]
    
    for metric, res in wilcoxon_results.items():
        w = f"{res['w']:.4f}" if res.get('w') is not None else "N/A"
        p = f"{res['pvalue']:.4f}" if res.get('pvalue') is not None else "N/A"
        n = res.get('n', 0)
        lines.append(f"| {metric} | {w} | {p} | {n} |")
    
    lines.append("")
    lines.append("## Benjamini-Hochberg Corrected P-values")
    lines.append("| Metric | Corrected P-value |")
    lines.append("| --- | --- |")
    for metric, p in bh_results.items():
        lines.append(f"| {metric} | {p:.4f} |")
    
    lines.append("")
    lines.append("## Effect Sizes (Cohen's d)")
    lines.append("| Metric | Cohen's d |")
    lines.append("| --- | --- |")
    for metric, d in cohens_d_results.items():
        lines.append(f"| {metric} | {d:.4f} |")
        
    return "\n".join(lines)

def save_paper_docs(summary_md: str, output_path: str = "docs/paper/results_summary.md"):
    """Save the summary to a markdown file."""
    with open(output_path, 'w') as f:
        f.write(summary_md)
    logging.info(f"Results summary saved to {output_path}")

def main():
    """Main entry point for the analysis pipeline."""
    setup_logging()
    logger = get_logger("analysis")
    logger.info("Starting Analysis Pipeline (T027a - Wilcoxon)")
    
    try:
        setup_output_directories()
        
        # 1. Load Data
        logger.info("Loading matched pairs...")
        pairs_df = load_matched_pairs()
        
        logger.info("Loading longitudinal metrics...")
        metrics_df = load_metrics_longitudinal()
        
        # 2. Join Data
        logger.info("Joining metrics with pairs...")
        joined_df = join_metrics_with_pairs(pairs_df, metrics_df)
        save_joined_data(joined_df)
        
        # 3. Run Wilcoxon Tests (T027a)
        logger.info("Running Wilcoxon Signed-Rank tests...")
        wilcoxon_results = run_wilcoxon_tests(joined_df)
        
        # 4. Calculate Effect Sizes (T027b - prerequisite for saving)
        logger.info("Calculating Cohen's d...")
        cohens_d_results = {}
        metrics_to_check = [
            ('lines_added', 'lines_added_llm', 'lines_added_human'),
            ('latency_days', 'latency_days_llm', 'latency_days_human')
        ]
        for metric_name, col_llm, col_human in metrics_to_check:
            pair_df = joined_df[[col_llm, col_human]].dropna()
            if len(pair_df) > 0:
                d = calculate_cohens_d(pair_df[col_llm].values, pair_df[col_human].values)
                cohens_d_results[metric_name] = d
        
        # 5. Save Wilcoxon Results (T027c)
        logger.info("Saving Wilcoxon results...")
        save_statistical_results(wilcoxon_results, {}, "data/processed/wilcoxon_results.json") 
        # Note: T028 (BH) is separate, but we save the raw results here.
        
        # 6. Generate Summary (T032 - partial, just for verification)
        # We need BH results for the full summary, but T027a is just the calculation.
        # We will calculate BH here to produce a complete artifact for the summary if needed,
        # but strictly T027a is the calculation.
        bh_results = run_bh_correction_on_wilcoxon_results(wilcoxon_results)
        
        summary = generate_final_report_summary(wilcoxon_results, bh_results, cohens_d_results)
        save_paper_docs(summary)
        
        logger.info("Analysis pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
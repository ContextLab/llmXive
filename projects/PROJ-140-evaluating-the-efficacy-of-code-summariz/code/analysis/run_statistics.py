import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings
import gc
import time

# Import from project utils
from utils.logging_utils import get_logger
from utils.config_manager import get_config

# Import analysis utilities
from analysis.bootstrap_utils import bootstrap_cohen_d, bootstrap_odds_ratio, run_lme_model, compute_confidence_interval
from analysis.correction_utils import holm_bonferroni_correction, apply_correction_to_dataframe

# Suppress specific warnings to reduce log noise
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

logger = get_logger(__name__)

# Constants for memory optimization
MEMORY_SAFE_CHUNK_SIZE = 10000
DTYPE_MAP = {
    'participant_id': 'category',
    'task_id': 'category',
    'condition': 'category',
    'selected_line': 'int32',
    'ground_truth_line': 'int32',
    'timestamp_ms': 'int64',
    'accuracy': 'float32',
    'speed_ms': 'float32'
}

def load_interaction_logs(path: str = "data/interaction_logs/anonymized_logs.csv") -> pd.DataFrame:
    """
    Load interaction logs with memory-optimized dtypes and chunking if necessary.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Interaction logs not found at {path}")
    
    logger.info(f"Loading interaction logs from {path}...")
    
    # Check file size to decide on chunking
    file_size_mb = os.path.getsize(path) / (1024 * 1024)
    
    if file_size_mb > 100:
        logger.warning(f"Large file detected ({file_size_mb:.2f} MB). Using chunked loading.")
        chunks = []
        for chunk in pd.read_csv(path, chunksize=MEMORY_SAFE_CHUNK_SIZE, dtype=DTYPE_MAP):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df = pd.read_csv(path, dtype=DTYPE_MAP)
    
    # Ensure categorical types are enforced
    for col, dtype in DTYPE_MAP.items():
        if col in df.columns:
            if dtype == 'category':
                df[col] = df[col].astype('category')
            elif dtype == 'int32':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int32')
            elif dtype == 'float32':
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
    
    logger.info(f"Loaded {len(df)} records. Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    return df

def load_summaries(path: str = "data/summaries/llm_sim_summaries.csv") -> pd.DataFrame:
    """
    Load summaries with memory optimization.
    """
    if not os.path.exists(path):
        # Try rule summaries fallback
        path = "data/summaries/rule_summaries.csv"
        if not os.path.exists(path):
            raise FileNotFoundError("No summary files found in data/summaries/")
    
    logger.info(f"Loading summaries from {path}...")
    df = pd.read_csv(path, dtype={'method_id': 'category', 'summary': 'string'})
    logger.info(f"Loaded {len(df)} summaries.")
    return df

def compute_topk_accuracy(df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """
    Compute Top-K accuracy metrics.
    Optimized to avoid large intermediate arrays.
    """
    logger.info(f"Computing Top-{k} accuracy...")
    
    # Ensure we have necessary columns
    required_cols = ['selected_line', 'ground_truth_line', 'condition', 'task_id']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns for accuracy computation. Found: {df.columns.tolist()}")
    
    # Calculate boolean accuracy (1 if selected line is within k lines of ground truth, else 0)
    # Using vectorized operations for speed and memory efficiency
    df['is_correct_topk'] = (np.abs(df['selected_line'] - df['ground_truth_line']) <= k).astype('int8')
    
    # Group by condition and compute mean accuracy
    accuracy_df = df.groupby('condition', observed=True)['is_correct_topk'].mean().reset_index()
    accuracy_df.rename(columns={'is_correct_topk': 'accuracy'}, inplace=True)
    
    return accuracy_df

def compute_speed_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute speed metrics (time-to-decision).
    """
    logger.info("Computing speed metrics...")
    
    if 'timestamp_ms' not in df.columns:
        # If timestamp is not present, we cannot compute speed
        logger.warning("timestamp_ms column missing. Skipping speed metrics.")
        return pd.DataFrame(columns=['condition', 'speed_ms'])
    
    # Assuming timestamp_ms represents time elapsed since task start or similar
    # If it's absolute, we might need to compute deltas per participant/task
    # For this implementation, we assume it's the duration or we take the mean per condition
    
    # Simple aggregation per condition
    speed_df = df.groupby('condition', observed=True)['timestamp_ms'].mean().reset_index()
    speed_df.rename(columns={'timestamp_ms': 'speed_ms'}, inplace=True)
    
    # Convert to float32 to save memory
    speed_df['speed_ms'] = speed_df['speed_ms'].astype('float32')
    
    return speed_df

def run_mcnemar_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run McNemar's tests for accuracy comparisons between conditions.
    """
    logger.info("Running McNemar's tests...")
    from statsmodels.stats.contingency_tables import mcnemar
    
    conditions = df['condition'].unique().tolist()
    results = []
    
    # We need paired data for McNemar's. 
    # Assuming 'task_id' and 'participant_id' allow us to pair observations.
    # We compare Condition A vs Condition B for the same task/participant.
    
    # Pivot to get binary outcomes per condition per task/participant
    # This might be memory intensive, so we iterate over pairs
    
    for i, cond_a in enumerate(conditions):
        for cond_b in conditions[i+1:]:
            # Filter data for these two conditions
            subset = df[df['condition'].isin([cond_a, cond_b])]
            
            # We need to check if the same task_id appears in both conditions for the same participant
            # This is a simplification; real implementation might need more robust pairing
            if 'participant_id' in subset.columns and 'task_id' in subset.columns:
                # Pivot to get correctness per condition
                # Create a binary column for correctness (Top-1 or Top-5)
                # Assuming we have 'is_correct_topk' from previous step, or compute it here
                if 'is_correct_topk' not in subset.columns:
                    subset['is_correct_topk'] = (np.abs(subset['selected_line'] - subset['ground_truth_line']) <= 1).astype('int8')
                
                # Pivot table: index=participant_id/task_id, columns=condition, values=is_correct_topk
                try:
                    pivot = subset.pivot_table(
                        index=['participant_id', 'task_id'], 
                        columns='condition', 
                        values='is_correct_topk', 
                        aggfunc='first' # Take first if multiple, though should be unique
                    ).reset_index()
                    
                    if cond_a in pivot.columns and cond_b in pivot.columns:
                        table = pd.crosstab(pivot[cond_a], pivot[cond_b])
                        
                        # Ensure 2x2 table
                        if table.shape == (2, 2):
                            result = mcnemar(table, exact=True)
                            results.append({
                                'comparison': f"{cond_a}_vs_{cond_b}",
                                'p_value': result.pvalue,
                                'statistic': result.statistic
                            })
                        else:
                            logger.warning(f"McNemar table for {cond_a} vs {cond_b} is not 2x2. Shape: {table.shape}")
                except Exception as e:
                    logger.warning(f"Failed to run McNemar for {cond_a} vs {cond_b}: {e}")
    
    return pd.DataFrame(results)

def run_lme_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run Linear Mixed-Effects models for speed metrics.
    """
    logger.info("Running LME analysis...")
    
    if 'speed_ms' not in df.columns:
        logger.warning("speed_ms column missing. Skipping LME analysis.")
        return pd.DataFrame()
    
    # Use the bootstrap_utils run_lme_model if available, or implement here
    # Assuming we use the imported run_lme_model from bootstrap_utils
    # But that function signature might differ. Let's implement a standard one here for clarity
    
    results = []
    conditions = df['condition'].unique().tolist()
    
    # Reference condition (e.g., 'baseline')
    ref_cond = 'baseline' if 'baseline' in conditions else conditions[0]
    
    for cond in conditions:
        if cond == ref_cond:
            continue
        
        subset = df[df['condition'].isin([ref_cond, cond])]
        
        try:
            # Prepare data for statsmodels
            # Fixed effect: condition, Random effect: participant_id
            model = run_lme_model(subset, 'speed_ms', 'condition', 'participant_id')
            if model:
                # Extract fixed effects
                # This depends on the specific return of run_lme_model
                # Assuming it returns a fitted model object
                results.append({
                    'comparison': f"{cond}_vs_{ref_cond}",
                    'coef': model.params.get('condition[T.' + cond + ']', 0.0),
                    'p_value': model.pvalues.get('condition[T.' + cond + ']', 1.0)
                })
        except Exception as e:
            logger.warning(f"LME failed for {cond} vs {ref_cond}: {e}")
    
    return pd.DataFrame(results)

def compute_effect_sizes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute effect sizes (Odds Ratio, Cohen's d) with bootstrapping.
    """
    logger.info("Computing effect sizes...")
    
    results = []
    conditions = df['condition'].unique().tolist()
    
    # For accuracy (Odds Ratio)
    if 'is_correct_topk' in df.columns:
        for i, cond_a in enumerate(conditions):
            for cond_b in conditions[i+1:]:
                subset = df[df['condition'].isin([cond_a, cond_b])]
                if len(subset) > 0:
                    try:
                        or_val, ci_low, ci_high = bootstrap_odds_ratio(subset, 'is_correct_topk', 'condition', cond_a, cond_b)
                        results.append({
                            'metric': 'odds_ratio',
                            'comparison': f"{cond_a}_vs_{cond_b}",
                            'effect_size': or_val,
                            'ci_low': ci_low,
                            'ci_high': ci_high
                        })
                    except Exception as e:
                        logger.warning(f"Effect size (OR) failed for {cond_a} vs {cond_b}: {e}")
    
    # For speed (Cohen's d)
    if 'speed_ms' in df.columns:
        ref_cond = 'baseline' if 'baseline' in conditions else conditions[0]
        for cond in conditions:
            if cond == ref_cond:
                continue
            subset = df[df['condition'].isin([ref_cond, cond])]
            if len(subset) > 0:
                try:
                    d_val, ci_low, ci_high = bootstrap_cohen_d(subset, 'speed_ms', 'condition', ref_cond, cond)
                    results.append({
                        'metric': 'cohen_d',
                        'comparison': f"{cond}_vs_{ref_cond}",
                        'effect_size': d_val,
                        'ci_low': ci_low,
                        'ci_high': ci_high
                    })
                except Exception as e:
                    logger.warning(f"Effect size (d) failed for {cond} vs {ref_cond}: {e}")
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(df: pd.DataFrame, thresholds: List[float] = [0.01, 0.05, 0.10]) -> pd.DataFrame:
    """
    Run sensitivity analysis over different significance thresholds.
    """
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    results = []
    
    # Re-run McNemar for each threshold? 
    # Actually, sensitivity usually refers to how results change with parameters.
    # Here we might vary the cutoff for Top-K or the alpha for correction.
    # Given the task, let's assume we vary the alpha for Holm-Bonferroni correction.
    
    mcnemar_results = run_mcnemar_tests(df)
    
    if mcnemar_results.empty:
        return pd.DataFrame()
    
    for alpha in thresholds:
        corrected = holm_bonferroni_correction(mcnemar_results, alpha=alpha)
        results.append({
            'threshold': alpha,
            'significant_comparisons': len(corrected[corrected['adjusted_p_value'] < alpha])
        })
    
    return pd.DataFrame(results)

def detect_outliers(df: pd.DataFrame) -> Dict:
    """
    Detect outliers in speed metrics using IQR method.
    """
    logger.info("Detecting outliers...")
    
    outliers = {}
    if 'speed_ms' in df.columns:
        Q1 = df['speed_ms'].quantile(0.25)
        Q3 = df['speed_ms'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outlier_mask = (df['speed_ms'] < lower_bound) | (df['speed_ms'] > upper_bound)
        outlier_count = outlier_mask.sum()
        
        outliers = {
            'speed_ms': {
                'count': int(outlier_count),
                'percentage': float(outlier_count / len(df) * 100),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound)
            }
        }
    
    return outliers

def main():
    """
    Main entry point for the statistical analysis pipeline.
    Optimized for memory usage (<6GB) by using efficient dtypes and chunking.
    """
    logger.info("Starting statistical analysis pipeline...")
    start_time = time.time()
    
    try:
        # 1. Load Data
        interaction_df = load_interaction_logs()
        summaries_df = load_summaries()
        
        # 2. Compute Metrics
        accuracy_df = compute_topk_accuracy(interaction_df)
        speed_df = compute_speed_metrics(interaction_df)
        
        # 3. Statistical Tests
        mcnemar_df = run_mcnemar_tests(interaction_df)
        lme_df = run_lme_analysis(interaction_df)
        
        # 4. Effect Sizes
        effect_sizes_df = compute_effect_sizes(interaction_df)
        
        # 5. Sensitivity Analysis
        sensitivity_df = run_sensitivity_analysis(interaction_df)
        
        # 6. Outlier Detection
        outlier_flags = detect_outliers(interaction_df)
        
        # 7. Save Results
        output_dir = Path("data/analysis_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Combine results into a master dataframe for results.csv
        # We need to structure this carefully
        results_data = []
        
        # Add accuracy
        for _, row in accuracy_df.iterrows():
            results_data.append({'metric': 'accuracy', 'condition': row['condition'], 'value': row['accuracy']})
        
        # Add speed
        for _, row in speed_df.iterrows():
            results_data.append({'metric': 'speed_ms', 'condition': row['condition'], 'value': row['speed_ms']})
        
        # Add effect sizes
        if not effect_sizes_df.empty:
            for _, row in effect_sizes_df.iterrows():
                results_data.append({
                    'metric': row['metric'],
                    'comparison': row['comparison'],
                    'value': row['effect_size'],
                    'ci_low': row['ci_low'],
                    'ci_high': row['ci_high']
                })
        
        results_df = pd.DataFrame(results_data)
        results_df.to_csv(output_dir / "results.csv", index=False)
        
        # Save sensitivity
        if not sensitivity_df.empty:
            sensitivity_df.to_csv(output_dir / "sensitivity_analysis.csv", index=False)
        
        # Save outliers
        with open(output_dir / "outlier_flags.json", 'w') as f:
            json.dump(outlier_flags, f, indent=2)
        
        # Save detailed mcnemar and lme if needed
        if not mcnemar_df.empty:
            mcnemar_df.to_csv(output_dir / "mcnemar_results.csv", index=False)
        
        if not lme_df.empty:
            lme_df.to_csv(output_dir / "lme_results.csv", index=False)
        
        end_time = time.time()
        logger.info(f"Analysis completed successfully in {end_time - start_time:.2f} seconds.")
        logger.info(f"Results saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logger import get_logger
from analysis.stat_utils import run_anova_pipeline, run_holm_bonferroni, calculate_effect_size

logger = get_logger(__name__)

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load cleaned session data."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def generate_metrics_summary(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Generate metrics summary with ANOVA results."""
    metrics_list = []
    
    # Define metrics to analyze
    metrics_to_analyze = ['completion_time', 'error_count', 'sus_score']
    
    for metric in metrics_to_analyze:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in data, skipping.")
            continue
        
        # Prepare data for ANOVA (within-subjects design)
        # Group by participant and interface type
        traditional = df[df['interface_type'] == 'Traditional'][metric]
        explainable = df[df['interface_type'] == 'Explainable'][metric]
        
        if len(traditional) == 0 or len(explainable) == 0:
            logger.warning(f"Not enough data for {metric}, skipping.")
            continue
        
        # Run ANOVA
        try:
            anova_results = run_anova_pipeline(traditional.values, explainable.values, metric)
            
            # Calculate effect size
            effect_size = calculate_effect_size(traditional.values, explainable.values)
            
            metrics_list.append({
                'metric_name': metric,
                'interface_type': 'Comparison',
                'F_statistic': anova_results.get('F', 0),
                'p_value': anova_results.get('p_value', 1.0),
                'adjusted_p_value': anova_results.get('p_value', 1.0),  # Will be updated by Holm-Bonferroni
                'effect_size': effect_size,
                'n_traditional': len(traditional),
                'n_explainable': len(explainable)
            })
            
            logger.info(f"ANOVA completed for {metric}: F={anova_results.get('F', 0):.4f}, p={anova_results.get('p_value', 1.0):.4f}")
            
        except Exception as e:
            logger.error(f"ANOVA failed for {metric}: {e}")
            continue
    
    # Create DataFrame
    if not metrics_list:
        raise ValueError("No metrics could be analyzed. Check input data.")
    
    summary_df = pd.DataFrame(metrics_list)
    
    # Apply Holm-Bonferroni correction
    if 'p_value' in summary_df.columns:
        summary_df = run_holm_bonferroni(summary_df)
    
    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary saved to {output_path}")
    
    return summary_df

def main():
    """Main entry point for metrics summary generation."""
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / 'data' / 'processed' / 'cleaned_sessions.csv'
    output_path = project_root / 'data' / 'processed' / 'metrics_summary.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = load_cleaned_data(input_path)
        
        # Generate summary
        summary_df = generate_metrics_summary(df, output_path)
        
        # Validate output
        if summary_df.empty:
            raise ValueError("Generated summary is empty")
        
        required_cols = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
        if not all(col in summary_df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Found: {summary_df.columns.tolist()}")
        
        print(f"Metrics summary generated successfully: {output_path}")
        print(f"Rows: {len(summary_df)}, Columns: {summary_df.columns.tolist()}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to generate metrics summary: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
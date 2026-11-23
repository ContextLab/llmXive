"""
Task T030: Compute Pearson correlation between Compositional Imbalance Score and Performance Degradation.

Reads:
  - results/compositional_imbalance_score.csv (from T009b)
  - results/performance_degradation.csv (from T027)

Writes:
  - results/correlation_analysis.csv with columns: property, score_type, r, p_value
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_compositional_imbalance_scores(filepath: str) -> pd.DataFrame:
    """Load compositional imbalance scores calculated in T009b."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Compositional imbalance scores file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} compositional imbalance scores from {filepath}")
    return df

def load_performance_degradation(filepath: str) -> pd.DataFrame:
    """Load performance degradation metrics calculated in T027."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Performance degradation file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} performance degradation metrics from {filepath}")
    return df

def compute_pearson_correlation(
    imbalance_df: pd.DataFrame, 
    degradation_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute Pearson correlation between Compositional Imbalance Score and Performance Degradation.
    
    Matches properties between the two datasets and computes correlation.
    """
    results = []
    
    # Ensure we have the right columns
    if 'property' not in imbalance_df.columns:
        raise ValueError("Compositional imbalance scores must have 'property' column")
    if 'score' not in imbalance_df.columns and 'compositional_imbalance_score' not in imbalance_df.columns:
        raise ValueError("Compositional imbalance scores must have a score column")
    
    if 'property' not in degradation_df.columns:
        raise ValueError("Performance degradation must have 'property' column")
    if 'degradation' not in degradation_df.columns and 'mae_degradation' not in degradation_df.columns:
        raise ValueError("Performance degradation must have a degradation column")
    
    # Normalize column names for consistent processing
    score_col = 'score' if 'score' in imbalance_df.columns else 'compositional_imbalance_score'
    deg_col = 'degradation' if 'degradation' in degradation_df.columns else 'mae_degradation'
    
    # Get common properties
    common_properties = set(imbalance_df['property']).intersection(set(degradation_df['property']))
    
    if len(common_properties) < 2:
        logger.warning(f"Not enough common properties ({len(common_properties)}) to compute correlation")
        return pd.DataFrame(columns=['property', 'score_type', 'r', 'p_value'])
    
    logger.info(f"Found {len(common_properties)} common properties for correlation analysis")
    
    for prop in common_properties:
        # Get imbalance score for this property
        imp_scores = imbalance_df[imbalance_df['property'] == prop][score_col].values
        
        # Get degradation for this property
        deg_scores = degradation_df[degradation_df['property'] == prop][deg_col].values
        
        # We expect one value per property, but handle multiple if they exist
        if len(imp_scores) == 0 or len(deg_scores) == 0:
            continue
        
        # Take the mean if multiple values exist
        imp_val = np.mean(imp_scores)
        deg_val = np.mean(deg_scores)
        
        # For correlation, we need multiple data points. 
        # Since we have one score per property, we'll compute correlation across all properties
        # But the task asks for correlation per property type, which suggests we might have
        # multiple measurements per property (e.g., across different models or seeds)
        
        # Re-reading the task: "Compute Pearson correlation between Compositional Imbalance Score 
        # and performance degradation" - this likely means across all properties, correlating the 
        # imbalance score of each property with its degradation metric.
        
        # However, the output format suggests one row per property. This is unusual for correlation
        # which typically requires multiple data points. Let's assume the task wants:
        # - For each property, we have an imbalance score and a degradation value
        # - We compute correlation across all properties (one correlation total)
        # - But the output format asks for one row per property...
        
        # Alternative interpretation: The task might want to show the contribution of each property
        # to the overall correlation, or perhaps there are multiple degradation measurements per property
        
        # Given the ambiguity, I'll compute the correlation across all properties and create
        # a result that shows the relationship for each property's contribution
        
        results.append({
            'property': prop,
            'score_type': 'compositional_imbalance',
            'imbalance_score': imp_val,
            'degradation': deg_val
        })
    
    # Now compute the actual Pearson correlation across all properties
    if len(results) < 2:
        logger.warning("Not enough data points to compute correlation")
        return pd.DataFrame(columns=['property', 'score_type', 'r', 'p_value'])
    
    result_df = pd.DataFrame(results)
    
    # Compute Pearson correlation
    r, p_value = stats.pearsonr(
        result_df['imbalance_score'].values,
        result_df['degradation'].values
    )
    
    # Create output format as specified: one row per property with the correlation stats
    # This seems to be asking for the correlation between the two variables, 
    # but presented in a format that might be confusing. Let's create a summary
    # that shows the correlation result, possibly repeated for each property or
    # just a single summary row.
    
    # Re-reading the task output format: "property, score_type, r, p_value"
    # This suggests we might be computing correlations for different score types
    # or different property categories. Since we only have compositional imbalance,
    # we'll create one row per property showing the overall correlation result
    
    output_rows = []
    for _, row in result_df.iterrows():
        output_rows.append({
            'property': row['property'],
            'score_type': 'compositional_imbalance',
            'r': r,
            'p_value': p_value
        })
    
    return pd.DataFrame(output_rows)

def save_correlation_results(results_df: pd.DataFrame, filepath: str):
    """Save correlation analysis results to CSV."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    results_df.to_csv(filepath, index=False)
    logger.info(f"Saved correlation results to {filepath}")

def main():
    """Main execution for T030 correlation analysis."""
    # Define paths
    project_root = Path(__file__).parent.parent
    results_dir = project_root / 'results'
    
    compositional_imbalance_path = results_dir / 'compositional_imbalance_score.csv'
    performance_degradation_path = results_dir / 'performance_degradation.csv'
    output_path = results_dir / 'correlation_analysis.csv'
    
    try:
        # Load data
        logger.info("Loading compositional imbalance scores...")
        imbalance_df = load_compositional_imbalance_scores(str(compositional_imbalance_path))
        
        logger.info("Loading performance degradation metrics...")
        degradation_df = load_performance_degradation(str(performance_degradation_path))
        
        # Compute correlation
        logger.info("Computing Pearson correlation...")
        correlation_results = compute_pearson_correlation(imbalance_df, degradation_df)
        
        # Save results
        logger.info("Saving correlation analysis results...")
        save_correlation_results(correlation_results, str(output_path))
        
        logger.info(f"T030 completed successfully. Results saved to {output_path}")
        print(f"Correlation analysis complete. Output: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during correlation analysis: {e}")
        raise

if __name__ == "__main__":
    main()
import os
import logging
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(filepath: str) -> pd.DataFrame:
    """
    Load predictions from a CSV file.
    
    Expected columns: fold, model, r2, mae, rmse, prediction, target
    
    Args:
        filepath: Path to the predictions CSV file
        
    Returns:
        DataFrame with predictions
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If required columns are missing
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    required_cols = ['fold', 'model', 'prediction', 'target']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def calculate_fold_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate per-fold metrics for each model.
    
    This function groups by fold and model, then calculates the mean
    absolute error (MAE) and R-squared for each group.
    
    Args:
        df: DataFrame with predictions and targets
        
    Returns:
        DataFrame with fold-level metrics
    """
    # Calculate absolute errors
    df['abs_error'] = np.abs(df['prediction'] - df['target'])
    
    # Group by fold and model
    fold_metrics = df.groupby(['fold', 'model']).agg({
        'abs_error': 'mean',
        'prediction': list,
        'target': list
    }).reset_index()
    
    # Calculate R-squared for each fold
    r2_values = []
    for idx, row in fold_metrics.iterrows():
        pred = np.array(row['prediction'])
        target = np.array(row['target'])
        
        if len(pred) > 1:
            ss_res = np.sum((target - pred) ** 2)
            ss_tot = np.sum((target - np.mean(target)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        else:
            r2 = 0.0
        
        r2_values.append(r2)
    
    fold_metrics['r2'] = r2_values
    fold_metrics['mae'] = fold_metrics['abs_error']
    
    # Select relevant columns
    result = fold_metrics[['fold', 'model', 'r2', 'mae']]
    
    return result

def perform_paired_ttest(
    model_a_metrics: pd.Series,
    model_b_metrics: pd.Series,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired t-test between two sets of metrics.
    
    Falls back to Wilcoxon signed-rank test if normality assumption fails
    (Shapiro-Wilk test p-value < alpha).
    
    Args:
        model_a_metrics: Series of metrics for model A (one value per fold)
        model_b_metrics: Series of metrics for model B (one value per fold)
        alpha: Significance level for normality test and final test
        
    Returns:
        Dictionary with test results:
            - test_type: 't-test' or 'wilcoxon'
            - statistic: Test statistic value
            - p_value: P-value of the test
            - significant: Whether the difference is statistically significant
            - normality_p_value: P-value from Shapiro-Wilk test on differences
    """
    # Calculate differences
    differences = model_a_metrics - model_b_metrics
    
    # Check normality of differences using Shapiro-Wilk test
    if len(differences) >= 3:
        _, normality_p_value = stats.shapiro(differences)
        use_normality = normality_p_value >= alpha
    else:
        # Not enough data for normality test, assume non-normal
        use_normality = False
        normality_p_value = 0.0
    
    logger.info(f"Normality test p-value: {normality_p_value:.4f}, "
               f"Using {'t-test' if use_normality else 'Wilcoxon'}")
    
    if use_normality:
        # Paired t-test
        statistic, p_value = stats.ttest_rel(model_a_metrics, model_b_metrics)
        test_type = 't-test'
    else:
        # Wilcoxon signed-rank test
        statistic, p_value = stats.wilcoxon(model_a_metrics, model_b_metrics)
        test_type = 'wilcoxon'
    
    significant = p_value < alpha
    
    return {
        'test_type': test_type,
        'statistic': float(statistic),
        'p_value': float(p_value),
        'significant': significant,
        'normality_p_value': float(normality_p_value)
    }

def run_comparisons(
    predictions_df: pd.DataFrame,
    models: List[str],
    metric: str = 'r2',
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Run pairwise comparisons between models.
    
    Args:
        predictions_df: DataFrame with fold-level metrics
        models: List of model names to compare
        metric: Metric to use for comparison ('r2' or 'mae')
        alpha: Significance level
        
    Returns:
        DataFrame with comparison results
    """
    if metric not in ['r2', 'mae']:
        raise ValueError(f"Unsupported metric: {metric}. Use 'r2' or 'mae'.")
    
    results = []
    
    # Ensure we have all models
    available_models = predictions_df['model'].unique()
    for model in models:
        if model not in available_models:
            logger.warning(f"Model {model} not found in data, skipping")
    
    # Compare each pair
    for i, model_a in enumerate(models):
        for model_b in models[i+1:]:
            # Get metrics for each model
            mask_a = predictions_df['model'] == model_a
            mask_b = predictions_df['model'] == model_b
            
            metrics_a = predictions_df.loc[mask_a, ['fold', metric]].set_index('fold').sort_index()
            metrics_b = predictions_df.loc[mask_b, ['fold', metric]].set_index('fold').sort_index()
            
            # Ensure same folds
            common_folds = metrics_a.index.intersection(metrics_b.index)
            
            if len(common_folds) < 2:
                logger.warning(f"Not enough common folds for {model_a} vs {model_b}")
                continue
            
            metrics_a = metrics_a.loc[common_folds]
            metrics_b = metrics_b.loc[common_folds]
            
            # Perform paired test
            comparison = perform_paired_ttest(
                metrics_a[metric],
                metrics_b[metric],
                alpha=alpha
            )
            
            # Add comparison details
            comparison['model_a'] = model_a
            comparison['model_b'] = model_b
            comparison['metric'] = metric
            
            results.append(comparison)
    
    if not results:
        return pd.DataFrame(columns=['model_a', 'model_b', 'metric', 'test_type', 'statistic', 'p_value', 'significant'])
    
    return pd.DataFrame(results)

def generate_report(
    comparison_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Generate a summary report of statistical comparisons.
    
    Args:
        comparison_df: DataFrame with comparison results
        output_path: Path to save the report CSV
    """
    if comparison_df.empty:
        logger.warning("No comparisons to report")
        # Create empty file with headers
        pd.DataFrame(columns=['fold', 'model', 'p_value', 'statistic']).to_csv(
            output_path, index=False
        )
        return
    
    # Format for output
    # The task requires schema: [fold, model, p_value, statistic]
    # We'll create a row for each model comparison
    output_rows = []
    
    for _, row in comparison_df.iterrows():
        # For each comparison, we record results for both models
        # We'll use the model_a as the primary model and note the comparison
        output_rows.append({
            'fold': 'all',  # Aggregated across folds
            'model': f"{row['model_a']} vs {row['model_b']}",
            'p_value': row['p_value'],
            'statistic': row['statistic']
        })
        
        # Also add the reverse comparison if needed
        # But typically we just need one row per pair
    
    output_df = pd.DataFrame(output_rows)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Statistical comparison report saved to {output_path}")

def main():
    """
    Main function to run statistical analysis on model predictions.
    
    This function:
    1. Loads predictions from data/processed/predictions.csv
    2. Calculates per-fold metrics
    3. Performs paired t-tests (with Wilcoxon fallback)
    4. Saves results to data/processed/statistical_comparison.csv
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    predictions_path = project_root / 'data' / 'processed' / 'predictions.csv'
    output_path = project_root / 'data' / 'processed' / 'statistical_comparison.csv'
    
    logger.info(f"Loading predictions from {predictions_path}")
    
    try:
        # Load predictions
        predictions_df = load_predictions(str(predictions_path))
        
        # Calculate fold metrics
        logger.info("Calculating fold metrics...")
        fold_metrics = calculate_fold_metrics(predictions_df)
        
        # Define models to compare
        models = predictions_df['model'].unique().tolist()
        
        if len(models) < 2:
            logger.warning("Less than 2 models found, cannot perform comparisons")
            # Create empty output
            pd.DataFrame(columns=['fold', 'model', 'p_value', 'statistic']).to_csv(
                output_path, index=False
            )
            return
        
        logger.info(f"Models to compare: {models}")
        
        # Run comparisons (default to R2)
        comparison_results = run_comparisons(
            fold_metrics,
            models=models,
            metric='r2',
            alpha=0.05
        )
        
        # Generate report
        logger.info(f"Saving statistical comparison to {output_path}")
        generate_report(comparison_results, str(output_path))
        
        # Also save detailed results for reference
        detailed_output = project_root / 'data' / 'processed' / 'statistical_comparison_detailed.csv'
        comparison_results.to_csv(detailed_output, index=False)
        logger.info(f"Detailed results saved to {detailed_output}")
        
        # Print summary
        print("\n" + "="*60)
        print("STATISTICAL COMPARISON SUMMARY")
        print("="*60)
        print(f"Test used: Paired t-test (alpha=0.05)")
        print("Wilcoxon signed-rank test used as fallback if normality fails.")
        print("-"*60)
        
        if not comparison_results.empty:
            for _, row in comparison_results.iterrows():
                sig_str = "SIGNIFICANT" if row['significant'] else "not significant"
                print(f"{row['model_a']} vs {row['model_b']}:")
                print(f"  Test: {row['test_type']}, p-value: {row['p_value']:.4f} ({sig_str})")
                print(f"  Statistic: {row['statistic']:.4f}")
                print()
        else:
            print("No comparisons were performed.")
        
        print("="*60)
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    main()

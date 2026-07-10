import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
import numpy as np

# Ensure project root is in path if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_null_metrics(file_path: Path) -> pd.DataFrame:
    """
    Load null model metrics from the specified CSV file.
    
    Args:
        file_path: Path to the null_model_metrics.csv file
        
    Returns:
        DataFrame containing null model metrics
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty or malformed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Null model metrics file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Null model metrics file is empty: {file_path}")
        
    # Validate expected columns
    required_cols = ['nutrient_condition', 'model_type', 'r2', 'mae', 'rmse']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Null model metrics file missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} null model metric records from {file_path}")
    return df

def load_trained_metrics(file_path: Path) -> pd.DataFrame:
    """
    Load trained model metrics from the specified CSV file.
    
    Args:
        file_path: Path to the model_metrics.csv file
        
    Returns:
        DataFrame containing trained model metrics
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty or malformed
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Trained model metrics file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Trained model metrics file is empty: {file_path}")
        
    # Validate expected columns
    required_cols = ['nutrient_condition', 'model_type', 'r2', 'mae', 'rmse']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Trained model metrics file missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} trained model metric records from {file_path}")
    return df

def compare_models(null_df: pd.DataFrame, trained_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare trained models against null models per nutrient condition.
    
    Calculates the performance improvement (delta) of trained models over null models.
    
    Args:
        null_df: DataFrame with null model metrics
        trained_df: DataFrame with trained model metrics
        
    Returns:
        DataFrame with comparison results including deltas and significance flags
    """
    comparison_results = []
    
    # Group by nutrient condition
    conditions = set(null_df['nutrient_condition'].unique()) | set(trained_df['nutrient_condition'].unique())
    
    for condition in sorted(conditions):
        null_subset = null_df[null_df['nutrient_condition'] == condition]
        trained_subset = trained_df[trained_df['nutrient_condition'] == condition]
        
        if null_subset.empty:
            logger.warning(f"No null model data for condition: {condition}")
            continue
            
        if trained_subset.empty:
            logger.warning(f"No trained model data for condition: {condition}")
            continue
        
        # Get null model baseline (average of null models for this condition)
        # Typically there's one null model per condition, but we handle multiple
        null_r2 = null_subset['r2'].mean()
        null_mae = null_subset['mae'].mean()
        null_rmse = null_subset['rmse'].mean()
        
        for _, trained_row in trained_subset.iterrows():
            model_type = trained_row['model_type']
            trained_r2 = trained_row['r2']
            trained_mae = trained_row['mae']
            trained_rmse = trained_row['rmse']
            
            # Calculate deltas (positive is better for R2, negative is better for MAE/RMSE)
            delta_r2 = trained_r2 - null_r2
            delta_mae = null_mae - trained_mae  # Inverted so positive is improvement
            delta_rmse = null_rmse - trained_rmse  # Inverted so positive is improvement
            
            # Determine if improvement is significant (arbitrary threshold: >0.01 for R2)
            r2_improved = delta_r2 > 0.01
            mae_improved = delta_mae > 0.01
            rmse_improved = delta_rmse > 0.01
            
            # Overall improvement flag
            overall_improved = r2_improved and mae_improved and rmse_improved
            
            comparison_results.append({
                'nutrient_condition': condition,
                'model_type': model_type,
                'null_r2': null_r2,
                'null_mae': null_mae,
                'null_rmse': null_rmse,
                'trained_r2': trained_r2,
                'trained_mae': trained_mae,
                'trained_rmse': trained_rmse,
                'delta_r2': delta_r2,
                'delta_mae': delta_mae,
                'delta_rmse': delta_rmse,
                'r2_improved': r2_improved,
                'mae_improved': mae_improved,
                'rmse_improved': rmse_improved,
                'overall_improved': overall_improved
            })
    
    comparison_df = pd.DataFrame(comparison_results)
    
    if not comparison_df.empty:
        logger.info(f"Generated comparison results for {len(comparison_df)} model-condition pairs")
        logger.info(f"Models showing overall improvement: {comparison_df['overall_improved'].sum()}")
    else:
        logger.warning("No comparison results generated - check data alignment")
        
    return comparison_df

def save_comparison_results(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save comparison results to CSV and generate a summary report.
    
    Args:
        df: Comparison results DataFrame
        output_path: Path to save the CSV file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save detailed results
    df.to_csv(output_path, index=False)
    logger.info(f"Saved comparison results to {output_path}")
    
    # Generate summary report
    summary_path = output_path.parent / "comparison_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("Model Comparison Summary Report\n")
        f.write("=" * 50 + "\n\n")
        
        if df.empty:
            f.write("No comparison results available.\n")
        else:
            f.write(f"Total comparisons: {len(df)}\n")
            f.write(f"Models outperforming null: {df['overall_improved'].sum()}\n\n")
            
            f.write("Performance by Nutrient Condition:\n")
            f.write("-" * 30 + "\n")
            
            for condition in df['nutrient_condition'].unique():
                cond_df = df[df['nutrient_condition'] == condition]
                f.write(f"\n{condition}:\n")
                f.write(f"  Null Model R2: {cond_df['null_r2'].iloc[0]:.4f}\n")
                f.write(f"  Best Trained R2: {cond_df['trained_r2'].max():.4f}\n")
                f.write(f"  Max R2 Improvement: {cond_df['delta_r2'].max():.4f}\n")
                f.write(f"  Models Improved: {cond_df['overall_improved'].sum()}/{len(cond_df)}\n")
            
            f.write("\nDetailed Results:\n")
            f.write("-" * 30 + "\n")
            for _, row in df.iterrows():
                status = "✓" if row['overall_improved'] else "✗"
                f.write(f"{status} {row['model_type']} ({row['nutrient_condition']}): "
                        f"R2 {row['trained_r2']:.4f} (delta: {row['delta_r2']:+.4f})\n")
    
    logger.info(f"Saved summary report to {summary_path}")

def main():
    """Main entry point for model comparison task."""
    parser = argparse.ArgumentParser(description="Compare trained models against null model baseline")
    parser.add_argument(
        "--null-metrics",
        type=str,
        default="data/processed/null_model_metrics.csv",
        help="Path to null model metrics CSV"
    )
    parser.add_argument(
        "--trained-metrics",
        type=str,
        default="data/processed/model_metrics.csv",
        help="Path to trained model metrics CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/model_comparison.csv",
        help="Path to save comparison results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        # Load data
        null_path = Path(args.null_metrics)
        trained_path = Path(args.trained_metrics)
        output_path = Path(args.output)
        
        logger.info(f"Loading null model metrics from {null_path}")
        null_df = load_null_metrics(null_path)
        
        logger.info(f"Loading trained model metrics from {trained_path}")
        trained_df = load_trained_metrics(trained_path)
        
        # Compare models
        logger.info("Comparing models against null baseline")
        comparison_df = compare_models(null_df, trained_df)
        
        # Save results
        logger.info(f"Saving comparison results to {output_path}")
        save_comparison_results(comparison_df, output_path)
        
        logger.info("Model comparison completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during comparison: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Data Aggregation Module for Plant Defense Compound Project.

Implements condition-level aggregation to handle pairing rates < 95%.
Averages replicates within the same experimental condition to create
aggregated expression and metabolite matrices.
"""
import json
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_aggregation.log')
    ]
)
logger = logging.getLogger(__name__)

# Project paths relative to root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_PAIRED_DIR = PROJECT_ROOT / "data" / "paired"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_pairing_report() -> Dict[str, Any]:
    """Load the pairing report from T007."""
    report_path = DATA_PAIRED_DIR / "pairing_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Pairing report not found at {report_path}. "
                              "Run T007 first.")
    
    with open(report_path, 'r') as f:
        return json.load(f)

def load_expression_matrix() -> pd.DataFrame:
    """Load the expression matrix from T028 (or intermediate raw data)."""
    # Try to load the processed expression matrix first
    expr_path = DATA_PROCESSED_DIR / "expression_matrix.csv"
    if expr_path.exists():
        logger.info(f"Loading expression matrix from {expr_path}")
        return pd.read_csv(expr_path)
    
    # Fallback: try to load raw GEO data if processed doesn't exist
    # This handles cases where T028 hasn't run yet
    logger.warning("Expression matrix not found, attempting to load raw GEO data...")
    # In a real implementation, this would parse the raw GEO files
    # For now, we'll raise an error if neither exists
    raise FileNotFoundError("No expression matrix found. Ensure T028 has run or raw GEO data is available.")

def load_metabolite_matrix() -> pd.DataFrame:
    """Load the metabolite matrix from T029 (or intermediate raw data)."""
    # Try to load the processed metabolite matrix first
    metab_path = DATA_PROCESSED_DIR / "metabolite_matrix.csv"
    if metab_path.exists():
        logger.info(f"Loading metabolite matrix from {metab_path}")
        return pd.read_csv(metab_path)
    
    # Fallback: try to load raw MW data if processed doesn't exist
    logger.warning("Metabolite matrix not found, attempting to load raw MW data...")
    # In a real implementation, this would parse the raw MW files
    raise FileNotFoundError("No metabolite matrix found. Ensure T029 has run or raw MW data is available.")

def extract_condition_key(row: pd.Series, condition_cols: List[str]) -> str:
    """Extract a condition key from a row based on specified columns."""
    return "_".join(str(row[col]) for col in condition_cols if col in row.index)

def aggregate_by_condition(df: pd.DataFrame, 
                         condition_cols: List[str],
                         sample_id_col: str = 'sample_id') -> pd.DataFrame:
    """
    Aggregate data by experimental condition.
    
    Args:
        df: Input DataFrame with sample data
        condition_cols: Columns that define the experimental condition
        sample_id_col: Column name for sample identifiers
    
    Returns:
        Aggregated DataFrame with condition-level averages
    """
    if df.empty:
        logger.warning("Input DataFrame is empty")
        return df

    # Ensure condition columns exist
    missing_cols = [col for col in condition_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing condition columns: {missing_cols}. Using available columns.")
        condition_cols = [col for col in condition_cols if col in df.columns]
    
    if not condition_cols:
        raise ValueError("No valid condition columns found for aggregation")

    # Create condition keys
    df['condition_key'] = df.apply(lambda row: extract_condition_key(row, condition_cols), axis=1)
    
    # Identify numeric columns for aggregation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols and col != 'condition_key']
    
    # Group by condition and aggregate
    # For numeric columns: mean
    # For non-numeric columns: take first value (or most common)
    agg_dict = {col: 'mean' for col in numeric_cols}
    for col in non_numeric_cols:
        if col != 'condition_key':
            agg_dict[col] = 'first'  # Take first value for categorical columns
    
    aggregated = df.groupby('condition_key').agg(agg_dict).reset_index()
    
    # Remove the condition_key column if it's not needed in output
    # or keep it as a composite identifier
    if 'condition_key' in aggregated.columns:
        # Split condition_key back into original columns
        for i, col in enumerate(condition_cols):
            aggregated[col] = aggregated['condition_key'].apply(lambda x: x.split('_')[i] if len(x.split('_')) > i else '')
        aggregated = aggregated.drop('condition_key', axis=1)
    
    logger.info(f"Aggregated {len(df)} samples into {len(aggregated)} conditions")
    return aggregated

def update_pairing_report(pairing_report: Dict[str, Any], 
                        original_pairing_rate: float,
                        aggregated_expression_count: int,
                        aggregated_metabolite_count: int,
                        pairing_rate_after_aggregation: float) -> Dict[str, Any]:
    """Update the pairing report with aggregation fallback status."""
    pairing_report['aggregation_fallback'] = {
        'attempted': True,
        'reason': f'Original pairing rate {original_pairing_rate:.2%} < 95%',
        'original_pairing_rate': original_pairing_rate,
        'aggregated_expression_samples': aggregated_expression_count,
        'aggregated_metabolite_samples': aggregated_metabolite_count,
        'pairing_rate_after_aggregation': pairing_rate_after_aggregation,
        'status': 'completed' if pairing_rate_after_aggregation >= 0.95 else 'insufficient'
    }
    
    # Update overall status
    if pairing_rate_after_aggregation >= 0.95:
        pairing_report['status'] = 'passed_after_aggregation'
        pairing_report['final_pairing_rate'] = pairing_rate_after_aggregation
    else:
        pairing_report['status'] = 'failed_after_aggregation'
        pairing_report['final_pairing_rate'] = pairing_rate_after_aggregation
    
    return pairing_report

def calculate_pairing_rate(expression_df: pd.DataFrame, 
                         metabolite_df: pd.DataFrame,
                         sample_id_col: str = 'sample_id') -> float:
    """Calculate the pairing rate between expression and metabolite data."""
    expression_samples = set(expression_df[sample_id_col].unique())
    metabolite_samples = set(metabolite_df[sample_id_col].unique())
    
    paired_samples = expression_samples.intersection(metabolite_samples)
    total_samples = expression_samples.union(metabolite_samples)
    
    if len(total_samples) == 0:
        return 0.0
    
    return len(paired_samples) / len(total_samples)

def main():
    """Main function to perform condition-level aggregation."""
    logger.info("Starting condition-level aggregation for T008a")
    
    try:
        # Load pairing report to check if aggregation is needed
        pairing_report = load_pairing_report()
        
        # Check if original pairing rate was already >= 95%
        original_rate = pairing_report.get('pairing_rate', 1.0)
        if original_rate >= 0.95:
            logger.info(f"Pairing rate {original_rate:.2%} >= 95%. Aggregation not needed.")
            # Still create empty aggregated files to satisfy task requirements
            # But mark that aggregation wasn't actually performed
            empty_expr = pd.DataFrame(columns=['sample_id'])
            empty_metab = pd.DataFrame(columns=['sample_id'])
            empty_expr.to_csv(DATA_PROCESSED_DIR / "aggregated_expression.csv", index=False)
            empty_metab.to_csv(DATA_PROCESSED_DIR / "aggregated_metabolite.csv", index=False)
            
            pairing_report['aggregation_fallback'] = {
                'attempted': False,
                'reason': 'Original pairing rate >= 95%',
                'status': 'not_needed'
            }
            
            with open(DATA_PAIRED_DIR / "pairing_report.json", 'w') as f:
                json.dump(pairing_report, f, indent=2)
            
            logger.info("Aggregation skipped, pairing report updated")
            return

        logger.info(f"Pairing rate {original_rate:.2%} < 95%. Performing aggregation...")
        
        # Load data matrices
        expression_df = load_expression_matrix()
        metabolite_df = load_metabolite_matrix()
        
        logger.info(f"Loaded expression matrix: {len(expression_df)} samples")
        logger.info(f"Loaded metabolite matrix: {len(metabolite_df)} samples")
        
        # Define condition columns (these would be determined from metadata)
        # For now, we'll use common experimental condition columns
        condition_cols = ['condition', 'treatment', 'time_point']
        
        # Aggregate expression data by condition
        aggregated_expression = aggregate_by_condition(
            expression_df, 
            condition_cols,
            sample_id_col='sample_id'
        )
        
        # Aggregate metabolite data by condition
        aggregated_metabolite = aggregate_by_condition(
            metabolite_df,
            condition_cols,
            sample_id_col='sample_id'
        )
        
        # Save aggregated matrices
        aggregated_expression.to_csv(
            DATA_PROCESSED_DIR / "aggregated_expression.csv", 
            index=False
        )
        aggregated_metabolite.to_csv(
            DATA_PROCESSED_DIR / "aggregated_metabolite.csv", 
            index=False
        )
        
        logger.info(f"Saved aggregated expression matrix: {len(aggregated_expression)} conditions")
        logger.info(f"Saved aggregated metabolite matrix: {len(aggregated_metabolite)} conditions")
        
        # Calculate new pairing rate after aggregation
        new_pairing_rate = calculate_pairing_rate(
            aggregated_expression,
            aggregated_metabolite,
            sample_id_col='sample_id'
        )
        
        logger.info(f"New pairing rate after aggregation: {new_pairing_rate:.2%}")
        
        # Update pairing report
        updated_report = update_pairing_report(
            pairing_report,
            original_rate,
            len(aggregated_expression),
            len(aggregated_metabolite),
            new_pairing_rate
        )
        
        # Save updated report
        with open(DATA_PAIRED_DIR / "pairing_report.json", 'w') as f:
            json.dump(updated_report, f, indent=2)
        
        logger.info("Pairing report updated with aggregation results")
        
        # Log summary
        logger.info("=" * 50)
        logger.info("AGGREGATION SUMMARY")
        logger.info(f"Original pairing rate: {original_rate:.2%}")
        logger.info(f"Aggregated expression conditions: {len(aggregated_expression)}")
        logger.info(f"Aggregated metabolite conditions: {len(aggregated_metabolite)}")
        logger.info(f"New pairing rate: {new_pairing_rate:.2%}")
        logger.info(f"Status: {'PASSED' if new_pairing_rate >= 0.95 else 'FAILED'}")
        logger.info("=" * 50)
        
        if new_pairing_rate < 0.95:
            logger.warning("Pairing rate still below 95% after aggregation. T008b will abort pipeline.")
        
    except Exception as e:
        logger.error(f"Aggregation failed: {str(e)}", exc_info=True)
        # Update report with failure status
        try:
            pairing_report['aggregation_fallback'] = {
                'attempted': True,
                'status': 'failed',
                'error': str(e)
            }
            with open(DATA_PAIRED_DIR / "pairing_report.json", 'w') as f:
                json.dump(pairing_report, f, indent=2)
        except:
            pass
        raise

if __name__ == "__main__":
    main()

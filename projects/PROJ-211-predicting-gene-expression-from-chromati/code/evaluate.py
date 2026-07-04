import os
import sys
import logging
import argparse
import json
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/evaluate.log')
    ]
)
logger = logging.getLogger(__name__)

def load_predictions(model_path: str) -> pd.DataFrame:
    """
    Load predicted expression values from a trained model's output file.
    Expects a CSV with columns: gene_id, cell_line, predicted_expression
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Predictions file not found: {model_path}")
    df = pd.read_csv(model_path)
    required_cols = {'gene_id', 'cell_line', 'predicted_expression'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Predictions file missing required columns: {required_cols - set(df.columns)}")
    return df

def load_actuals(data_path: str) -> pd.DataFrame:
    """
    Load actual expression values from processed data.
    Expects a CSV with gene_id, cell_line, and expression columns.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Actuals file not found: {data_path}")
    df = pd.read_csv(data_path)
    # Normalize column names if necessary
    if 'expression' not in df.columns and 'actual_expression' in df.columns:
        df = df.rename(columns={'actual_expression': 'expression'})
    if 'gene_id' not in df.columns or 'cell_line' not in df.columns or 'expression' not in df.columns:
        raise ValueError("Actuals file must contain 'gene_id', 'cell_line', and 'expression' columns")
    return df

def load_gene_list(path: str) -> List[str]:
    """
    Load a list of gene IDs from a CSV or text file.
    Expects a single column named 'gene_id' or just a list of gene IDs.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Gene list file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(path)
        if 'gene_id' in df.columns:
            genes = df['gene_id'].tolist()
        elif len(df.columns) == 1:
            genes = df.iloc[:, 0].tolist()
        else:
            raise ValueError(f"Gene list file {path} must have a 'gene_id' column or be a single column file")
    elif ext in ['.txt', '.tsv']:
        with open(path, 'r') as f:
            genes = [line.strip() for line in f if line.strip()]
    else:
        raise ValueError(f"Unsupported file format for gene list: {ext}")
    return genes

def calculate_correlation_matrix(predictions: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Pearson correlation between predicted and actual expression per cell line.
    """
    merged = pd.merge(predictions, actuals, on=['gene_id', 'cell_line'], suffixes=('_pred', '_actual'))
    if merged.empty:
        logger.warning("No matching records found between predictions and actuals.")
        return pd.DataFrame()
    
    correlations = []
    for cell_line in merged['cell_line'].unique():
        subset = merged[merged['cell_line'] == cell_line]
        if len(subset) < 2:
            logger.warning(f"Not enough data points for correlation in {cell_line}")
            continue
        corr = subset['predicted_expression'].corr(subset['expression'])
        correlations.append({'cell_line': cell_line, 'correlation': corr})
    
    return pd.DataFrame(correlations)

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    corrected = [min(p * n_tests, 1.0) for p in p_values]
    return corrected

def calculate_r2_for_gene_category(predictions: pd.DataFrame, actuals: pd.DataFrame, gene_list: List[str]) -> float:
    """
    Calculate R² score for a specific category of genes.
    """
    gene_set = set(gene_list)
    merged = pd.merge(predictions, actuals, on=['gene_id', 'cell_line'], suffixes=('_pred', '_actual'))
    filtered = merged[merged['gene_id'].isin(gene_set)]
    
    if len(filtered) == 0:
        logger.warning(f"No matching genes found for category. Returning NaN.")
        return float('nan')
    
    y_true = filtered['expression'].values
    y_pred = filtered['predicted_expression'].values
    
    return r2_score(y_true, y_pred)

def run_external_validation(
    train_predictions: pd.DataFrame,
    train_actuals: pd.DataFrame,
    test_predictions: pd.DataFrame,
    test_actuals: pd.DataFrame,
    housekeeping_genes: List[str],
    cell_type_specific_genes: List[str],
    output_path: str
) -> Dict[str, float]:
    """
    Perform external validation: train on a subset of cell lines, test on a held-out cell line.
    This function assumes the model was already trained (predictions exist) and validates
    the generalization performance on a held-out cell line for specific gene categories.
    
    FR-014: External validation
    SC-006: Validate generalization to unseen cell types
    """
    logger.info("Starting external validation...")
    
    # Determine the held-out cell line (the one present in test but not in train)
    train_lines = set(train_predictions['cell_line'].unique())
    test_lines = set(test_predictions['cell_line'].unique())
    held_out_lines = test_lines - train_lines
    
    if not held_out_lines:
        # Fallback: if no explicit held-out line, assume the last one in test is the target
        # But strictly, external validation implies training on one set, testing on a disjoint set.
        logger.warning("No disjoint cell lines found between train and test sets. Using all test lines as held-out.")
        held_out_lines = test_lines
    
    results = {}
    
    for held_out_line in held_out_lines:
        logger.info(f"Validating on held-out cell line: {held_out_line}")
        
        # Filter data for the held-out line
        test_subset = test_predictions[test_predictions['cell_line'] == held_out_line]
        test_actual_subset = test_actuals[test_actuals['cell_line'] == held_out_line]
        
        if test_subset.empty or test_actual_subset.empty:
            logger.warning(f"No data for held-out line {held_out_line}, skipping.")
            continue
        
        # Calculate R² for Housekeeping Genes
        hk_r2 = calculate_r2_for_gene_category(
            test_subset, test_actual_subset, housekeeping_genes
        )
        results[f"{held_out_line}_housekeeping_r2"] = hk_r2
        logger.info(f"  Housekeeping Genes R²: {hk_r2:.4f}")
        
        # Calculate R² for Cell-Type Specific Genes
        cts_r2 = calculate_r2_for_gene_category(
            test_subset, test_actual_subset, cell_type_specific_genes
        )
        results[f"{held_out_line}_cell_type_specific_r2"] = cts_r2
        logger.info(f"  Cell-Type Specific Genes R²: {cts_r2:.4f}")
        
        # Overall R² for the held-out line (all genes)
        overall_r2 = calculate_r2_for_gene_category(
            test_subset, test_actual_subset, list(set(test_subset['gene_id']))
        )
        results[f"{held_out_line}_overall_r2"] = overall_r2
        logger.info(f"  Overall R²: {overall_r2:.4f}")
    
    # Save results to CSV
    df_results = pd.DataFrame([results])
    df_results.to_csv(output_path, index=False)
    logger.info(f"External validation results saved to {output_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate model performance and run external validation")
    parser.add_argument('--train-pred', type=str, required=True, help="Path to training predictions CSV")
    parser.add_argument('--train-actual', type=str, required=True, help="Path to training actuals CSV")
    parser.add_argument('--test-pred', type=str, required=True, help="Path to test (held-out) predictions CSV")
    parser.add_argument('--test-actual', type=str, required=True, help="Path to test (held-out) actuals CSV")
    parser.add_argument('--housekeeping', type=str, required=True, help="Path to housekeeping genes list")
    parser.add_argument('--cell-type-specific', type=str, required=True, help="Path to cell-type-specific genes list")
    parser.add_argument('--output', type=str, default='data/processed/external_validation_r2.csv', help="Output path for results")
    
    args = parser.parse_args()
    
    try:
        # Load data
        logger.info("Loading data...")
        train_pred = load_predictions(args.train_pred)
        train_actual = load_actuals(args.train_actual)
        test_pred = load_predictions(args.test_pred)
        test_actual = load_actuals(args.test_actual)
        
        housekeeping_genes = load_gene_list(args.housekeeping)
        cell_type_specific_genes = load_gene_list(args.cell_type_specific)
        
        # Run validation
        run_external_validation(
            train_pred, train_actual,
            test_pred, test_actual,
            housekeeping_genes, cell_type_specific_genes,
            args.output
        )
        
        logger.info("External validation completed successfully.")
        
    except Exception as e:
        logger.error(f"External validation failed: {e}")
        raise

if __name__ == "__main__":
    main()
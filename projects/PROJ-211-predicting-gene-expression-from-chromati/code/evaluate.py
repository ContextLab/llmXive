import os
import sys
import logging
import argparse
import json
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.metrics import r2_score

# Import shared utilities
from utils import checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(cell_line: str, model_dir: str = "data/models") -> pd.DataFrame:
    """
    Load predicted expression values for a specific cell line.
    Expects a CSV file named 'predictions_{cell_line}.csv' with columns: gene_id, predicted.
    """
    path = os.path.join(model_dir, f"predictions_{cell_line}.csv")
    if not os.path.exists(path):
        # Fallback to model output if prediction file doesn't exist yet (train.py might output directly)
        # Assuming train.py might output 'predictions_{cell_line}.csv' or we need to generate from model
        # For this task, we assume the training pipeline (T021) produced this file.
        raise FileNotFoundError(f"Predictions file not found: {path}")
    
    df = pd.read_csv(path)
    return df

def load_actuals(cell_line: str, data_dir: str = "data/processed") -> pd.DataFrame:
    """
    Load actual (imputed) expression values for a specific cell line.
    Expects 'imputed_expression.csv' with cell lines as columns or rows.
    Assuming format from T014: rows=genes, columns=cell_lines (or similar).
    We need to match the index of predictions.
    """
    path = os.path.join(data_dir, "imputed_expression.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Actuals file not found: {path}")
    
    df = pd.read_csv(path)
    # Normalize column names if necessary
    if cell_line not in df.columns:
        # Check if cell_line is in index
        if cell_line in df.index:
            actuals = df.loc[cell_line].to_frame().T
        else:
            raise ValueError(f"Cell line '{cell_line}' not found in actuals data columns or index.")
    else:
        actuals = df[[cell_line]]
    return actuals

def load_gene_list(path: str) -> List[str]:
    """Load a list of gene IDs from a CSV file (assumed single column 'gene_id')."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Gene list file not found: {path}")
    df = pd.read_csv(path)
    # Handle potential column name variations
    col_name = df.columns[0]
    return df[col_name].tolist()

def calculate_correlation_matrix(predictions_path: str, actuals_path: str, output_path: str) -> pd.DataFrame:
    """
    Calculate Pearson correlation between predicted and actual expression for each cell line.
    Inputs:
      - predictions_path: CSV with columns [gene_id, predicted] (or multiple predicted columns per cell line)
      - actuals_path: CSV with gene_id and actual values
    Output:
      - DataFrame with cell_line, correlation, p_value
    """
    logger.info(f"Loading predictions from {predictions_path}")
    preds_df = pd.read_csv(predictions_path)
    
    logger.info(f"Loading actuals from {actuals_path}")
    actuals_df = pd.read_csv(actuals_path)

    # Ensure both have gene_id for merging
    if 'gene_id' not in preds_df.columns:
        # Try to infer if index is gene_id
        if 'index' in preds_df.columns:
            preds_df.rename(columns={'index': 'gene_id'}, inplace=True)
        else:
            # Assume first column is gene_id if unnamed
            preds_df.rename(columns={preds_df.columns[0]: 'gene_id'}, inplace=True)
    
    if 'gene_id' not in actuals_df.columns:
        if 'index' in actuals_df.columns:
            actuals_df.rename(columns={'index': 'gene_id'}, inplace=True)
        else:
            actuals_df.rename(columns={actuals_df.columns[0]: 'gene_id'}, inplace=True)

    # Identify cell lines. 
    # Case A: Predictions file has one row per gene, multiple columns for cell lines.
    # Case B: Predictions file has one row per gene per cell line (long format).
    
    # We assume the standard format from training: 
    # predictions_{cell_line}.csv might be separate, OR a single file with all predictions.
    # Let's handle the case where we are given a single predictions file with columns: gene_id, cell_line, predicted
    # OR a wide format: gene_id, GM12878_pred, K562_pred...
    
    # Strategy: If 'cell_line' column exists, use long format. Else, assume wide format where columns ending in '_pred' or matching cell lines exist.
    # However, T021 produces separate models. T023 task says "Calculate Pearson correlation...".
    # Let's assume the input to this function is a single merged file or we iterate over known cell lines.
    
    # Simpler approach for this specific task implementation:
    # We expect `predictions_{cell_line}.csv` files in `data/models` and `imputed_expression.csv` in `data/processed`.
    # We will iterate over cell lines found in the predictions directory.
    
    model_dir = os.path.dirname(predictions_path)
    # Extract cell lines from filenames like predictions_GM12878.csv
    cell_lines = [f.replace("predictions_", "").replace(".csv", "") for f in os.listdir(model_dir) if f.startswith("predictions_")]
    
    results = []
    
    for cell_line in cell_lines:
        pred_file = os.path.join(model_dir, f"predictions_{cell_line}.csv")
        if not os.path.exists(pred_file):
            logger.warning(f"Skipping {cell_line}: predictions file missing.")
            continue

        p_df = pd.read_csv(pred_file)
        # Ensure gene_id column
        if 'gene_id' not in p_df.columns:
            p_df['gene_id'] = p_df.index
        
        # Get actuals
        a_df = pd.read_csv(actuals_path)
        if 'gene_id' not in a_df.columns:
            a_df['gene_id'] = a_df.index
        
        # Merge on gene_id
        merged = pd.merge(p_df, a_df, on='gene_id', suffixes=('_pred', '_actual'))
        
        if merged.empty:
            logger.warning(f"No overlapping genes for {cell_line}.")
            continue

        # Identify actual column. It should be the cell line name column in the actuals file
        # If actuals file is wide (gene_id, GM12878, K562...), the column is cell_line
        actual_col = cell_line
        if actual_col not in merged.columns:
            # Try to find a column that matches
            matches = [c for c in merged.columns if c == cell_line or c.endswith(cell_line)]
            if matches:
                actual_col = matches[0]
            else:
                logger.error(f"Could not find actual column '{cell_line}' in merged data for {cell_line}. Columns: {merged.columns.tolist()}")
                continue

        pred_col = [c for c in merged.columns if c.endswith('_pred')][0]
        
        # Remove NaNs
        clean = merged[[pred_col, actual_col]].dropna()
        
        if len(clean) < 2:
            logger.warning(f"Not enough data points for correlation in {cell_line}.")
            continue

        corr, p_val = stats.pearsonr(clean[pred_col], clean[actual_col])
        
        results.append({
            'cell_line': cell_line,
            'pearson_correlation': corr,
            'p_value': p_val,
            'n_samples': len(clean)
        })
        logger.info(f"Calculated correlation for {cell_line}: {corr:.4f} (p={p_val:.2e})")

    result_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation matrix to {output_path}")
    
    return result_df

def apply_bonferroni_correction(pvalues_path: str, output_path: str) -> pd.DataFrame:
    """
    Apply Bonferroni correction to p-values.
    Input: CSV with 'p_value' column.
    Output: CSV with 'p_value_corrected' column.
    """
    df = pd.read_csv(pvalues_path)
    n_tests = len(df)
    if n_tests == 0:
        logger.warning("No p-values to correct.")
        return pd.DataFrame()

    df['p_value_corrected'] = df['p_value'] * n_tests
    df['p_value_corrected'] = df['p_value_corrected'].clip(upper=1.0)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved corrected p-values to {output_path}")
    return df

def calculate_r2_for_gene_category(predictions_path: str, actuals_path: str, gene_list_path: str, output_path: str) -> pd.DataFrame:
    """
    Calculate R2 for a specific gene category (e.g., housekeeping).
    """
    # Load gene list
    genes = load_gene_list(gene_list_path)
    
    # Load predictions and actuals
    preds_df = pd.read_csv(predictions_path)
    actuals_df = pd.read_csv(actuals_path)
    
    # Filter for genes in list
    # Assuming gene_id column exists
    preds_df = preds_df[preds_df['gene_id'].isin(genes)]
    actuals_df = actuals_df[actuals_df['gene_id'].isin(genes)]
    
    if preds_df.empty or actuals_df.empty:
        logger.warning(f"No overlapping genes for category at {gene_list_path}")
        return pd.DataFrame()
    
    # Merge
    merged = pd.merge(preds_df, actuals_df, on='gene_id')
    # Identify columns (assuming wide format or specific naming)
    # This function is generic, but for T025 we need to know which columns to use.
    # We will assume the input files are already filtered to the specific cell line and gene set.
    # If multiple cell lines exist, this function should be called per cell line.
    
    # Simplified: Assume the input files contain only the relevant cell line data.
    pred_col = [c for c in merged.columns if 'pred' in c][0]
    actual_col = [c for c in merged.columns if 'actual' in c or c not in ['gene_id', 'pred']][0]
    
    y_true = merged[actual_col]
    y_pred = merged[pred_col]
    
    r2 = r2_score(y_true, y_pred)
    
    df = pd.DataFrame({'r2': [r2], 'n_genes': [len(merged)]})
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved R2 for category to {output_path}")
    return df

def run_external_validation(train_cell_lines: List[str], test_cell_line: str, data_dir: str = "data/processed", model_dir: str = "data/models", output_path: str = "data/processed/external_validation_r2.csv"):
    """
    Train on multiple cell lines, test on held-out cell line.
    For T026, we assume the model is already trained (T021) and we just evaluate.
    Here we calculate R2 for the held-out line.
    """
    # Load actuals for test line
    actuals_path = os.path.join(data_dir, "imputed_expression.csv")
    preds_path = os.path.join(model_dir, f"predictions_{test_cell_line}.csv")
    
    if not os.path.exists(preds_path):
        logger.error(f"Predictions for held-out line {test_cell_line} not found.")
        return None

    r2_df = calculate_r2_for_gene_category(
        predictions_path=preds_path,
        actuals_path=actuals_path,
        gene_list_path=None, # Use all genes
        output_path=output_path
    )
    return r2_df

def main():
    parser = argparse.ArgumentParser(description="Evaluate model predictions.")
    parser.add_argument("--predictions_dir", type=str, default="data/models", help="Directory containing prediction CSVs.")
    parser.add_argument("--actuals_file", type=str, default="data/processed/imputed_expression.csv", help="Path to actual expression CSV.")
    parser.add_argument("--output_file", type=str, default="data/processed/correlations.csv", help="Output path for correlation matrix.")
    args = parser.parse_args()

    logger.info("Starting evaluation task T023.")
    
    # Check inputs
    if not os.path.exists(args.actuals_file):
        logger.error(f"Actuals file not found: {args.actuals_file}. Please run preprocessing tasks first.")
        sys.exit(1)
    
    if not os.path.exists(args.predictions_dir):
        logger.error(f"Predictions directory not found: {args.predictions_dir}. Please run training tasks first.")
        sys.exit(1)

    # Calculate correlations
    corr_df = calculate_correlation_matrix(args.predictions_dir, args.actuals_file, args.output_file)
    
    # Apply checksum
    checksum_file(args.output_file)
    
    logger.info("Task T023 completed successfully.")

if __name__ == "__main__":
    main()

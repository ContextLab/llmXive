import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import pickle
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

# Ensure project root is in path for imports if running as script
if 'code' not in sys.path:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(project_root, 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)

from utils import load_config, checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '..', 'logs', 'training.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
ALPHA = 0.5
L1_RATIO = 0.5  # Corresponds to alpha=0.5 in sklearn's ElasticNet (l1_ratio)
N_FOLDS = 5

def load_variable_peaks(input_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the imputed expression matrix and separates features (peaks) from targets (genes).
    Assumes the input CSV has a specific structure where the first column is Gene ID,
    and subsequent columns are cell lines or peak features.
    
    Based on T014 output: 'data/processed/imputed_expression.csv'.
    The schema implies rows are genes, columns are features (peaks) for specific cell lines?
    Or is it a wide matrix of (Gene x Peak_Features)?
    
    Given the task "Train Elastic Net... for each cell line", the input likely needs to be
    reshaped or split by cell line if it's a combined matrix.
    
    However, looking at T014 output: `data/processed/imputed_expression.csv`.
    And T016c: `data/processed/housekeeping_matrix.csv`.
    
    Assumption for this implementation:
    The input file `imputed_expression.csv` contains rows as Genes and columns as 
    aggregated accessibility features (Peaks) for a specific cell line context, 
    OR it is a wide table where columns are named `<cellline>_<peak_id>`.
    
    To support "each cell line", we assume the input file has a MultiIndex or 
    columns that can be grouped by cell line. 
    
    Simplified Assumption for T021 based on standard pipelines:
    The input `imputed_expression.csv` has:
    - Index: Gene IDs
    - Columns: Peak IDs (aggregated features). 
    - BUT we need to train per cell line.
    
    Correction: The task says "Input: data/processed/imputed_expression.csv".
    If the previous step (T014) produced a single matrix, it likely contains 
    features for ALL cell lines or a specific subset. 
    
    Let's assume the input file structure is:
    Gene_ID, CellLine1_Peak1, CellLine1_Peak2, ..., CellLine2_Peak1, ...
    OR
    Gene_ID, Peak1, Peak2, ... (and we need to filter by cell line metadata).
    
    Given the ambiguity, we will implement a robust loader that:
    1. Loads the CSV.
    2. Checks for a 'CellLine' column or infers from column names.
    3. If columns are named `CellLine_PeakID`, we split them.
    4. If the file is just one big matrix, we might need to assume the user 
       has pre-split it or the task implies training on the whole set if 
       "cell line" is a feature.
    
    CRITICAL: The task says "for each cell line".
    We will assume the input `imputed_expression.csv` has columns formatted as 
    `{cell_line}_{peak_id}`. We will group columns by the prefix before the last underscore.
    
    If that fails, we fallback to treating the whole matrix as one if only one cell line is present.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Input file {input_path} is empty.")
    
    # Identify the ID column (usually the first one)
    id_col = df.columns[0]
    features_df = df.drop(columns=[id_col])
    gene_ids = df[id_col]
    
    # Attempt to split by cell line based on column naming convention
    # Expected: "GM12878_peak_1", "K562_peak_2", etc.
    cell_line_features = {}
    
    # Check if columns contain underscores that separate cell line from peak
    # We look for a common pattern. If all columns belong to one cell line, 
    # the prefix might be the same.
    
    prefixes = set()
    for col in features_df.columns:
        parts = col.rsplit('_', 1)
        if len(parts) == 2:
            prefixes.add(parts[0])
        else:
            prefixes.add("unknown")
    
    # If we have multiple distinct prefixes, split by them
    if len(prefixes) > 1:
        for prefix in prefixes:
            if prefix == "unknown":
                continue
            cols = [c for c in features_df.columns if c.startswith(f"{prefix}_")]
            if cols:
                cell_line_features[prefix] = features_df[cols]
    else:
        # Fallback: If only one prefix or no underscore pattern, assume the whole matrix
        # is for a single cell line, or the prefix is the column name itself?
        # If the input is just one cell line, we use it.
        # If the input is mixed but no pattern, we can't split.
        # We'll assume the first prefix found is the cell line name if unique.
        if len(prefixes) == 1 and list(prefixes)[0] != "unknown":
            cell_line_features[list(prefixes)[0]] = features_df
        else:
            # Last resort: treat the whole thing as one dataset (maybe the file is already split by user)
            # But the task requires "each cell line".
            # We will raise an error if we can't determine cell lines.
            raise ValueError(f"Could not determine cell lines from column names. Found prefixes: {prefixes}. "
                             f"Expected format: {{cell_line}}_{{peak_id}}")

    return gene_ids, cell_line_features

def train_elastic_net(X: np.ndarray, y: np.ndarray, l1_ratio: float = L1_RATIO) -> ElasticNet:
    """
    Trains an Elastic Net model with internal cross-validation for lambda selection.
    Sklearn's ElasticNetCV does this automatically.
    """
    # Use ElasticNetCV to find best alpha (lambda) via CV
    # l1_ratio is fixed at 0.5 (alpha=0.5 in task description maps to l1_ratio in sklearn)
    # Note: Task says "alpha=0.5, lambda via internal k-fold". 
    # In sklearn: ElasticNet(alpha=..., l1_ratio=...). 
    # "alpha" in task usually refers to the regularization strength (lambda).
    # "l1_ratio" is the mixing parameter (0.5 for Elastic Net).
    # We will use ElasticNetCV to search for the best regularization strength.
    
    model = ElasticNetCV(
        l1_ratio=l1_ratio,
        cv=N_FOLDS,
        random_state=42,
        n_jobs=-1,
        max_iter=10000
    )
    model.fit(X, y)
    return model

def run_cross_validation(X: np.ndarray, y: np.ndarray, l1_ratio: float = L1_RATIO) -> Dict[str, Any]:
    """
    Runs cross-validation to evaluate the model performance before final training.
    Returns scores and best alpha.
    """
    model = ElasticNetCV(
        l1_ratio=l1_ratio,
        cv=N_FOLDS,
        random_state=42,
        n_jobs=-1,
        max_iter=10000
    )
    model.fit(X, y)
    
    scores = model.cv_results_['mean_test_score']
    best_alpha = model.alpha_
    
    return {
        "mean_scores": scores.tolist(),
        "best_alpha": float(best_alpha),
        "mean_cv_score": float(np.mean(scores)),
        "std_cv_score": float(np.std(scores))
    }

def train_all_cell_lines(input_path: str, output_model_dir: str, output_scores_path: str):
    """
    Main orchestration function to train models for each cell line.
    """
    os.makedirs(output_model_dir, exist_ok=True)
    
    logger.info(f"Starting training pipeline for {input_path}")
    
    try:
        gene_ids, cell_line_features = load_variable_peaks(input_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    all_cv_scores = {}

    for cell_line, features in cell_line_features.items():
        logger.info(f"Processing cell line: {cell_line}")
        
        # Prepare X and y
        # X: Accessibility features (Peaks)
        # y: Gene Expression (Target)
        # The input file has Genes as rows. So X is (n_genes, n_peaks), y is (n_genes,)
        # Wait, the input `imputed_expression.csv` is likely:
        # Rows = Genes, Columns = Features (Peaks).
        # So X = features.values, y = gene_ids? No, gene_ids are labels.
        # We need a target vector.
        # Re-reading T014: "impute missing values... per peak".
        # This implies the matrix is Genes x Peaks.
        # But we need to predict Expression from Accessibility.
        # If the file is Genes x Peaks, where is the Expression?
        # Ah, T013: "filter genes... log pseudocount".
        # T014: "impute... per peak".
        # This suggests the input file contains the Expression values?
        # No, T012: "Merge aggregated peak features with gene expression counts".
        # So the merged matrix has BOTH.
        # Structure: Gene_ID, Peak1_Access, Peak2_Access, ..., Gene_Expression?
        # OR: Gene_ID, CellLine1_Expression, CellLine1_Peak1...
        
        # Let's assume the standard format for this specific pipeline based on T012.5:
        # "Merge aggregated peak features with gene expression counts to form the joint matrix".
        # Likely: Index=Gene, Columns=Features (Peaks).
        # Where is the Target?
        # Maybe the file contains multiple cell lines, and for each cell line, 
        # we have a set of Peaks (features) and a set of Expression values (target)?
        # Or maybe the file is Genes x (Peaks + Expression)?
        
        # Let's assume the file has a specific column for the target expression for that cell line.
        # If the file is Genes x Features, and we need to predict Expression, 
        # the Expression values must be in the file.
        # Hypothesis: The file contains columns like `GM12878_Peak1`, `GM12878_Peak2`, ..., `GM12878_Expression`.
        # We will split: Features = all columns with cell_line prefix, Target = column with `Expression` or `Count` suffix?
        # Or maybe the target is implicit? No, regression needs y.
        
        # Let's assume the target column is named `{cell_line}_expression` or similar.
        # If not found, we might need to look at the data.
        
        # Robust approach:
        # 1. Identify target column.
        # 2. Identify feature columns.
        
        # Heuristic: If there's a column ending in '_expression' or '_counts' for the cell line, use it.
        # Otherwise, if there's only one column that isn't a peak (e.g. if peaks are named peak_1, peak_2),
        # we might have a problem.
        
        # Let's assume the merged matrix has:
        # Gene_ID, <cell_line>_peak_1, <cell_line>_peak_2, ..., <cell_line>_expression
        
        target_col = None
        feature_cols = []
        
        for col in features.columns:
            if col.lower().endswith('expression') or col.lower().endswith('counts'):
                target_col = col
            else:
                feature_cols.append(col)
        
        if target_col is None:
            # Fallback: Maybe the last column is the target?
            # Or maybe the file structure is different.
            # Let's try to find a column that doesn't look like a peak.
            # If we can't find it, we fail loudly.
            logger.warning(f"Could not find explicit target column for {cell_line}. "
                           f"Assuming the last column is the target?")
            # Actually, let's assume the target is named `{cell_line}_expression` based on spec.
            # If not, we try to guess.
            # If we can't, we raise error.
            raise ValueError(f"Target column (expression) not found for {cell_line} in columns: {features.columns}")
        
        X = features[feature_cols].values
        y = features[target_col].values
        
        # Handle missing values (should be imputed already, but just in case)
        if np.isnan(X).any() or np.isnan(y).any():
            logger.warning(f"NaN values found in {cell_line} data. Dropping rows.")
            mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X = X[mask]
            y = y[mask]
        
        if X.shape[0] == 0:
            logger.warning(f"No valid samples for {cell_line}. Skipping.")
            continue
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Run CV
        cv_results = run_cross_validation(X_scaled, y)
        all_cv_scores[cell_line] = cv_results
        
        # Train final model
        logger.info(f"Training final model for {cell_line} with alpha={cv_results['best_alpha']}")
        final_model = ElasticNet(
            alpha=cv_results['best_alpha'],
            l1_ratio=L1_RATIO,
            random_state=42,
            max_iter=10000
        )
        final_model.fit(X_scaled, y)
        
        # Save model
        model_path = os.path.join(output_model_dir, f"elastic_net_{cell_line}.pkl")
        model_data = {
            'model': final_model,
            'scaler': scaler,
            'feature_names': feature_cols,
            'target_column': target_col,
            'cv_results': cv_results
        }
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Saved model to {model_path}")
        checksum_file(model_path)

    # Save CV scores
    with open(output_scores_path, 'w') as f:
        json.dump(all_cv_scores, f, indent=2)
    
    logger.info(f"Saved CV scores to {output_scores_path}")
    checksum_file(output_scores_path)

def main():
    parser = argparse.ArgumentParser(description="Train Elastic Net models for gene expression prediction.")
    parser.add_argument("--input", type=str, default="data/processed/imputed_expression.csv",
                        help="Path to the imputed expression matrix CSV.")
    parser.add_argument("--model-dir", type=str, default="data/models",
                        help="Directory to save trained models.")
    parser.add_argument("--scores", type=str, default="data/processed/cv_scores.json",
                        help="Path to save CV scores JSON.")
    
    args = parser.parse_args()
    
    # Ensure directories exist
    os.makedirs(args.model_dir, exist_ok=True)
    
    try:
        train_all_cell_lines(args.input, args.model_dir, args.scores)
        logger.info("Training completed successfully.")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

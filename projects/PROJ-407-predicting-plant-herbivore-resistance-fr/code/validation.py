import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/interim/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data():
    """Load the processed dataset from data/processed."""
    path = 'data/processed/pca_reduced.csv'
    if not os.path.exists(path):
        # Fallback to harmonized if PCA reduced doesn't exist yet (though T020 should have created it)
        path = 'data/interim/harmonized.csv'
        if not os.path.exists(path):
            raise FileNotFoundError(f"Processed data file not found at {path}")
    
    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(path)
    return df

def load_split_indices():
    """Load the train/test split indices."""
    path = 'data/interim/split_indices.json'
    if not os.path.exists(path):
        raise FileNotFoundError(f"Split indices file not found at {path}")
    
    logger.info(f"Loading split indices from {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_model_metrics():
    """Load model metrics."""
    path = 'data/processed/model_metrics.json'
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model metrics file not found at {path}")
    
    logger.info(f"Loading model metrics from {path}")
    with open(path, 'r') as f:
        return json.load(f)

def train_random_forest(X_train, y_train, n_estimators=100, max_depth=10, random_state=42):
    """Train a Random Forest Regressor."""
    from sklearn.ensemble import RandomForestRegressor
    logger.info("Training Random Forest model...")
    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=random_state)
    model.fit(X_train, y_train)
    return model

def calculate_r2(model, X_test, y_test):
    """Calculate R^2 score."""
    logger.info("Calculating R^2 score...")
    return model.score(X_test, y_test)

def run_permutation_test(model, X, y, n_permutations=1000, random_state=42, split_indices=None):
    """
    Run permutation test to validate model performance.
    
    Args:
        model: Trained model
        X: Features
        y: Target
        n_permutations: Number of permutations
        random_state: Random seed
        split_indices: Dictionary with 'train' and 'test' indices
        
    Returns:
        Dictionary with null distribution and p-value
    """
    logger.info(f"Running permutation test with {n_permutations} iterations...")
    
    # Calculate observed score
    observed_score = model.score(X, y)
    logger.info(f"Observed R^2 score: {observed_score:.4f}")
    
    null_scores = []
    
    # Use the provided split indices if available, otherwise use full data
    if split_indices:
        train_idx = np.array(split_indices['train'])
        test_idx = np.array(split_indices['test'])
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    else:
        X_train, X_test = X, X
        y_train, y_test = y, y
        
    for i in range(n_permutations):
        # Shuffle y values
        y_permuted = y_train.sample(frac=1, random_state=random_state + i).reset_index(drop=True)
        
        # Retrain model on permuted data
        perm_model = train_random_forest(X_train, y_permuted, n_estimators=model.n_estimators, 
                                        max_depth=model.max_depth, random_state=random_state + i)
        
        # Calculate score on original test set
        perm_score = perm_model.score(X_test, y_test)
        null_scores.append(perm_score)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")
    
    null_scores = np.array(null_scores)
    
    # Calculate p-value
    p_value = np.mean(null_scores >= observed_score)
    
    logger.info(f"Permutation test complete. P-value: {p_value:.4f}")
    
    return {
        'observed_score': observed_score,
        'null_scores': null_scores,
        'p_value': p_value,
        'n_permutations': n_permutations
    }

def apply_batch_covariate_adjustment(df):
    """
    Implement batch covariate adjustment logic.
    
    Checks if 'batch' or 'study_id' columns exist in metadata.
    If they exist, one-hot encode them and add as covariates to the model input.
    If metadata is MISSING, raise a specific warning/error that stratification by batch 
    is not possible, and proceed with genotype-only stratification.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with batch covariates added (or original if no batch columns)
    """
    logger.info("Checking for batch covariates...")
    
    # Check for batch or study_id columns
    batch_cols = [col for col in ['batch', 'study_id'] if col in df.columns]
    
    if not batch_cols:
        logger.warning("No 'batch' or 'study_id' columns found in metadata. "
                     "Proceeding with genotype-only stratification (FR-007 fallback).")
        # Create a log file to record this decision
        log_path = 'data/interim/batch_adjustment_log.txt'
        with open(log_path, 'w') as f:
            f.write("Batch adjustment not performed: No batch or study_id columns found.\n")
            f.write("Proceeding with genotype-only stratification as per FR-007 fallback.\n")
        return df
    
    logger.info(f"Found batch covariates: {batch_cols}")
    
    # One-hot encode batch columns
    df_encoded = pd.get_dummies(df, columns=batch_cols, drop_first=True)
    
    # Save the batch corrected data
    output_path = 'data/interim/batch_corrected_data.csv'
    df_encoded.to_csv(output_path, index=False)
    logger.info(f"Saved batch corrected data to {output_path}")
    
    # Log the adjustment details
    log_path = 'data/interim/batch_adjustment_log.txt'
    with open(log_path, 'w') as f:
        f.write(f"Batch adjustment performed using columns: {batch_cols}\n")
        f.write(f"Output saved to: {output_path}\n")
        f.write(f"Number of original columns: {len(df.columns)}\n")
        f.write(f"Number of adjusted columns: {len(df_encoded.columns)}\n")
    
    return df_encoded

def save_results(results, output_dir='data/interim'):
    """Save permutation test results."""
    # Save null distribution
    null_dist_path = os.path.join(output_dir, 'null_distribution.csv')
    pd.DataFrame({'score': results['null_scores']}).to_csv(null_dist_path, index=False)
    logger.info(f"Saved null distribution to {null_dist_path}")
    
    # Save p-value
    pval_path = os.path.join(output_dir, 'permutation_p_value.json')
    with open(pval_path, 'w') as f:
        json.dump({
            'observed_score': results['observed_score'],
            'p_value': results['p_value'],
            'n_permutations': results['n_permutations']
        }, f, indent=2)
    logger.info(f"Saved p-value to {pval_path}")
    
    # Save execution log
    log_path = os.path.join(output_dir, 'permutation_run.log')
    with open(log_path, 'w') as f:
        f.write(f"Permutation test completed with {results['n_permutations']} iterations\n")
        f.write(f"Observed score: {results['observed_score']:.4f}\n")
        f.write(f"P-value: {results['p_value']:.4f}\n")
    logger.info(f"Saved execution log to {log_path}")

def main():
    """Main function to run batch covariate adjustment and validation."""
    try:
        # Load data
        df = load_processed_data()
        
        # Apply batch covariate adjustment
        df_adjusted = apply_batch_covariate_adjustment(df)
        
        # Continue with validation if needed
        logger.info("Batch covariate adjustment completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during batch covariate adjustment: {str(e)}")
        raise

if __name__ == "__main__":
    main()
import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str = "data/processed/ingredient_pairs_with_labels.csv") -> pd.DataFrame:
    """
    Load the processed dataset containing predictors and labels.
    
    Args:
        input_path: Path to the CSV file containing processed data.
        
    Returns:
        DataFrame with predictors and labels.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T019 (Compatibility Labels) has been completed.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for a set of predictors.
    
    VIF measures how much the variance of an estimated regression coefficient 
    increases if your predictors are correlated.
    
    Formula: VIF_j = 1 / (1 - R_j^2)
    where R_j^2 is the R-squared value when predictor j is regressed on all other predictors.
    
    Args:
        df: DataFrame containing the predictors.
        predictor_cols: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping predictor names to their VIF values.
        
    Raises:
        ValueError: If any predictor has zero variance or if there are insufficient samples.
    """
    if len(predictor_cols) == 0:
        raise ValueError("At least one predictor column must be provided.")
        
    # Check for zero variance columns
    for col in predictor_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame.")
        if df[col].var() == 0:
            raise ValueError(f"Column '{col}' has zero variance. VIF cannot be calculated.")
    
    vif_results = {}
    
    # Handle categorical variables by creating dummy variables if necessary
    # For functional_role, we assume it's already encoded or we create dummies
    df_temp = df.copy()
    
    # Identify categorical columns in predictor_cols
    categorical_cols = []
    for col in predictor_cols:
        if df_temp[col].dtype == 'object' or df_temp[col].dtype.name == 'category':
            categorical_cols.append(col)
    
    # Create dummy variables for categorical predictors
    if categorical_cols:
        df_temp = pd.get_dummies(df_temp, columns=categorical_cols, drop_first=True)
    
    # Ensure we have numeric columns only for VIF calculation
    numeric_predictors = [col for col in df_temp.columns if col in predictor_cols or 
                          any(col.startswith(c + '_') for c in categorical_cols)]
    
    # Filter to only the predictors we care about (and their dummies)
    relevant_cols = []
    for col in predictor_cols:
        if col in df_temp.columns:
            relevant_cols.append(col)
        else:
            # Check if this is a categorical column that got dummied
            dummies = [c for c in df_temp.columns if c.startswith(col + '_')]
            relevant_cols.extend(dummies)
    
    if len(relevant_cols) == 0:
        raise ValueError("No valid numeric predictors found for VIF calculation.")
    
    # Calculate VIF for each predictor
    for i, col in enumerate(relevant_cols):
        # Create design matrix X for regression: col ~ other predictors
        y = df_temp[col]
        X = df_temp.drop(columns=[col])
        
        # Add intercept
        X_with_intercept = sm.add_constant(X)
        
        # Fit OLS regression
        model = sm.OLS(y, X_with_intercept).fit()
        
        # Calculate VIF: 1 / (1 - R^2)
        r_squared = model.rsquared
        vif = 1 / (1 - r_squared) if (1 - r_squared) > 1e-10 else np.inf
        
        vif_results[col] = vif
        logger.info(f"VIF for {col}: {vif:.4f} (R^2 = {r_squared:.4f})")
    
    return vif_results

def drop_high_vif_predictors(vif_results: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF above a threshold.
    
    Args:
        vif_results: Dictionary of VIF values.
        threshold: VIF threshold above which predictors are considered problematic.
        
    Returns:
        List of predictor names with VIF > threshold.
    """
    high_vif = [col for col, vif in vif_results.items() if vif > threshold]
    if high_vif:
        logger.warning(f"High VIF detected (> {threshold}): {high_vif}")
    else:
        logger.info(f"No predictors exceed VIF threshold of {threshold}")
    return high_vif

def perform_likelihood_ratio_test() -> Dict[str, float]:
    """
    Placeholder for Likelihood Ratio Test (to be implemented in T024b).
    
    Returns:
        Empty dict indicating this test is not part of T023.
    """
    logger.info("Likelihood Ratio Test is scheduled for T024b")
    return {}

def post_hoc_power_validation() -> Dict[str, float]:
    """
    Placeholder for post-hoc power validation (to be implemented in T025).
    
    Returns:
        Empty dict indicating this validation is not part of T023.
    """
    logger.info("Post-hoc power validation is scheduled for T025")
    return {}

def resolve_multicollinearity_and_retest(df: pd.DataFrame, 
                                         predictor_cols: List[str],
                                         vif_threshold: float = 5.0) -> Tuple[Dict[str, float], List[str]]:
    """
    Identify and remove high VIF predictors, then recalculate VIF.
    
    Args:
        df: DataFrame with predictors.
        predictor_cols: Initial list of predictors.
        vif_threshold: VIF threshold for removal.
        
    Returns:
        Tuple of (final_vif_results, removed_predictors)
    """
    removed = []
    current_cols = predictor_cols.copy()
    
    while True:
        vif_results = calculate_vif(df, current_cols)
        high_vif = drop_high_vif_predictors(vif_results, vif_threshold)
        
        if not high_vif:
            break
        
        # Remove the predictor with the highest VIF
        worst_col = max(high_vif, key=lambda x: vif_results[x])
        removed.append(worst_col)
        current_cols.remove(worst_col)
        logger.info(f"Removed {worst_col} (VIF = {vif_results[worst_col]:.2f}) due to multicollinearity")
    
    final_vif = calculate_vif(df, current_cols)
    return final_vif, removed

def main():
    """
    Main function to execute VIF calculation task (T023).
    
    This function:
    1. Loads the processed ingredient pairs dataset.
    2. Calculates VIF for all predictors (log_co_occurrence, flavor_similarity, functional_role).
    3. Saves the VIF scores to data/logs/vif_scores.json.
    """
    logger.info("Starting VIF Calculation (Task T023)")
    
    # Define paths
    input_path = "data/processed/ingredient_pairs_with_labels.csv"
    output_dir = Path("data/logs")
    output_path = output_dir / "vif_scores.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = load_processed_data(input_path)
        
        # Define predictors based on task description
        # Note: functional_role might be categorical, so we handle it appropriately
        predictor_cols = ['log_co_occurrence', 'flavor_similarity', 'functional_role']
        
        # Verify all predictors exist
        missing = [col for col in predictor_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required predictor columns: {missing}. "
                             "Ensure T018 (Imputation) has been completed correctly.")
        
        logger.info(f"Calculating VIF for predictors: {predictor_cols}")
        
        # Calculate VIF
        vif_results = calculate_vif(df, predictor_cols)
        
        # Identify high VIF predictors
        high_vif_predictors = drop_high_vif_predictors(vif_results, threshold=5.0)
        
        # Prepare results
        results = {
            "vif_scores": vif_results,
            "high_vif_predictors": high_vif_predictors,
            "threshold": 5.0,
            "total_samples": len(df),
            "predictor_count": len(predictor_cols),
            "status": "completed"
        }
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"VIF calculation complete. Results saved to {output_path}")
        logger.info(f"VIF Scores: {vif_results}")
        
        if high_vif_predictors:
            logger.warning(f"High VIF detected for: {high_vif_predictors}. "
                         "Consider removing these predictors or using regularization.")
        
        return results
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during VIF calculation: {e}")
        raise

if __name__ == "__main__":
    import statsmodels.api as sm  # Import here to avoid issues if not needed
    main()

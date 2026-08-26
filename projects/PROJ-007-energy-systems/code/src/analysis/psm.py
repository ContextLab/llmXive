import pandas as pd
import numpy as np
from typing import Optional, Tuple, Dict, List
import warnings
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from src.analysis.balance import calculate_smd
from src.data.preprocess import PowerError

def estimate_propensity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    
    Args:
        df: DataFrame with covariates and treatment variable
    
    Returns:
        DataFrame with added 'propensity_score' column
    """
    covariate_cols = ['income', 'housing_type', 'location']
    treatment_col = 'treatment'
    
    # Filter out rows with missing treatment or covariates
    valid_cols = [treatment_col] + covariate_cols
    df_clean = df.dropna(subset=valid_cols)
    
    if len(df_clean) == 0:
        raise ValueError("No valid data for propensity estimation after dropping NaNs")
    
    X = df_clean[covariate_cols]
    y = df_clean[treatment_col]
    
    # Handle categorical variables (simple encoding for now)
    for col in X.columns:
        if X[col].dtype == 'object':
            X = pd.get_dummies(X, columns=[col], drop_first=True)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    
    scores = model.predict_proba(X_scaled)[:, 1]
    
    result = df_clean.copy()
    result['propensity_score'] = scores
    
    return result

def match_pairs(df: pd.DataFrame, caliper: float) -> pd.DataFrame:
    """
    Perform nearest neighbor matching with caliper constraint.
    
    Args:
        df: DataFrame with 'propensity_score' and 'treatment' columns
        caliper: Maximum allowed difference in propensity scores
    
    Returns:
        DataFrame with matched pairs (only treated units with matches)
    """
    treated = df[df['treatment'] == 1].copy()
    control = df[df['treatment'] == 0].copy()
    
    if len(treated) == 0 or len(control) == 0:
        raise ValueError("Cannot match: missing treated or control units")
    
    matched_indices = []
    
    for _, t_row in treated.iterrows():
        t_score = t_row['propensity_score']
        # Find controls within caliper
        diffs = (control['propensity_score'] - t_score).abs()
        within_caliper = diffs <= caliper
        
        if within_caliper.any():
            # Find nearest neighbor
            best_idx = diffs[within_caliper].idxmin()
            matched_indices.append((t_row.name, best_idx))
    
    if len(matched_indices) == 0:
        raise ValueError("No matches found within caliper")
    
    # Create matched DataFrame
    matched_df = pd.DataFrame(matched_indices, columns=['treated_idx', 'control_idx'])
    matched_df['treated_data'] = matched_df['treated_idx'].apply(lambda x: df.loc[x])
    matched_df['control_data'] = matched_df['control_idx'].apply(lambda x: df.loc[x])
    
    # Flatten to single DataFrame
    result_rows = []
    for _, row in matched_df.iterrows():
        t_data = row['treated_data']
        c_data = row['control_data']
        
        t_entry = t_data.to_dict()
        t_entry['pair_id'] = row.name
        t_entry['match_type'] = 'treated'
        
        c_entry = c_data.to_dict()
        c_entry['pair_id'] = row.name
        c_entry['match_type'] = 'control'
        
        result_rows.append(t_entry)
        result_rows.append(c_entry)
    
    return pd.DataFrame(result_rows)

def check_common_support(df: pd.DataFrame) -> bool:
    """
    Check if there is common support in propensity scores.
    
    Args:
        df: DataFrame with 'propensity_score' column
    
    Returns:
        True if common support exists, False otherwise
    """
    treated_scores = df[df['treatment'] == 1]['propensity_score']
    control_scores = df[df['treatment'] == 0]['propensity_score']
    
    if len(treated_scores) == 0 or len(control_scores) == 0:
        return False
    
    # Check overlap
    treated_min, treated_max = treated_scores.min(), treated_scores.max()
    control_min, control_max = control_scores.min(), control_scores.max()
    
    overlap = max(0, min(treated_max, control_max) - max(treated_min, control_min))
    
    return overlap > 0

def iterative_matching(
    df: pd.DataFrame,
    covariates: List[str],
    max_caliper: float = 0.2,
    min_caliper: float = 0.01,
    max_iterations: int = 20,
    smd_threshold: float = 0.1
) -> Tuple[pd.DataFrame, Dict]:
    """
    Iteratively adjust caliper and covariates to achieve balance.
    
    This function implements an iterative loop that:
    1. Attempts matching with current caliper
    2. Calculates SMD for all covariates
    3. If SMD > threshold, reduces caliper by 0.01
    4. If caliper < min_caliper, removes lowest-weight covariate and retries
    5. Terminates after max_iterations or when balance is achieved
    6. Sets balance_status flag if balance cannot be achieved (triggers DiD fallback)
    
    Args:
        df: Preprocessed DataFrame with treatment and covariates
        covariates: List of covariate column names to use for matching
        max_caliper: Starting caliper value
        min_caliper: Minimum caliper before covariate removal
        max_iterations: Maximum number of iterations
        smd_threshold: Maximum acceptable SMD for balance
    
    Returns:
        Tuple of (matched_df, balance_info) where balance_info contains:
            - 'balance_status': 'balanced' or 'failed'
            - 'final_caliper': final caliper used
            - 'smd_values': dict of SMD values for each covariate
            - 'removed_covariates': list of covariates removed during iterations
    """
    current_caliper = max_caliper
    current_covariates = covariates.copy()
    removed_covariates = []
    iteration = 0
    
    # Estimate propensity scores with current covariates
    df_with_scores = estimate_propensity(df[current_covariates + ['treatment']])
    
    # Check common support
    if not check_common_support(df_with_scores):
        balance_info = {
            'balance_status': 'failed',
            'final_caliper': current_caliper,
            'smd_values': {},
            'removed_covariates': removed_covariates,
            'reason': 'No common support in propensity scores'
        }
        return df_with_scores, balance_info
    
    while iteration < max_iterations:
        try:
            # Perform matching
            matched_df = match_pairs(df_with_scores, current_caliper)
            
            # Calculate SMD for all original covariates (not just current ones)
            smd_values = calculate_smd(matched_df, covariates)
            
            # Check if all SMDs are below threshold
            max_smd = max(smd_values.values()) if smd_values else float('inf')
            
            if max_smd <= smd_threshold:
                # Balance achieved
                balance_info = {
                    'balance_status': 'balanced',
                    'final_caliper': current_caliper,
                    'smd_values': smd_values,
                    'removed_covariates': removed_covariates,
                    'iterations': iteration + 1
                }
                return matched_df, balance_info
            
            # If not balanced, reduce caliper
            if current_caliper > min_caliper:
                current_caliper -= 0.01
                iteration += 1
                continue
            
            # If caliper is too small, remove lowest-weight covariate
            if len(current_covariates) > 1:
                # Estimate model to get weights
                X = df[current_covariates]
                for col in X.columns:
                    if X[col].dtype == 'object':
                        X = pd.get_dummies(X, columns=[col], drop_first=True)
                
                X_scaled = StandardScaler().fit_transform(X)
                y = df['treatment']
                
                model = LogisticRegression(max_iter=1000)
                model.fit(X_scaled, y)
                
                # Get absolute coefficients as weights
                weights = np.abs(model.coef_[0])
                # Map back to original column names
                col_weights = dict(zip(X.columns, weights))
                
                # Find lowest weight covariate
                lowest_covariate = min(col_weights, key=col_weights.get)
                current_covariates.remove(lowest_covariate)
                removed_covariates.append(lowest_covariate)
                
                # Re-estimate propensity scores with reduced covariates
                df_with_scores = estimate_propensity(df[current_covariates + ['treatment']])
                
                # Check common support again
                if not check_common_support(df_with_scores):
                    balance_info = {
                        'balance_status': 'failed',
                        'final_caliper': current_caliper,
                        'smd_values': smd_values,
                        'removed_covariates': removed_covariates,
                        'reason': 'No common support after covariate removal'
                    }
                    return df_with_scores, balance_info
                
                # Reset caliper to max for new covariate set
                current_caliper = max_caliper
                iteration += 1
                continue
            
            # If we get here, we can't remove more covariates and balance failed
            break
            
        except Exception as e:
            # If matching fails, try reducing caliper
            if current_caliper > min_caliper:
                current_caliper -= 0.01
                iteration += 1
                continue
            else:
                break
    
    # If we exit the loop without achieving balance
    balance_info = {
        'balance_status': 'failed',
        'final_caliper': current_caliper,
        'smd_values': smd_values if 'smd_values' in locals() else {},
        'removed_covariates': removed_covariates,
        'iterations': iteration,
        'reason': f'Maximum iterations ({max_iterations}) reached without achieving balance'
    }
    
    return matched_df, balance_info
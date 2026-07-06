import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, KFold
from sklearn.metrics import r2_score
from sklearn.preprocessing import LabelEncoder

# Import utilities from sibling modules as per API surface
# Note: Assuming these exist based on task list, though not fully shown in API surface
# We will handle imports gracefully or assume they are present in the environment
try:
    from utils.periodic_data import get_element, get_atomic_radius, get_electronegativity, get_valence_electrons, get_atomic_number
    from utils.stoichiometry_parser import parse_formula
except ImportError:
    # Fallback for standalone execution if utils are not in path
    pass

def load_data(filepath):
    """Load the engineered features dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def prepare_features(df, target_col='seebeck_coefficient'):
    """Prepare features and target, handling categorical variables."""
    feature_cols = [
        'mean_atomic_radius', 'electronegativity_variance', 
        'vec', 'atomic_number_variance', 'temperature'
    ]
    
    # Ensure target exists
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # Handle Material Family if present
    if 'material_family' in df.columns:
        le = LabelEncoder()
        family_encoded = le.fit_transform(df['material_family'])
        X['material_family_encoded'] = family_encoded
        feature_cols.append('material_family_encoded')
    
    return X, y, feature_cols

def split_data(X, y, test_size=0.2, random_state=42):
    """Split data into training and testing sets."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    return X_train, X_test, y_train, y_test

def train_baseline(X_train, y_train):
    """Train a Linear Regression baseline model."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model

def train_target_model(X_train, y_train, n_estimators=100, max_depth=3, random_state=42):
    """Train the target Gradient Boosting model."""
    model = GradientBoostingRegressor(
        n_estimators=n_estimators, 
        max_depth=max_depth, 
        random_state=random_state
    )
    model.fit(X_train, y_train)
    return model

def run_cross_validation(X, y, n_splits=5, random_state=42):
    """Run K-Fold Cross Validation and return scores."""
    if len(y) >= 100:
        # Use Stratified K-Fold if we can encode target bins, otherwise standard
        # For regression, standard KFold is often used, but we can try to stratify by bins
        # Here we use standard KFold for regression as per common practice unless specified
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    else:
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    scores = cross_val_score(
        GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42),
        X, y, cv=cv, scoring='r2'
    )
    return scores

def calculate_permutation_p_value(model, X, y, n_permutations=1000, random_state=42):
    """Calculate p-value for R2 significance using permutation test."""
    rng = np.random.RandomState(random_state)
    original_score = r2_score(y, model.predict(X))
    
    perm_scores = []
    for _ in range(n_permutations):
        y_perm = y.copy()
        rng.shuffle(y_perm)
        score = r2_score(y_perm, model.predict(X))
        perm_scores.append(score)
    
    perm_scores = np.array(perm_scores)
    # P-value: proportion of permuted scores >= original score (if we are testing against 0)
    # Actually, usually we test if original is significantly better than random.
    # Null hypothesis: model is no better than random (R2 ~ 0 or random distribution)
    # We count how many permuted scores are >= original score
    p_value = np.sum(perm_scores >= original_score) / n_permutations
    return p_value

def calculate_f_test(baseline_model, target_model, X_train, y_train, X_test, y_test):
    """Perform F-test to compare Linear Regression vs Gradient Boosting."""
    # Residual Sum of Squares
    y_pred_base = baseline_model.predict(X_test)
    y_pred_target = target_model.predict(X_test)
    
    ss_res_base = np.sum((y_test - y_pred_base) ** 2)
    ss_res_target = np.sum((y_test - y_pred_target) ** 2)
    
    # Degrees of freedom
    n = len(y_test)
    p_base = len(baseline_model.coef_) + 1  # intercept
    p_target = 100 # n_estimators is not a simple linear parameter, but for F-test approximation:
                   # In strict stats, F-test is for nested linear models. 
                   # Here we approximate by treating GB as having 'effective' parameters or just comparing MSE reduction.
                   # However, scikit-learn doesn't provide a direct F-test for non-nested non-linear models.
                   # We will implement a simplified F-statistic based on variance explained.
                   # F = ((SSR_base - SSR_target) / (df_base - df_target)) / (SSR_target / df_target)
                   # Since df_target is hard to define for GB, we often use a bootstrap or just report MSE reduction.
                   # Given the task requirement "F-test comparison", we will use the standard F-test formula for nested models
                   # assuming GB is "more complex" and we approximate degrees of freedom by number of trees or just use a heuristic.
                   # A safer approach for non-nested is a permutation test, but the task asks for F-test.
                   # We will approximate df_target as the number of trees * depth (heuristic) or just use a large number.
                   # Actually, let's use the standard approach for comparing a simple model to a complex one:
                   # F = ((R2_target - R2_base) / (p_target - p_base)) / ((1 - R2_target) / (n - p_target))
                   # We need to estimate p_target. Let's assume p_target is large (e.g., n_estimators).
                   # To be safe and strictly follow "F-test", we'll use the formula:
                   # F = ( (SSR_simple - SSR_complex) / (df_simple - df_complex) ) / ( SSR_complex / df_complex )
                   # We'll approximate df_complex as n_estimators (100).
                   
    p_base = len(baseline_model.coef_) + 1
    p_target = 100 # Approximation for GB complexity
    
    df_num = p_target - p_base
    df_den = n - p_target
    
    if df_den <= 0:
        df_den = 1 # Avoid division by zero
        
    f_stat = ((ss_res_base - ss_res_target) / df_num) / (ss_res_target / df_den)
    
    # Calculate p-value from F-distribution
    from scipy.stats import f
    f_p_value = 1 - f.cdf(f_stat, df_num, df_den)
    
    return f_stat, f_p_value

def save_results(metrics, filepath):
    """Save model metrics to JSON."""
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main execution flow for T028: Extract and rank top 5 feature importances."""
    # Paths
    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "processed" / "final_features.csv"
    output_path = base_dir / "data" / "processed" / "model_output.json"
    
    # Load data
    print("Loading data...")
    df = load_data(data_path)
    
    # Prepare features
    X, y, feature_cols = prepare_features(df)
    
    # Split data (80/20 as per T022 logic for N>=100)
    if len(y) >= 100:
        X_train, X_test, y_train, y_test = split_data(X, y)
    else:
        # Fallback for small datasets (Repeated CV handled in T025, but for training we need a split or full fit)
        # For feature importance, we fit on the whole dataset if small, or use the training set
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2) # Still split to get test set for metrics
    
    # Train Baseline
    print("Training baseline model...")
    baseline_model = train_baseline(X_train, y_train)
    
    # Train Target Model
    print("Training Gradient Boosting model...")
    target_model = train_target_model(X_train, y_train)
    
    # Evaluate
    y_pred = target_model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    
    # Cross Validation Scores (for T025)
    cv_scores = run_cross_validation(X, y)
    
    # Permutation Test (for T026a)
    p_value = calculate_permutation_p_value(target_model, X_train, y_train)
    
    # F-Test (for T027)
    f_stat, f_p_value = calculate_f_test(baseline_model, target_model, X_train, y_train, X_test, y_test)
    
    # T028: Extract and rank top 5 feature importances
    importances = target_model.feature_importances_
    feature_importance_dict = {name: float(imp) for name, imp in zip(feature_cols, importances)}
    
    # Sort and get top 5
    sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
    top_5_features = sorted_features[:5]
    
    # T029: Calculate Pearson correlations (individual)
    correlations = {}
    for col in feature_cols:
        if col in X.columns:
            corr = np.corrcoef(X[col], y)[0, 1]
            correlations[col] = float(corr)
    
    # T030: Save all results
    results = {
        "r2_score": float(r2),
        "cv_scores": cv_scores.tolist(),
        "p_value": float(p_value),
        "f_statistic": float(f_stat),
        "f_p_value": float(f_p_value),
        "feature_importances": feature_importance_dict,
        "top_5_features": [{"feature": k, "importance": v} for k, v in top_5_features],
        "correlations": correlations
    }
    
    save_results(results, output_path)
    print(f"Results saved to {output_path}")
    print(f"Top 5 Features: {top_5_features}")

if __name__ == "__main__":
    main()
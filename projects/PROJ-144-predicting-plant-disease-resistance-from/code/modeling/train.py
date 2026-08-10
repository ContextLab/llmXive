import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import balanced_accuracy_score
from code.utils.constants import HOLD_OUT_FRACTION, RANDOM_STATE

def train_model(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Train a Random Forest model with Stratified 5-fold CV and GridSearchCV.
    Returns the trained model and the best parameters.
    """
    # Split data: Hold-out first
    X_temp, X_hold, y_temp, y_hold = train_test_split(
        X, y, test_size=HOLD_OUT_FRACTION, random_state=RANDOM_STATE, stratify=y
    )
    
    # Define model
    rf = RandomForestClassifier(random_state=RANDOM_STATE, n_estimators=500, max_depth=10)
    
    # GridSearchCV within CV loop
    param_grid = {'max_depth': [10, 15, 20]}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=cv,
        scoring='balanced_accuracy',
        n_jobs=-1
    )
    
    grid_search.fit(X_temp, y_temp)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Save model
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/best_model.pkl", "wb") as f:
        pickle.dump(best_model, f)
        
    return best_model, best_params, X_hold, y_hold

if __name__ == "__main__":
    # Example usage if run directly (should be called by pipeline)
    print("Train script ready.")

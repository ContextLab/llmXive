import os
import sys
import logging
import pickle
import random
from pathlib import Path
import pandas as pd
from sklearn.ensemble import LightGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import pearsonr
from utils import calculate_vif, check_vif_threshold

def log_transform_latency(df):
    """Log-transforms latency values to reduce skewness."""
    df['latency'] = np.log1p(df['latency'])
    return df

def aggregate_interaction_counts(df):
    """Aggregates interaction counts per session."""
    session_counts = df.groupby('session_id').agg({
        'error_flag': 'sum',
        'hint_request': 'sum',
        'pause': 'sum'
    }).reset_index()
    df = pd.merge(df, session_counts, on='session_id')
    return df

def engineer_features(df):
    """Engineers features for the model."""
    df = log_transform_latency(df)
    df = aggregate_interaction_counts(df)
    return df

def check_collinearity(df, vif_threshold=5.0):
    """Checks for collinearity using VIF and flags predictors if needed."""
    vif_data = calculate_vif(df)
    predictors_to_flag = [col for col, vif in vif_data.items() if vif > vif_threshold]
    return predictors_to_flag

def train_model(X, y):
    """Trains a LightGBM regressor model."""
    model = LightGBMRegressor(objective='regression', metric='rmse', n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def validate_against_golden_set(model, X_test, y_test):
    """Validates the model against the golden set."""
    y_pred = model.predict(X_test)
    correlation, _ = pearsonr(y_test, y_pred)
    return correlation

def main():
    """Main function to train and validate the load model."""
    # Load data
    try:
        df = pd.read_csv('data/processed/golden_set.csv')
    except FileNotFoundError:
        print("Error: golden_set.csv not found.")
        sys.exit(1)

    # Feature engineering
    df = engineer_features(df)

    # Select features and target variable
    features = ['latency', 'error_flag', 'hint_request', 'pause']
    target = 'expert_load_score'

    # Prepare data for training
    X = df[features]
    y = df[target]

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Check for collinearity
    vif_threshold = 5.0
    predictors_to_flag = check_collinearity(df, vif_threshold)
    if predictors_to_flag:
        print(f"Warning: Predictors with VIF > {vif_threshold}: {predictors_to_flag}")

    # Train the model
    model = train_model(X_train, y_train)

    # Validate the model
    correlation = validate_against_golden_set(model, X_test, y_test)
    print(f"Pearson correlation between predicted and actual load scores: {correlation:.2f}")

    if correlation >= 0.6:
        print("Model validation successful.")
        # Save the model
        with open('data/processed/load_model.pkl', 'wb') as f:
            pickle.dump(model, f)
    else:
        print("Model validation failed. Correlation is below 0.6.")

if __name__ == "__main__":
    main()

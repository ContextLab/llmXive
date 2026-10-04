import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from code.config import SEED, DATA_PATH
from code.scaffold_split import scaffold_split

logger = logging.getLogger(__name__)

def apply_log_transformation(values: pd.Series) -> pd.Series:
    return np.log(values)

def select_target_variable(df: pd.DataFrame) -> str:
    # T026 logic simplified
    candidates = ['conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']
    for c in candidates:
        if c in df.columns:
            return c
    # Fallback
    if 'log_conductivity_proxy' in df.columns:
        return 'log_conductivity_proxy'
    return 'conductivity' # Default

def train_models(df: pd.DataFrame, target_col: str):
    # T029: Train RF and GB
    X = df.drop(columns=[target_col, 'smiles'])
    y = df[target_col]
    
    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    
    rf.fit(X, y)
    gb.fit(X, y)
    
    return rf, gb

def run_cross_validation(df: pd.DataFrame, target_col: str):
    # T030: CV
    X = df.drop(columns=[target_col, 'smiles'])
    y = df[target_col]
    
    rf = RandomForestRegressor(n_estimators=100, random_state=SEED)
    scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
    return scores.mean(), scores.std()

def save_model_results(results: dict):
    path = os.path.join(DATA_PATH, 'processed', 'model_results.json')
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    args = parser.parse_args()
    
    setup_logging()
    
    data_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    df = pd.read_csv(data_path)
    
    target_col = select_target_variable(df)
    df[target_col] = apply_log_transformation(df[target_col])
    
    if args.train:
        rf, gb = train_models(df, target_col)
        logger.info("Models trained.")
    
    return 0

def setup_logging():
    from code.logging_config import setup_logging as sl
    sl()

"""
Correlation Calculation Module.

Calculates correlation coefficients between structural features and execution outcomes.
"""
import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

from config.loader import get_config

def encode_target(outcome: str) -> int:
    """Encode target: 1 for Pass, 0 otherwise."""
    return 1 if outcome == 'Pass' else 0

def calculate_correlations(df: pd.DataFrame, feature_cols: list, target_col: str) -> Dict[str, float]:
    """Calculate Pearson correlation for each feature against the target."""
    encoded_target = df[target_col].apply(encode_target)
    correlations = {}
    for col in feature_cols:
        if col in df.columns:
            # Handle non-numeric columns gracefully
            if pd.api.types.is_numeric_dtype(df[col]):
                corr = df[col].corr(encoded_target)
                correlations[col] = float(corr) if not np.isnan(corr) else 0.0
            else:
                correlations[col] = 0.0
    return correlations

def main():
    """Main entry point."""
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    models_dir = Path(config.get("models_dir", "models"))
    processed_dir = data_dir / "processed"

    features_path = processed_dir / "features.csv"
    if not features_path.exists():
        print(f"Error: {features_path} not found.")
        sys.exit(1)

    df = pd.read_csv(features_path)
    feature_cols = ['lines_of_code', 'cyclomatic_complexity', 'dependency_depth', 'semantic_complexity_score']
    existing_cols = [c for c in feature_cols if c in df.columns]

    correlations = calculate_correlations(df, existing_cols, 'dynamic_execution_outcome')

    # Save to model report or standalone file
    output_path = models_dir / "correlations.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(correlations, f, indent=2)

    print(f"Correlations saved to {output_path}")
    print(json.dumps(correlations, indent=2))

if __name__ == "__main__":
    main()

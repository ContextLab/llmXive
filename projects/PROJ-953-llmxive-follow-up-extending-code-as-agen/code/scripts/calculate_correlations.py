import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

def encode_target(target_col: pd.Series) -> np.ndarray:
    """
    Encode the target column to binary:
    'Pass' -> 0 (No dynamic execution needed if already passed statically? 
               Actually, the goal is to predict 'need for dynamic execution'.
               If outcome is 'Pass', we might not need dynamic execution (0).
               If outcome is 'Fail' or 'Timeout/Fail', we definitely needed it (1).
    """
    # Mapping: Pass -> 0 (No need), Fail/Timeout/Fail -> 1 (Need)
    # Adjust based on specific project definition of "need"
    # Assuming: 'Pass' = 0, others = 1
    return target_col.map(lambda x: 0 if x == 'Pass' else 1).astype(int).values

def calculate_correlations(features_path: str, ground_truth_path: str) -> Dict[str, Any]:
    """
    Calculate correlation coefficients between structural features and execution necessity.
    
    Args:
        features_path: Path to data/processed/features.csv
        ground_truth_path: Path to data/processed/ground_truth.csv
        
    Returns:
        Dictionary containing correlation results and metadata
    """
    # Load features
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    if not os.path.exists(ground_truth_path):
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")

    features_df = pd.read_csv(features_path)
    ground_truth_df = pd.read_csv(ground_truth_path)

    # Merge on task_id
    merged_df = pd.merge(
        features_df, 
        ground_truth_df[['task_id', 'dynamic_execution_outcome']], 
        on='task_id', 
        how='inner'
    )

    if merged_df.empty:
        raise ValueError("No overlapping task_ids found between features and ground truth.")

    # Encode target
    y = encode_target(merged_df['dynamic_execution_outcome'])

    # Select numeric feature columns (exclude task_id and target)
    feature_cols = [col for col in merged_df.columns if col not in ['task_id', 'dynamic_execution_outcome']]
    X = merged_df[feature_cols].select_dtypes(include=[np.number]).values

    if X.shape[1] == 0:
        raise ValueError("No numeric features found for correlation calculation.")

    # Calculate Pearson correlation for each feature
    correlations = {}
    for i, col in enumerate(feature_cols):
        if np.std(X[:, i]) > 0:  # Avoid division by zero for constant features
            corr = np.corrcoef(X[:, i], y)[0, 1]
            correlations[col] = float(corr)
        else:
            correlations[col] = 0.0

    # Identify strongest correlations
    sorted_corrs = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    
    result = {
        "correlations": correlations,
        "top_correlations": sorted_corrs[:10],
        "framing": "associational",
        "feature_count": len(feature_cols),
        "sample_size": len(merged_df)
    }

    return result

def main():
    """
    Main entry point for calculating correlations.
    Reads features and ground truth, calculates correlations, and saves results.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    features_path = project_root / "data" / "processed" / "features.csv"
    ground_truth_path = project_root / "data" / "processed" / "ground_truth.csv"
    output_path = project_root / "data" / "processed" / "correlation_report.json"

    print(f"Calculating correlations...")
    print(f"Features path: {features_path}")
    print(f"Ground truth path: {ground_truth_path}")

    try:
        results = calculate_correlations(str(features_path), str(ground_truth_path))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Correlation report saved to: {output_path}")
        print(f"Top 5 correlations: {results['top_correlations'][:5]}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error processing data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

"""
Per-system evaluation logic for User Story 2.

Implements per-system evaluation logic to report R² values for each alloy system separately.
Requires alloy_systems.json from T015b to group samples.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from config import get_project_root, get_data_paths

logger = logging.getLogger(__name__)

def load_alloy_systems() -> Dict[str, List[str]]:
    """
    Load alloy_systems.json from data/processed/ directory.
    
    Returns:
        Dict mapping alloy_system_id to list of sample IDs.
        
    Raises:
        FileNotFoundError: If alloy_systems.json is missing.
        ValueError: If file format is invalid.
    """
    data_paths = get_data_paths()
    alloy_systems_path = data_paths['processed'] / 'alloy_systems.json'
    
    if not alloy_systems_path.exists():
        raise FileNotFoundError(
            f"[T025] Required file missing: {alloy_systems_path}. "
            f"Ensure T015b (generate_alloy_systems_report) has completed successfully."
        )
    
    try:
        with open(alloy_systems_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise ValueError(f"Invalid format in {alloy_systems_path}: expected dict, got {type(data)}")
        
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {alloy_systems_path}: {e}")

def load_processed_data() -> pd.DataFrame:
    """
    Load descriptors and segregation energies from processed data files.
    
    Returns:
        DataFrame with merged descriptors and energies.
        
    Raises:
        FileNotFoundError: If required data files are missing.
    """
    data_paths = get_data_paths()
    descriptors_path = data_paths['processed'] / 'descriptors.csv'
    energies_path = data_paths['processed'] / 'segregation_energies.csv'
    
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Missing descriptors file: {descriptors_path}")
    if not energies_path.exists():
        raise FileNotFoundError(f"Missing energies file: {energies_path}")
    
    descriptors_df = pd.read_csv(descriptors_path)
    energies_df = pd.read_csv(energies_path)
    
    # Merge on sample_id (assuming both files have this column)
    merged_df = pd.merge(descriptors_df, energies_df, on='sample_id', how='inner')
    
    logger.info(f"Merged {len(merged_df)} samples from descriptors and energies")
    return merged_df

def evaluate_per_system(
    df: pd.DataFrame,
    alloy_systems: Dict[str, List[str]],
    feature_columns: List[str]
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate model performance separately for each alloy system.
    
    Args:
        df: DataFrame with samples, features, and target (segregation_energy).
        alloy_systems: Dict mapping alloy_system_id to list of sample IDs.
        feature_columns: List of feature column names to use for regression.
        
    Returns:
        Dict mapping alloy_system_id to evaluation metrics (r2, rmse, n_samples).
    """
    results = {}
    
    for system_id, sample_ids in alloy_systems.items():
        # Filter samples for this system
        system_df = df[df['sample_id'].isin(sample_ids)]
        
        if len(system_df) == 0:
            logger.warning(f"No samples found for alloy system: {system_id}")
            continue
        
        if len(system_df) < 2:
            logger.warning(f"Insufficient samples ({len(system_df)}) for regression in {system_id}")
            results[system_id] = {
                'r2': None,
                'rmse': None,
                'n_samples': len(system_df),
                'error': 'Insufficient samples'
            }
            continue
        
        # Prepare features and target
        X = system_df[feature_columns].values
        y = system_df['segregation_energy'].values
        
        # Train a simple Linear Regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict and calculate metrics
        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        results[system_id] = {
            'r2': float(r2),
            'rmse': float(rmse),
            'n_samples': int(len(system_df)),
            'coefficients': {col: float(coef) for col, coef in zip(feature_columns, model.coef_)}
        }
        
        logger.info(f"Evaluated {system_id}: R²={r2:.4f}, RMSE={rmse:.4f}, n={len(system_df)}")
    
    return results

def save_per_system_results(
    results: Dict[str, Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save per-system evaluation results to JSON file.
    
    Args:
        results: Dict of evaluation metrics per alloy system.
        output_path: Optional output path. Defaults to results/per_system_metrics.json.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / 'results' / 'per_system_metrics.json'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved per-system results to {output_path}")
    return output_path

def run_per_system_evaluation(
    feature_columns: Optional[List[str]] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Main entry point for per-system evaluation.
    
    Args:
        feature_columns: Optional list of feature columns. Defaults to all numeric columns
                         except 'sample_id', 'species', 'segregation_energy'.
        output_path: Optional output path for results.
        
    Returns:
        Dict of evaluation metrics per alloy system.
    """
    logger.info("Starting per-system evaluation...")
    
    # Load alloy systems mapping
    alloy_systems = load_alloy_systems()
    logger.info(f"Loaded {len(alloy_systems)} alloy systems")
    
    # Load processed data
    df = load_processed_data()
    
    # Determine feature columns if not provided
    if feature_columns is None:
        # Exclude non-feature columns
        exclude_cols = {'sample_id', 'species', 'segregation_energy'}
        feature_columns = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(f"Using {len(feature_columns)} features: {feature_columns}")
    
    # Perform evaluation
    results = evaluate_per_system(df, alloy_systems, feature_columns)
    
    # Save results
    output_file = save_per_system_results(results, output_path)
    
    logger.info(f"Per-system evaluation complete. Results saved to {output_file}")
    return results

def main():
    """CLI entry point for per-system evaluation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_per_system_evaluation()
        print(f"Successfully evaluated {len(results)} alloy systems")
        print(f"Results saved to: results/per_system_metrics.json")
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {e}")
        raise

if __name__ == '__main__':
    main()
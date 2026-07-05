"""
Leave-One-Species-Out Cross-Validation for Species Distribution Models.

This module orchestrates the full LOSO cycle:
1. Iterate through each species as the held-out test set.
2. Train a Random Forest model on N-1 species using climate variables.
3. Evaluate the model on the held-out species using KNOWN trait values
   (as per Spec FR-004) combined with climate data.
4. Aggregate metrics (AUC, TSS) across all folds.
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, confusion_matrix

import src.utils.config as config
from src.utils.logging import get_logger, log_provenance, log_error
from src.modeling.metrics import calculate_auc, calculate_tss, evaluate_model
from src.analysis.collinearity import (
    load_climate_data,
    load_trait_data,
    merge_predictors,
    create_full_predictor_matrix,
    get_predictor_columns
)

# Initialize logger
logger = get_logger(__name__)

def prepare_training_data(
    climate_df: pd.DataFrame,
    trait_df: pd.DataFrame,
    exclude_species: List[str]
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare the training dataset by merging climate and trait data,
    excluding the specified held-out species.

    Args:
        climate_df: DataFrame with climate variables per occurrence.
        trait_df: DataFrame with species-level traits.
        exclude_species: List of species to exclude (the held-out one).

    Returns:
        Tuple of (feature_matrix, target_vector).
    """
    logger.info(f"Preparing training data, excluding species: {exclude_species}")

    # Filter climate data
    train_climate = climate_df[~climate_df['species'].isin(exclude_species)].copy()
    
    if train_climate.empty:
        raise ValueError(f"No training records found after excluding {exclude_species}")

    # Merge with traits (inner join ensures we only keep species with traits)
    # We assume trait_df has a 'species' column and climate_df has 'species'
    merged_data = train_climate.merge(trait_df, on='species', how='inner')

    # Check for missing values in predictor columns
    predictor_cols = get_predictor_columns(trait_df, climate_df)
    # Filter to only columns present in merged_data
    available_predictors = [c for c in predictor_cols if c in merged_data.columns]
    
    if not available_predictors:
        raise ValueError("No predictor columns found after merging climate and trait data.")

    # Drop rows with NaN in predictors
    clean_data = merged_data.dropna(subset=available_predictors)
    
    if clean_data.empty:
        raise ValueError("No valid training samples remain after dropping NaNs.")

    X = clean_data[available_predictors]
    y = clean_data['presence'] # Assuming 1=presence, 0=background/absence

    logger.info(f"Training data shape: {X.shape}")
    return X, y

def prepare_test_data(
    climate_df: pd.DataFrame,
    trait_df: pd.DataFrame,
    test_species: str
) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prepare the test dataset for the held-out species using KNOWN trait values.
    
    This function strictly adheres to Spec FR-004: it uses the actual trait values
    for the held-out species, not imputed ones.

    Args:
        climate_df: DataFrame with climate variables.
        trait_df: DataFrame with species-level traits.
        test_species: The single species to hold out.

    Returns:
        Tuple of (feature_matrix, target_vector, list_of_features_used).
    """
    logger.info(f"Preparing test data for held-out species: {test_species}")

    # Filter climate data for the specific species
    test_climate = climate_df[climate_df['species'] == test_species].copy()
    
    if test_climate.empty:
        logger.warning(f"No occurrence records found for species: {test_species}")
        return None, None, []

    # Merge with traits
    # We explicitly join on the species to get its KNOWN traits
    merged_data = test_climate.merge(trait_df, on='species', how='inner')

    if merged_data.empty:
        logger.warning(f"Species {test_species} has no known trait values in the dataset.")
        return None, None, []

    # Identify predictor columns (same logic as training)
    predictor_cols = get_predictor_columns(trait_df, climate_df)
    available_predictors = [c for c in predictor_cols if c in merged_data.columns]

    # Drop NaNs
    clean_data = merged_data.dropna(subset=available_predictors)

    if clean_data.empty:
        logger.warning(f"No valid test samples for {test_species} after cleaning.")
        return None, None, []

    X = clean_data[available_predictors]
    y = clean_data['presence']

    logger.info(f"Test data shape for {test_species}: {X.shape}")
    return X, y, available_predictors

def run_loso_cv(
    climate_data_path: str,
    trait_data_path: str,
    output_dir: str,
    species_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute the Leave-One-Species-Out Cross-Validation loop.

    Args:
        climate_data_path: Path to the pre-processed climate occurrence data (CSV).
        trait_data_path: Path to the pre-processed trait data (CSV).
        output_dir: Directory to save results.
        species_list: Optional list of species to iterate over. If None, uses all unique species.

    Returns:
        Dictionary containing aggregated results and per-fold metrics.
    """
    os.makedirs(output_dir, exist_ok=True)
    results_path = Path(output_dir) / "loso_results.json"

    logger.info(f"Starting LOSO CV. Loading data from {climate_data_path} and {trait_data_path}")

    try:
        climate_df = load_climate_data(climate_data_path)
        trait_df = load_trait_data(trait_data_path)
    except Exception as e:
        log_error(logger, "Failed to load data for LOSO", e)
        raise

    # Determine species list
    if species_list is None:
        species_list = climate_df['species'].unique().tolist()
    
    # Filter species_list to only those present in both dataframes
    valid_species = [s for s in species_list if s in climate_df['species'].unique() and s in trait_df['species'].unique()]
    
    if len(valid_species) < 2:
        raise ValueError("Need at least 2 valid species to run LOSO CV.")

    logger.info(f"Running LOSO for {len(valid_species)} species: {valid_species}")

    fold_results = []
    all_metrics = {
        'species': [],
        'auc': [],
        'tss': [],
        'n_train': [],
        'n_test': []
    }

    # Configuration
    max_depth = config.MAX_DEPTH
    n_estimators = config.N_ESTIMATORS
    random_state = config.RANDOM_SEED

    for i, holdout_species in enumerate(valid_species):
        logger.info(f"--- Fold {i+1}/{len(valid_species)}: Holding out {holdout_species} ---")
        
        try:
            # 1. Prepare Training Data (N-1 species)
            X_train, y_train = prepare_training_data(
                climate_df, trait_df, exclude_species=[holdout_species]
            )

            # 2. Prepare Test Data (1 species) using KNOWN traits
            X_test, y_test, features_used = prepare_test_data(
                climate_df, trait_df, test_species=holdout_species
            )

            if X_test is None or y_test is None:
                logger.warning(f"Skipping {holdout_species}: No valid test data.")
                continue

            # Ensure feature alignment (should be same as training if columns match)
            if set(X_train.columns) != set(X_test.columns):
                # Reorder X_test to match X_train
                X_test = X_test[X_train.columns]

            # 3. Train Model (Random Forest)
            logger.info(f"Training RF on {len(X_train)} samples (max_depth={max_depth}, n_est={n_estimators})")
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1,
                class_weight='balanced' # Handle class imbalance
            )
            model.fit(X_train, y_train)

            # 4. Evaluate
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            y_pred = (y_pred_proba > 0.5).astype(int)

            auc_score = calculate_auc(y_test, y_pred_proba)
            tss_score = calculate_tss(y_test, y_pred)

            logger.info(f"Results for {holdout_species}: AUC={auc_score:.4f}, TSS={tss_score:.4f}")

            # Store results
            fold_results.append({
                'fold': i + 1,
                'held_out_species': holdout_species,
                'auc': auc_score,
                'tss': tss_score,
                'n_train_samples': len(X_train),
                'n_test_samples': len(X_test),
                'features_used': features_used
            })

            all_metrics['species'].append(holdout_species)
            all_metrics['auc'].append(auc_score)
            all_metrics['tss'].append(tss_score)
            all_metrics['n_train'].append(len(X_train))
            all_metrics['n_test'].append(len(X_test))

        except Exception as e:
            log_error(logger, f"Error processing fold {holdout_species}", e)
            fold_results.append({
                'fold': i + 1,
                'held_out_species': holdout_species,
                'error': str(e)
            })
            continue

    # 5. Aggregate and Save
    summary = {
        'total_folds': len(valid_species),
        'successful_folds': len([r for r in fold_results if 'error' not in r]),
        'mean_auc': np.mean(all_metrics['auc']) if all_metrics['auc'] else 0,
        'std_auc': np.std(all_metrics['auc']) if all_metrics['auc'] else 0,
        'mean_tss': np.mean(all_metrics['tss']) if all_metrics['tss'] else 0,
        'std_tss': np.std(all_metrics['tss']) if all_metrics['tss'] else 0,
        'per_fold_results': fold_results
    }

    # Save to JSON
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"LOSO CV complete. Results saved to {results_path}")
    log_provenance(logger, "LOSO_CV", {
        'climate_source': climate_data_path,
        'trait_source': trait_data_path,
        'config': {
            'max_depth': max_depth,
            'n_estimators': n_estimators,
            'random_state': random_state
        }
    })

    return summary

def main():
    """Entry point for running LOSO CV from command line."""
    # Default paths (adjust based on project structure if needed)
    # Assuming data is in data/processed based on T001b
    climate_path = "data/processed/climate_occurrences_cleaned.csv"
    trait_path = "data/processed/traits_merged.csv"
    output_path = "results/loso_cv_results"

    import argparse
    parser = argparse.ArgumentParser(description="Run Leave-One-Species-Out Cross-Validation")
    parser.add_argument('--climate', type=str, default=climate_path, help='Path to climate data')
    parser.add_argument('--traits', type=str, default=trait_path, help='Path to trait data')
    parser.add_argument('--output', type=str, default=output_path, help='Output directory')
    parser.add_argument('--species', type=str, nargs='+', default=None, help='Specific species to test')
    
    args = parser.parse_args()

    # Convert species list if provided
    species_list = args.species if args.species else None

    run_loso_cv(
        climate_data_path=args.climate,
        trait_data_path=args.traits,
        output_dir=args.output,
        species_list=species_list
    )

if __name__ == "__main__":
    main()
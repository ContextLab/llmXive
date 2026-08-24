import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Import from local utils
from utils.config import get_path, ensure_directories, get_config_dict
from utils.metrics import (
    expected_calibration_error,
    brier_score,
    pca_shift,
    key_feature_shift,
    spearman_correlation
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_models(models_dir: str) -> Dict[str, Any]:
    """Load trained models from the specified directory."""
    models = {}
    models_path = Path(models_dir)
    
    model_files = {
        'logistic_regression': 'logistic_regression.pkl',
        'random_forest': 'random_forest.pkl'
    }
    
    for name, filename in model_files.items():
        filepath = models_path / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            models[name] = pickle.load(f)
            logger.info(f"Loaded model: {name}")
    
    return models


def load_yearly_test_splits(data_dir: str) -> Dict[int, Dict[str, Any]]:
    """
    Load yearly test splits from data/processed/.
    Handles missing years gracefully by logging a warning and skipping them.
    
    Returns a dictionary mapping year -> {X: array, y: array, year: int}
    """
    processed_dir = Path(data_dir)
    yearly_data = {}
    available_years = []
    
    # Determine range of years based on available files
    # We expect files named test_data_{year}.json
    all_files = list(processed_dir.glob("test_data_*.json"))
    extracted_years = []
    
    for f in all_files:
        try:
            year_str = f.stem.replace("test_data_", "")
            year = int(year_str)
            extracted_years.append(year)
        except ValueError:
            continue
    
    if not extracted_years:
        logger.warning("No yearly test split files found in data/processed/")
        return {}
    
    min_year = min(extracted_years)
    max_year = max(extracted_years)
    
    logger.info(f"Scanning years from {min_year} to {max_year}")
    
    for year in range(min_year, max_year + 1):
        filepath = processed_dir / f"test_data_{year}.json"
        
        if not filepath.exists():
            # GRACEFUL HANDLING OF MISSING YEARS (T025)
            logger.warning(
                f"Missing year {year}: Test split file not found at {filepath}. "
                f"Skipping processing for this year as per edge case handling."
            )
            continue
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if 'X' not in data or 'y' not in data:
                logger.warning(
                    f"Skipping year {year}: Invalid data format in {filepath}. "
                    f"Expected 'X' and 'y' keys."
                )
                continue
            
            yearly_data[year] = {
                'X': data['X'],
                'y': data['y'],
                'year': year
            }
            available_years.append(year)
            logger.info(f"Loaded test data for year {year}")
            
        except json.JSONDecodeError as e:
            logger.warning(
                f"Skipping year {year}: Failed to parse JSON in {filepath}. Error: {e}"
            )
            continue
        except Exception as e:
            logger.warning(
                f"Skipping year {year}: Unexpected error loading {filepath}. Error: {e}"
            )
            continue
    
    if not available_years:
        logger.error("No valid test data could be loaded for any year.")
    
    return yearly_data


def compute_shift_metrics(
    train_features: List[List[float]],
    test_features: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> Dict[str, float]:
    """Compute covariate shift metrics (PCA shift and Key Feature Shift)."""
    try:
        pca_val = pca_shift(train_features, test_features)
        key_val = key_feature_shift(train_features, test_features, feature_names)
        
        return {
            'pca_shift': float(pca_val),
            'key_feature_shift': float(key_val)
        }
    except Exception as e:
        logger.warning(f"Could not compute shift metrics: {e}")
        return {
            'pca_shift': None,
            'key_feature_shift': None
        }


def compute_metrics_for_year(
    model_name: str,
    model: Any,
    year_data: Dict[str, Any],
    train_features: List[List[float]],
    feature_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute all calibration and shift metrics for a single year.
    
    Returns a record dictionary compatible with metric_record_schema.yaml.
    """
    year = year_data['year']
    X_test = year_data['X']
    y_test = year_data['y']
    
    # Predict probabilities and labels
    try:
        if hasattr(model, 'predict_proba'):
            y_prob = model.predict_proba(X_test)[:, 1]
        else:
            # Fallback for models without predict_proba
            y_prob = model.decision_function(X_test)
            # Normalize if necessary (simple sigmoid for now if not already prob)
            # In practice, we assume LogisticRegression/RF provide probs
        
        y_pred = (y_prob >= 0.5).astype(int)
    except Exception as e:
        logger.error(f"Prediction failed for year {year}, model {model_name}: {e}")
        return None
    
    # Calibration Metrics
    ece_5 = expected_calibration_error(y_test, y_prob, n_bins=5)
    ece_10 = expected_calibration_error(y_test, y_prob, n_bins=10)
    ece_20 = expected_calibration_error(y_test, y_prob, n_bins=20)
    brier = brier_score(y_test, y_prob)
    
    # Covariate Shift Metrics
    shift_metrics = compute_shift_metrics(train_features, X_test, feature_names)
    
    # Spearman Correlation (Rho) for each binning strategy
    # We compute correlation between binned predictions and true labels within each bin?
    # Actually, per T024 spec: rho is the correlation between bin centers and observed rates?
    # Standard ECE calculation involves bins. We compute rho as Spearman correlation
    # between the average predicted probability in each bin and the actual fraction of positives in that bin.
    
    def compute_rho(y_true, y_prob, n_bins):
        # Bin the predictions
        bins = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)
        
        rho_vals = []
        for i in range(n_bins):
            mask = bin_indices == i
            if np.sum(mask) > 1:
                pred_mean = np.mean(y_prob[mask])
                true_mean = np.mean(y_true[mask])
                # We need multiple points to compute correlation, but here we have one point per bin (mean vs mean)
                # This is a degenerate correlation (n=1). 
                # Correction: The task likely implies computing correlation over the *time series* later,
                # or computing rho as a measure of alignment within the binning.
                # However, T024 says "rho_5, rho_10, rho_20" are stored per year.
                # Interpretation: rho is the Spearman correlation between the bin centers and the observed rates.
                # But with one point per bin, correlation is undefined.
                # Alternative: Maybe it's the correlation of the residuals?
                # Let's assume the standard "reliability diagram" correlation:
                # We collect (bin_center, observed_rate) for all bins with data.
                # If we have < 2 bins with data, rho is 0 or NaN.
                pass
        
        # Re-implementation for robust rho calculation per binning strategy
        bin_centers = []
        observed_rates = []
        
        for i in range(n_bins):
            mask = bin_indices == i
            if np.sum(mask) > 0:
                bin_centers.append((bins[i] + bins[i+1]) / 2)
                observed_rates.append(np.mean(y_true[mask]))
        
        if len(bin_centers) < 2:
            return 0.0
        
        rho, _ = spearman_correlation(np.array(bin_centers), np.array(observed_rates))
        return rho
    
    rho_5 = compute_rho(y_test, y_prob, 5)
    rho_10 = compute_rho(y_test, y_prob, 10)
    rho_20 = compute_rho(y_test, y_prob, 20)
    
    # Compute differences
    rho_diff_5_10 = abs(rho_5 - rho_10)
    rho_diff_10_20 = abs(rho_10 - rho_20)
    max_rho_diff = max(rho_diff_5_10, rho_diff_10_20)
    
    record = {
        'year': year,
        'model_type': model_name,
        'ece_5': ece_5,
        'ece_10': ece_10,
        'ece_20': ece_20,
        'brier': brier,
        'pca_shift': shift_metrics['pca_shift'],
        'key_feature_shift': shift_metrics['key_feature_shift'],
        'rho_5': rho_5,
        'rho_10': rho_10,
        'rho_20': rho_20,
        'rho_diff_5_10': rho_diff_5_10,
        'rho_diff_10_20': rho_diff_10_20,
        'max_rho_diff': max_rho_diff,
        'p_value_wls': None, # Computed later in T026
        'change_point_year': None # Computed later in T028
    }
    
    return record


def run_evaluation_pipeline(
    config_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> bool:
    """
    Main pipeline to evaluate models across all available years.
    Handles missing years gracefully.
    """
    config = get_config_dict(config_path)
    
    models_dir = get_path(config, 'paths.models_dir')
    data_dir = get_path(config, 'paths.processed_dir')
    output_file = output_path or get_path(config, 'paths.metrics_output')
    
    ensure_directories([output_file])
    
    logger.info("Loading models...")
    models = load_models(models_dir)
    
    logger.info("Loading yearly test splits (handling missing years)...")
    yearly_splits = load_yearly_test_splits(data_dir)
    
    if not yearly_splits:
        logger.error("No test data available. Aborting evaluation.")
        return False
    
    # Load training features for shift calculation (from the earliest year)
    # We assume the first available year in splits is the training year or we load from a specific file
    # For shift calculation, we need the training set features.
    # Assumption: The first year's test data is used as a proxy for training distribution if not explicitly saved,
    # OR we load 'train_data_{earliest_year}.json' if it exists.
    # Per T017, we saved test splits. We need training features.
    # Let's try to load training data for the earliest year.
    earliest_year = min(yearly_splits.keys())
    train_file = Path(data_dir) / f"train_data_{earliest_year}.json"
    
    train_features = None
    feature_names = None
    
    if train_file.exists():
        with open(train_file, 'r') as f:
            train_data = json.load(f)
            train_features = train_data.get('X')
            feature_names = train_data.get('feature_names')
        logger.info(f"Loaded training features from {earliest_year}")
    else:
        # Fallback: Use the earliest test set as the reference distribution for shift
        # This is a limitation, but necessary if training data isn't persisted separately
        logger.warning(
            f"Training data file {train_file} not found. "
            f"Using earliest test year ({earliest_year}) as reference for shift calculation."
        )
        train_features = yearly_splits[earliest_year]['X']
        # feature_names might be missing, handled in metrics.py
    
    all_records = []
    
    for model_name, model in models.items():
        logger.info(f"Evaluating model: {model_name}")
        
        for year in sorted(yearly_splits.keys()):
            year_data = yearly_splits[year]
            
            try:
                record = compute_metrics_for_year(
                    model_name, model, year_data, train_features, feature_names
                )
                
                if record:
                    all_records.append(record)
                    logger.info(f"  Computed metrics for {year} ({model_name})")
                else:
                    logger.warning(f"  Skipped {year} for {model_name} due to computation error")
                    
            except Exception as e:
                logger.error(f"  Error processing year {year} for {model_name}: {e}")
                continue
    
    if not all_records:
        logger.error("No metrics records were generated.")
        return False
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(all_records, f, indent=2)
    
    logger.info(f"Evaluation complete. Results saved to {output_file}")
    return True


def main():
    """Entry point for script execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate calibration drift over time")
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--output', type=str, help='Output file path')
    args = parser.parse_args()
    
    success = run_evaluation_pipeline(
        config_path=args.config,
        output_path=args.output
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    import sys
    main()

import pickle
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor
from compositional import ilr, ilr_inv
from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def load_trained_model(model_path: str) -> RandomForestRegressor:
    """Load the trained Random Forest model."""
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def extract_feature_importance(model: RandomForestRegressor) -> Dict[str, float]:
    """Extract feature importance from the Random Forest model."""
    importance_scores = model.feature_importances_
    # Feature names are assumed to be the ILR components (ilr_0, ilr_1, etc.)
    # We return the mapping for now; actual mapping to elements happens in perturbation analysis
    feature_names = [f"ilr_{i}" for i in range(len(importance_scores))]
    return dict(zip(feature_names, importance_scores))

def save_importance_results(importance: Dict[str, float], output_path: str) -> None:
    """Save feature importance results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(importance, f, indent=2)
    logger.info(f"Saved feature importance to {output_path}")

def run_permutation_importance(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray, n_repeats: int = 10, random_state: int = 42) -> np.ndarray:
    """Run permutation importance on ILR features."""
    logger.info("Running permutation importance on ILR features")
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=random_state, scoring='neg_mean_absolute_error')
    return result.importances_mean

def save_permutation_results(scores: np.ndarray, output_path: str) -> None:
    """Save permutation importance results to a CSV file."""
    df = pd.DataFrame({'feature': [f'ilr_{i}' for i in range(len(scores))], 'score': scores})
    df.to_csv(output_path, index=False)
    logger.info(f"Saved permutation importance to {output_path}")

def run_importance_analysis(model: RandomForestRegressor, X_ilr: np.ndarray, y: np.ndarray, output_path: str) -> None:
    """Run baseline importance analysis (permutation) and save results."""
    perm_scores = run_permutation_importance(model, X_ilr, y)
    save_permutation_results(perm_scores, output_path)

def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """Calculate Variance Inflation Factor (VIF) for predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Exclude intercept column if present
    if 'intercept' in X.columns:
        X = X.drop('intercept', axis=1)
        
    vif_data = pd.DataFrame()
    vif_data["Feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    return vif_data

def save_vif_results(vif_df: pd.DataFrame, output_path: str) -> None:
    """Save VIF results to a JSON file."""
    # Convert to dict for JSON serialization
    vif_dict = vif_df.to_dict(orient='records')
    with open(output_path, 'w') as f:
        json.dump(vif_dict, f, indent=2)
    logger.info(f"Saved VIF results to {output_path}")

def rank_and_compare_importance(element_importance: Dict[str, float], baseline_importance: Dict[str, float]) -> List[Tuple[str, float, float]]:
    """Rank elements by importance and compare with baseline."""
    # Sort by importance descending
    ranked = sorted(element_importance.items(), key=lambda x: x[1], reverse=True)
    # Compare with baseline (if available)
    comparison = []
    for elem, score in ranked:
        baseline_score = baseline_importance.get(elem, 0.0)
        comparison.append((elem, score, baseline_score))
    return comparison

def save_ranking_results(ranked_data: List[Tuple[str, float, float]], output_path: str) -> None:
    """Save ranking results to a CSV file."""
    df = pd.DataFrame(ranked_data, columns=['element', 'importance_score', 'baseline_score'])
    df.to_csv(output_path, index=False)
    logger.info(f"Saved ranking results to {output_path}")

def run_perturbation_sensitivity_analysis(model: RandomForestRegressor, data_path: str, output_path: str, random_state: int = 42) -> None:
    """
    Implement Perturbation-Based Sensitivity Analysis (T027b).
    
    Algorithm:
    1. Load raw composition data from `data_path` (alloys_clean.parquet).
    2. For each element e in [Cu, Mg, Si, Zn, Mn]:
       a. Perturb raw composition by adding Gaussian noise (sigma=0.01 * value).
       b. Re-transform perturbed composition to ILR space.
       c. Predict using the trained model.
       d. Compute loss change: |Prediction(original) - Prediction(noised_e)|.
       e. Average loss change over all samples.
    3. Sort elements by average loss change (descending) to produce ranking.
    4. Save results to `output_path`.
    """
    logger.info("Starting Perturbation-Based Sensitivity Analysis (T027b)")
    
    # Load configuration for paths
    config = get_config()
    
    # Load the clean dataset
    logger.info(f"Loading clean data from {data_path}")
    df = pd.read_parquet(data_path)
    
    # Define elements to perturb (excluding Al balance)
    elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    # Ensure we have the necessary composition columns
    missing_cols = [e for e in elements if e not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing composition columns in data: {missing_cols}")
    
    # Prepare original compositions for ILR transformation
    # We need to normalize the compositions to sum to 1.0 (atomic fractions)
    # Assuming the data is already normalized per T012/T013, but verify
    composition_cols = elements + ['Al']
    if 'Al' not in df.columns:
        # Calculate Al as balance if not present
        df['Al'] = 1.0 - df[elements].sum(axis=1)
    
    # Verify sum is ~1.0
    total_sum = df[composition_cols].sum(axis=1)
    if not np.allclose(total_sum, 1.0, atol=1e-5):
        logger.warning("Composition sums are not exactly 1.0. Normalizing...")
        df[composition_cols] = df[composition_cols].div(total_sum, axis=0)
    
    # Prepare original data for ILR transformation
    original_compositions = df[composition_cols].values
    
    # Transform original compositions to ILR space
    logger.info("Transforming original compositions to ILR space")
    original_ilr = ilr(original_compositions)
    
    # Get original predictions
    logger.info("Computing original predictions")
    original_predictions = model.predict(original_ilr)
    
    # Initialize results storage
    importance_scores = {}
    std_devs = {}
    
    # Perturb each element independently
    for element in elements:
        logger.info(f"Perturbing element: {element}")
        
        # Get index of the element in composition_cols
        elem_idx = composition_cols.index(element)
        
        # Perturb the specific element's composition
        # Noise: Gaussian with sigma = 0.01 * value
        noise = np.random.normal(0, 0.01 * original_compositions[:, elem_idx], size=original_compositions[:, elem_idx].shape)
        
        # Create perturbed compositions
        perturbed_compositions = original_compositions.copy()
        perturbed_compositions[:, elem_idx] += noise
        
        # Re-normalize to ensure sum is 1.0 (important for compositional data)
        perturbed_sums = perturbed_compositions.sum(axis=1, keepdims=True)
        perturbed_compositions = perturbed_compositions / perturbed_sums
        
        # Transform perturbed compositions to ILR space
        perturbed_ilr = ilr(perturbed_compositions)
        
        # Get predictions on perturbed data
        perturbed_predictions = model.predict(perturbed_ilr)
        
        # Compute loss change (absolute difference)
        loss_change = np.abs(original_predictions - perturbed_predictions)
        
        # Aggregate: mean absolute loss change
        mean_importance = np.mean(loss_change)
        std_importance = np.std(loss_change)
        
        importance_scores[element] = mean_importance
        std_devs[element] = std_importance
        
        logger.info(f"  {element}: Importance = {mean_importance:.6f}, Std = {std_importance:.6f}")
    
    # Sort elements by importance (descending)
    sorted_elements = sorted(importance_scores.keys(), key=lambda x: importance_scores[x], reverse=True)
    
    # Prepare output DataFrame
    output_data = []
    for elem in sorted_elements:
        output_data.append({
            'element': elem,
            'importance_score': importance_scores[elem],
            'std_dev': std_devs[elem]
        })
    
    output_df = pd.DataFrame(output_data)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved element importance results to {output_path}")
    
    # Log comparison with baseline if baseline file exists
    baseline_path = str(Path(output_path).parent / "baseline_permutation_importance.csv")
    if Path(baseline_path).exists():
        logger.info("Comparing with baseline permutation importance...")
        # Load baseline (assuming it has ilr_0, ilr_1, etc. - we can't directly map without more work)
        # For now, just log that comparison logic would go here
        logger.info("Baseline comparison requires mapping ILR features to elements (future work)")

def validate_framing(report_path: str) -> Dict[str, Any]:
    """Validate that the final report contains required associational framing phrases."""
    required_phrases = [
        "associational relationship",
        "statistical association",
        "correlates with",
        "linked to",
        "associated with"
    ]
    
    with open(report_path, 'r') as f:
        content = f.read().lower()
    
    found_phrases = []
    missing_phrases = []
    
    for phrase in required_phrases:
        if phrase in content:
            found_phrases.append(phrase)
        else:
            missing_phrases.append(phrase)
    
    framing_verified = len(missing_phrases) == 0
    
    result = {
        'framing_verified': framing_verified,
        'found_phrases': found_phrases,
        'missing_phrases': missing_phrases
    }
    
    return result

def main():
    """Main entry point for analysis tasks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run analysis tasks")
    parser.add_argument('--task', type=str, required=True, help="Task to run: perturbation, vif, validate")
    parser.add_argument('--model-path', type=str, default='models/rf_model.pkl', help="Path to trained model")
    parser.add_argument('--data-path', type=str, default='data/processed/alloys_clean.parquet', help="Path to clean data")
    parser.add_argument('--output-path', type=str, help="Output path for results")
    parser.add_argument('--report-path', type=str, default='results/final_report.md', help="Path to final report")
    
    args = parser.parse_args()
    
    if args.task == 'perturbation':
        if not args.output_path:
            args.output_path = 'results/element_importance.csv'
        
        model = load_trained_model(args.model_path)
        run_perturbation_sensitivity_analysis(model, args.data_path, args.output_path)
        
    elif args.task == 'vif':
        # VIF calculation would go here
        logger.info("VIF calculation not fully implemented in this task")
        
    elif args.task == 'validate':
        if not args.report_path:
            args.report_path = 'results/final_report.md'
        
        result = validate_framing(args.report_path)
        output_path = 'results/associational_framing_check.json'
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Saved framing validation to {output_path}")
        
        if not result['framing_verified']:
            logger.warning(f"Framing verification failed. Missing phrases: {result['missing_phrases']}")
            return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
import os
import sys
import json
import logging
import pickle
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.inspection import permutation_importance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_filtered_data_for_importance(train_path: str = "data/processed/filtered_train.csv",
                                    test_path: str = "data/processed/filtered_test.csv") -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load filtered training and test data for importance analysis."""
    try:
        train_data = np.load(train_path, allow_pickle=True).item()
        test_data = np.load(test_path, allow_pickle=True).item()
        
        X_train = train_data['features']
        y_train = train_data['labels']
        X_test = test_data['features']
        y_test = test_data['labels']
        
        logger.info(f"Loaded {len(y_train)} training samples and {len(y_test)} test samples for importance analysis")
        return X_train, y_train, X_test, y_test
    except Exception as e:
        logger.error(f"Error loading filtered data for importance: {e}")
        raise

def load_baseline_distribution(path: str = "data/processed/baseline_f1.json") -> Dict[str, Any]:
    """Load baseline distribution from JSON file."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading baseline distribution: {e}")
        raise

def load_classifier(model_path: str = "data/processed/classifier.pkl") -> Any:
    """Load trained classifier from pickle file."""
    try:
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading classifier: {e}")
        raise

def compute_shap_values(model: Any, X_train: np.ndarray, X_test: np.ndarray, 
                       feature_names: List[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Compute SHAP values for feature importance."""
    try:
        # Create SHAP explainer
        explainer = shap.Explainer(model, X_train)
        
        # Compute SHAP values for test set
        shap_values = explainer(X_test)
        
        logger.info(f"Computed SHAP values with shape: {shap_values.values.shape}")
        return shap_values.values, shap_values
    except Exception as e:
        logger.error(f"Error computing SHAP values: {e}")
        raise

def compute_permutation_importance(model: Any, X_test: np.ndarray, y_test: np.ndarray,
                                  feature_names: List[str] = None) -> np.ndarray:
    """Compute permutation importance for feature importance."""
    try:
        result = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
        logger.info(f"Computed permutation importance with mean shape: {result.importances_mean.shape}")
        return result.importances_mean
    except Exception as e:
        logger.error(f"Error computing permutation importance: {e}")
        raise

def analyze_importance_against_baseline(shap_values: np.ndarray, permutation_importance: np.ndarray,
                                       baseline_data: Dict[str, Any], feature_names: List[str]) -> Dict[str, Any]:
    """Analyze feature importance against baseline."""
    # Calculate mean absolute SHAP values
    mean_shap = np.abs(shap_values).mean(axis=0)
    
    # Create importance analysis
    importance_analysis = {
        "shap_importance": {
            "values": mean_shap.tolist(),
            "feature_names": feature_names
        },
        "permutation_importance": {
            "values": permutation_importance.tolist(),
            "feature_names": feature_names
        },
        "baseline_comparison": {
            "baseline_f1": baseline_data.get("baseline_f1", 0),
            "description": "Feature importance analysis compared against majority class baseline"
        },
        "top_features": []
    }
    
    # Get top 10 features by SHAP importance
    top_indices = np.argsort(mean_shap)[::-1][:10]
    for idx in top_indices:
        importance_analysis["top_features"].append({
            "feature_name": feature_names[idx] if feature_names else f"feature_{idx}",
            "shap_importance": float(mean_shap[idx]),
            "permutation_importance": float(permutation_importance[idx])
        })
    
    return importance_analysis

def generate_interpretation_report(importance_analysis: Dict[str, Any], 
                                  output_path: str = "shap_interpretation.md") -> None:
    """Generate human-readable interpretation report."""
    report = """# Feature Importance Analysis Report

## Important Note: Associational Findings Only

**This report presents associational findings only. The correlations identified between features and physical validity labels do not imply causation. These results are derived from observational data and should be interpreted as patterns of association, not causal relationships.**

## Methodology

1. **SHAP Values**: Computed using the TreeExplainer/ShapExplainer to measure feature contribution to model predictions
2. **Permutation Importance**: Measured by randomly shuffling each feature and observing the decrease in model performance
3. **Baseline Comparison**: Compared against majority class predictor baseline

## Top 10 Most Important Features

"""
    
    for i, feature in enumerate(importance_analysis["top_features"], 1):
        report += f"{i}. **{feature['feature_name']}**: SHAP={feature['shap_importance']:.4f}, Perm={feature['permutation_importance']:.4f}\n"
    
    report += f"""
## Baseline Comparison

- Baseline F1 Score (Majority Class): {importance_analysis['baseline_comparison']['baseline_f1']:.4f}
- Model Performance: See evaluation metrics for comparison

## Limitations

1. **Associational Nature**: All findings are correlational, not causal
2. **Data Limitations**: Results are specific to the dataset used
3. **Model Dependency**: Importance values are model-specific

## Conclusion

This analysis identifies features that are strongly associated with physical validity predictions. However, these associations should not be interpreted as causal relationships without further experimental validation.
"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)
    
    logger.info(f"Interpretation report saved to: {output_path}")

def main():
    """Main function to compute feature importance."""
    parser = argparse.ArgumentParser(description="Compute feature importance using SHAP and permutation")
    parser.add_argument("--train", default="data/processed/filtered_train.csv", help="Path to filtered training data")
    parser.add_argument("--test", default="data/processed/filtered_test.csv", help="Path to filtered test data")
    parser.add_argument("--model", default="data/processed/classifier.pkl", help="Path to trained classifier")
    parser.add_argument("--baseline", default="data/processed/baseline_f1.json", help="Path to baseline distribution")
    parser.add_argument("--output", default="data/processed/feature_importance.json", help="Output path for importance analysis")
    parser.add_argument("--report", default="shap_interpretation.md", help="Output path for interpretation report")
    args = parser.parse_args()
    
    logger.info("Computing feature importance...")
    
    try:
        # Load data
        X_train, y_train, X_test, y_test = load_filtered_data_for_importance(args.train, args.test)
        model = load_classifier(args.model)
        baseline_data = load_baseline_distribution(args.base)
        
        # Define feature names (adjust based on actual feature dimensions)
        n_features = X_train.shape[1]
        feature_names = [f"feature_{i}" for i in range(n_features)]
        
        # Compute SHAP values
        shap_values, shap_obj = compute_shap_values(model, X_train, X_test, feature_names)
        
        # Compute permutation importance
        perm_importance = compute_permutation_importance(model, X_test, y_test, feature_names)
        
        # Analyze importance
        importance_analysis = analyze_importance_against_baseline(shap_values, perm_importance, baseline_data, feature_names)
        
        # Save results
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(importance_analysis, f, indent=2)
        logger.info(f"Feature importance saved to: {args.output}")
        
        # Generate interpretation report
        generate_interpretation_report(importance_analysis, args.report)
        
        logger.info("Feature importance computation completed successfully")
    except Exception as e:
        logger.error(f"Feature importance computation failed: {e}")
        raise

if __name__ == "__main__":
    main()
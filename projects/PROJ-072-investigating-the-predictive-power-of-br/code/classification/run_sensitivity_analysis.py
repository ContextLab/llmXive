import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score
from scipy import stats

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from classification.sensitivity_analysis import load_analysis_config, load_features
from classification.validation import permutation_accuracy_test
from classification.cohen_d import calculate_cohen_d_for_all_features

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_sensitivity_analysis():
    """
    Re-run the classifier using data/processed/features_sim_med.csv.
    Save results to data/processed/sensitivity_results.json.
    """
    logger.info("Starting sensitivity analysis run (T031b)...")

    # 1. Load analysis config to verify prerequisites
    config_path = project_root / "data" / "metadata" / "analysis_config.json"
    try:
        config = load_analysis_config(config_path)
        if not config.get("medication_status_available"):
            logger.info("Medication status not available in original data. Proceeding with simulated data.")
        else:
            logger.warning("Medication status was available in original data. Simulated data might be redundant but proceeding as per task.")
    except FileNotFoundError:
        logger.error(f"Analysis config not found at {config_path}. T031a must be completed first.")
        raise

    # 2. Load the simulated features
    features_path = project_root / "data" / "processed" / "features_sim_med.csv"
    if not features_path.exists():
        logger.error(f"Simulated features file not found at {features_path}. T031 must be completed first.")
        raise FileNotFoundError(f"Missing required input: {features_path}")

    logger.info(f"Loading features from {features_path}")
    df = load_features(features_path)

    # Ensure we have the simulated medication column
    if 'sim_med_status' not in df.columns:
        logger.error("Column 'sim_med_status' not found in features_sim_med.csv")
        raise ValueError("Missing 'sim_med_status' column in features_sim_med.csv")

    # 3. Prepare X and y
    # The target is the diagnostic label. We assume the last column or a specific column is the target.
    # Based on T015, subject_labels.csv maps subject_id to diagnosis.
    # The features CSV likely has subject_id as index or first column, and diagnosis might be included or separate.
    # Let's assume the standard pipeline output: first column is subject_id, last column is diagnosis (0/1), rest are features.
    # Or, we load labels separately.
    # Looking at T026/T027, the classification pipeline usually takes X (features) and y (labels).
    # Let's assume the file has a 'diagnosis' column or we need to load it.
    # Given T031 appends to features.csv, and features.csv comes from T022 which assembles features.
    # T022 usually joins with labels. Let's check if 'diagnosis' is in df.
    if 'diagnosis' in df.columns:
        y = df['diagnosis'].values
        X = df.drop(columns=['diagnosis', 'subject_id', 'sim_med_status']).values
    else:
        # Fallback: assume last column is diagnosis if not explicitly named, or load from external file
        # But T015 generates subject_labels.csv. Let's try to load it.
        labels_path = project_root / "data" / "metadata" / "subject_labels.csv"
        if labels_path.exists():
            labels_df = pd.read_csv(labels_path)
            # Merge on subject_id
            if 'subject_id' in df.columns:
                df = df.merge(labels_df[['subject_id', 'diagnosis']], on='subject_id', how='inner')
                y = df['diagnosis'].values
                X = df.drop(columns=['diagnosis', 'subject_id', 'sim_med_status']).values
            else:
                logger.error("Cannot merge labels: 'subject_id' column missing in features file.")
                raise ValueError("Missing 'subject_id' in features file")
        else:
            logger.error("Cannot find subject_labels.csv to extract y.")
            raise FileNotFoundError("Missing subject_labels.csv")

    logger.info(f"Dataset shape: X={X.shape}, y={y.shape}")
    if len(np.unique(y)) < 2:
        logger.error("Only one class found in y. Cannot run classification.")
        raise ValueError("Insufficient classes for classification")

    # 4. Run Classification (Logistic Regression with Stratified CV)
    # Using a simple pipeline similar to T026/T029 logic
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    accuracies = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = LogisticRegression(max_iter=1000, random_state=42, solver='lbfgs')
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        accuracies.append(acc)

    mean_accuracy = float(np.mean(accuracies))
    logger.info(f"Cross-validated Accuracy: {mean_accuracy:.4f}")

    # 5. Run Permutation Test for Significance
    logger.info("Running permutation test for accuracy significance...")
    # Use a subset of permutations for speed if N is large, but task says "sufficient"
    # Let's do 1000 as a standard sufficient number
    p_value = permutation_accuracy_test(y, X, n_permutations=1000, random_state=42)
    logger.info(f"Permutation p-value: {p_value:.4f}")

    # 6. Calculate Cohen's d
    # Calculate Cohen's d for the main feature(s) or a composite score?
    # T030 calculates Cohen's d for all features. T031b asks for "cohen_d_value".
    # Usually, this refers to the effect size of the classifier's separation or the main feature.
    # Given the context of "sensitivity analysis", we might calculate the d for the difference in the simulated covariate's effect or the main classification effect.
    # However, the schema asks for a single float. Let's calculate Cohen's d for the first feature (or a representative one) between groups,
    # OR, more likely, the effect size of the classification outcome if we treat the predicted probabilities as a continuous measure?
    # Re-reading T030: "Calculate Cohen's d for significant group differences".
    # Let's calculate the Cohen's d of the *first* feature (or the mean of all features) between the two groups to represent the effect size.
    # A more robust interpretation: The effect size of the difference in the *outcome* (diagnosis) on the *features*?
    # Let's stick to the most standard interpretation in this pipeline: Cohen's d for the separation of the groups on the *first* feature or a composite.
    # Actually, T030 saves "cohen_d_results.json". T031b asks for "cohen_d_value".
    # Let's calculate the Cohen's d for the difference in the *mean feature vector* magnitude? No.
    # Let's calculate it for the first feature as a representative, or the average of all features.
    # To be safe and consistent with T030's "for all features", let's pick the feature with the highest absolute t-stat (most discriminative) and report its d.
    # Or simpler: Calculate d for the first feature (index 0) as a proxy if we can't determine the "main" one.
    # Let's calculate the mean of the absolute Cohen's d across all features to represent the "overall" effect size.
    cohen_d_results = calculate_cohen_d_for_all_features(X, y)
    # cohen_d_results is a dict {feature_idx: d_value}. Let's take the mean of the absolute values.
    if cohen_d_results:
        d_values = list(cohen_d_results.values())
        mean_cohen_d = float(np.mean(np.abs(d_values)))
    else:
        mean_cohen_d = 0.0
    
    logger.info(f"Mean Absolute Cohen's d: {mean_cohen_d:.4f}")

    # 7. Save Results
    output_path = project_root / "data" / "processed" / "sensitivity_results.json"
    results = {
        "accuracy": round(mean_accuracy, 4),
        "p_value": round(p_value, 4),
        "cohen_d_value": round(mean_cohen_d, 4)
    }

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis results saved to {output_path}")
    return results

def main():
    try:
        run_sensitivity_analysis()
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
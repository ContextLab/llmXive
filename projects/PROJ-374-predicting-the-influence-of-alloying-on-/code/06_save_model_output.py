"""
Task T030: Save model metrics, feature importances, and correlations to data/processed/model_output.json.

This script aggregates results from previous pipeline steps:
- CV fold scores from state/cv_fold_scores.json (for CI calculation)
- Permutation p-value from state/permutation_pvalue.json
- F-test results from state/f_test_results.json
- Feature importances from state/feature_importances.json
- Correlations from state/correlations.json
- R2 score (derived from mean of CV fold scores or saved in state)

It produces a single consolidated JSON file at data/processed/model_output.json.
"""
import os
import sys
import json
import numpy as np
from pathlib import Path

# Add project root to path to allow imports if needed, though this script is self-contained
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_json_file(filepath):
    """Load and return JSON data from a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_confidence_interval(scores, confidence=0.95):
    """Calculate confidence interval from a list of scores (e.g., CV fold scores)."""
    scores_array = np.array(scores)
    lower = np.percentile(scores_array, (1 - confidence) / 2 * 100)
    upper = np.percentile(scores_array, (1 + confidence) / 2 * 100)
    return lower, upper

def main():
    print("Starting T030: Aggregating model metrics...")

    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load CV Fold Scores to calculate R2 and CI
    # T025 saves individual fold R2 scores here
    cv_scores_path = STATE_DIR / "cv_fold_scores.json"
    try:
        cv_data = load_json_file(cv_scores_path)
        # Expecting a list of scores or a dict with a 'scores' key
        if isinstance(cv_data, dict) and 'scores' in cv_data:
            fold_scores = cv_data['scores']
        elif isinstance(cv_data, list):
            fold_scores = cv_data
        else:
            # Fallback: try to find any list-like value
            fold_scores = list(cv_data.values())[0] if cv_data else []
        
        if not fold_scores:
            raise ValueError("No CV fold scores found in state/cv_fold_scores.json")
        
        fold_scores = [float(s) for s in fold_scores]
        r2_score = float(np.mean(fold_scores))
        ci_lower, ci_upper = calculate_confidence_interval(fold_scores)
        print(f"Calculated R2: {r2_score:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    except FileNotFoundError:
        print("ERROR: cv_fold_scores.json not found. T025 must be completed first.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR processing CV scores: {e}")
        sys.exit(1)

    # 2. Load Permutation P-value
    # T026a saves permutation results here
    perm_pval_path = STATE_DIR / "permutation_pvalue.json"
    try:
        perm_data = load_json_file(perm_pval_path)
        if isinstance(perm_data, dict) and 'p_value' in perm_data:
            p_value = float(perm_data['p_value'])
        elif isinstance(perm_data, (int, float)):
            p_value = float(perm_data)
        else:
            p_value = float(perm_data.get('p_value', perm_data))
        print(f"Loaded Permutation P-value: {p_value:.4f}")
    except FileNotFoundError:
        print("WARNING: permutation_pvalue.json not found. Setting p_value to 1.0 (Not Significant).")
        p_value = 1.0
    except Exception as e:
        print(f"ERROR processing permutation p-value: {e}")
        p_value = 1.0

    # 3. Load F-test Results
    # T027 saves F-test results here
    f_test_path = STATE_DIR / "f_test_results.json"
    try:
        f_data = load_json_file(f_test_path)
        if isinstance(f_data, dict):
            f_statistic = float(f_data.get('f_statistic', 0.0))
            f_p_value = float(f_data.get('p_value', 1.0))
        else:
            # Fallback for unexpected format
            f_statistic = 0.0
            f_p_value = 1.0
        print(f"Loaded F-test: F={f_statistic:.4f}, p={f_p_value:.4f}")
    except FileNotFoundError:
        print("WARNING: f_test_results.json not found. Setting F-stats to 0.")
        f_statistic = 0.0
        f_p_value = 1.0
    except Exception as e:
        print(f"ERROR processing F-test results: {e}")
        f_statistic = 0.0
        f_p_value = 1.0

    # 4. Load Feature Importances
    # T028 saves feature importances here
    feat_imp_path = STATE_DIR / "feature_importances.json"
    try:
        imp_data = load_json_file(feat_imp_path)
        if isinstance(imp_data, dict) and 'importances' in imp_data:
            feature_importances = imp_data['importances']
        elif isinstance(imp_data, list):
            feature_importances = imp_data
        else:
            # Try to convert dict to list of dicts if it's a flat mapping
            if isinstance(imp_data, dict):
                feature_importances = [{"feature": k, "importance": v} for k, v in imp_data.items()]
            else:
                feature_importances = []
        print(f"Loaded {len(feature_importances)} feature importances.")
    except FileNotFoundError:
        print("WARNING: feature_importances.json not found. Setting empty list.")
        feature_importances = []
    except Exception as e:
        print(f"ERROR processing feature importances: {e}")
        feature_importances = []

    # 5. Load Correlations
    # T029 saves correlations here
    corr_path = STATE_DIR / "correlations.json"
    try:
        corr_data = load_json_file(corr_path)
        if isinstance(corr_data, dict) and 'correlations' in corr_data:
            correlations = corr_data['correlations']
        elif isinstance(corr_data, list):
            correlations = corr_data
        else:
            if isinstance(corr_data, dict):
                correlations = [{"feature": k, "correlation": v} for k, v in corr_data.items()]
            else:
                correlations = []
        print(f"Loaded {len(correlations)} correlations.")
    except FileNotFoundError:
        print("WARNING: correlations.json not found. Setting empty list.")
        correlations = []
    except Exception as e:
        print(f"ERROR processing correlations: {e}")
        correlations = []

    # 6. Assemble Final Output
    output_data = {
        "r2_score": r2_score,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "p_value": p_value,
        "f_statistic": f_statistic,
        "f_p_value": f_p_value,
        "feature_importances": feature_importances,
        "correlations": correlations
    }

    # 7. Write to data/processed/model_output.json
    output_path = PROCESSED_DIR / "model_output.json"
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully saved model output to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
import os
import sys
import json
import logging
from pathlib import Path

from analyze_explainability import (
    load_model,
    load_data,
    find_best_model,
    calculate_shap_and_plot,
    perform_permutation_importance,
    calculate_bootstrap_shap_ci,
    calculate_p_values_and_significance,
)
from utils import setup_logging, load_state, update_state, compute_file_hash

# Ensure paths are relative to project root if run from subdirectories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "artifacts"
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results" / "reports"
STATE_FILE = PROJECT_ROOT / "state" / "state.yaml"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_significance_report(
    feature_importance: dict,
    p_values: dict,
    confidence_intervals: dict,
    output_path: Path,
) -> None:
    """
    Save the statistical significance report to a JSON file.

    Args:
        feature_importance: Dictionary of feature names to permutation importance scores.
        p_values: Dictionary of feature names to p-values from bootstrap tests.
        confidence_intervals: Dictionary of feature names to (lower, upper) CI tuples.
        output_path: Path where the JSON report will be saved.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "feature_importance": feature_importance,
        "p_values": p_values,
        "confidence_intervals": confidence_intervals,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Significance report saved to {output_path}")

def main():
    logger.info("Starting significance report generation (T035)...")

    # 1. Load the best model
    logger.info("Loading best model...")
    model_path = find_best_model(MODELS_DIR)
    if not model_path:
        logger.error("No trained model found in models/artifacts/")
        sys.exit(1)
    model, model_type = load_model(model_path)
    logger.info(f"Loaded model: {model_type} from {model_path}")

    # 2. Load the processed data
    logger.info("Loading processed data...")
    data_path = DATA_DIR / "cleaned_316L.csv"
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}")
        sys.exit(1)
    X, y, feature_names = load_data(data_path)
    logger.info(f"Loaded data with {X.shape[0]} samples and {len(feature_names)} features")

    # 3. Perform Permutation Importance (1000 permutations)
    logger.info("Performing Permutation Importance (1000 permutations)...")
    perm_scores = perform_permutation_importance(model, X, y, n_repeats=1000, random_state=42)
    feature_importance = {name: float(score) for name, score in zip(feature_names, perm_scores)}
    logger.info(f"Permutation importance computed for {len(feature_names)} features.")

    # 4. Calculate Bootstrap SHAP CIs (1000 iterations)
    logger.info("Calculating Bootstrap SHAP Confidence Intervals (1000 iterations)...")
    shap_values, ci_lower, ci_upper = calculate_bootstrap_shap_ci(model, X, n_iterations=1000, random_state=42)
    confidence_intervals = {
        name: (float(lower), float(upper))
        for name, lower, upper in zip(feature_names, ci_lower, ci_upper)
    }
    logger.info("Bootstrap CIs calculated.")

    # 5. Calculate p-values and significance
    logger.info("Calculating p-values and statistical significance...")
    p_values, significant_features = calculate_p_values_and_significance(
        shap_values, ci_lower, ci_upper, alpha=0.05
    )
    p_values_dict = {name: float(p) for name, p in zip(feature_names, p_values)}
    logger.info(f"Found {len(significant_features)} significant features at alpha=0.05")

    # 6. Save the report
    output_path = RESULTS_DIR / "significance_report.json"
    save_significance_report(feature_importance, p_values_dict, confidence_intervals, output_path)

    # 7. Update state.yaml
    if STATE_FILE.exists():
        state = load_state(STATE_FILE)
        file_hash = compute_file_hash(output_path)
        state["artifacts"]["significance_report"] = {
            "path": str(output_path.relative_to(PROJECT_ROOT)),
            "hash": file_hash,
            "timestamp": str(Path(output_path).stat().st_mtime),
        }
        update_state(STATE_FILE, state)
        logger.info("State updated with significance report hash.")
    else:
        logger.warning(f"State file not found at {STATE_FILE}, skipping update.")

    logger.info("T035 completed successfully.")

if __name__ == "__main__":
    main()
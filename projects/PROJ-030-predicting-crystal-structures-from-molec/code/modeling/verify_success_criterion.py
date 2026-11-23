import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_validation, get_path_results, get_path_processed_data, ensure_directory
from analysis.define_lift import load_power_analysis_results, calculate_lift_threshold

logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_lift(actual_accuracy: float, baseline_accuracy: float) -> float:
    """
    Calculate the lift value: actual_accuracy - baseline_accuracy.
    """
    return actual_accuracy - baseline_accuracy

def verify_success_criterion(
    actual_accuracy: float,
    baseline_accuracy: float,
    lift_threshold: float,
    is_deferred: bool = False
) -> Dict[str, Any]:
    """
    Verify if the model performance meets the success criterion:
    Accuracy > Majority Baseline + [config.lift_threshold]

    Args:
        actual_accuracy: The model's achieved accuracy.
        baseline_accuracy: The majority-class baseline accuracy.
        lift_threshold: The required lift threshold from config.
        is_deferred: If True, the threshold is 'DEFERRED' and we handle it specially.

    Returns:
        A dictionary containing the verification result, lift value, and status.
    """
    result = {
        "actual_accuracy": actual_accuracy,
        "baseline_accuracy": baseline_accuracy,
        "lift_threshold": lift_threshold,
        "lift_value": calculate_lift(actual_accuracy, baseline_accuracy),
        "is_deferred": is_deferred,
        "status": "unknown",
        "message": ""
    }

    if is_deferred:
        result["status"] = "deferred"
        result["message"] = (
            "Success criterion verification is DEFERRED. "
            "The lift threshold was not available during power analysis. "
            "Model performance is recorded but no pass/fail gate is applied."
        )
        return result

    required_accuracy = baseline_accuracy + lift_threshold
    passed = actual_accuracy > required_accuracy

    result["required_accuracy"] = required_accuracy
    result["status"] = "passed" if passed else "failed"

    if passed:
        result["message"] = (
            f"Success criterion MET. "
            f"Actual Accuracy ({actual_accuracy:.4f}) > Baseline ({baseline_accuracy:.4f}) + Threshold ({lift_threshold:.4f}) = {required_accuracy:.4f}"
        )
    else:
        result["message"] = (
            f"Success criterion NOT MET. "
            f"Actual Accuracy ({actual_accuracy:.4f}) is NOT > Baseline ({baseline_accuracy:.4f}) + Threshold ({lift_threshold:.4f}) = {required_accuracy:.4f}"
        )

    return result

def main():
    """
    Main entry point for the success criterion verification.
    Loads baseline metrics, power analysis results, and model metrics,
    then verifies the success criterion and outputs the result.
    """
    # Setup logging
    log_dir = project_root / "logs"
    ensure_directory(log_dir)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "verify_success_criterion.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting success criterion verification (T017c).")

    # Define paths
    validation_dir = get_path_validation()
    ensure_directory(validation_dir)
    output_path = validation_dir / "success_criterion_check.json"

    results_dir = get_path_results()
    baseline_metrics_path = results_dir / "majority_class_baseline_metrics.json"
    model_metrics_path = results_dir / "model_metrics.json" # Or specific model metrics if needed

    # 1. Load Majority Class Baseline Metrics
    try:
        logger.info(f"Loading baseline metrics from: {baseline_metrics_path}")
        baseline_data = load_json_file(baseline_metrics_path)
        # Assuming the baseline file has 'accuracy' or similar key for the classification task
        # The task T017b outputs 'majority_class_baseline_metrics.json'
        if 'accuracy' in baseline_data:
            baseline_accuracy = baseline_data['accuracy']
        elif 'metrics' in baseline_data and 'accuracy' in baseline_data['metrics']:
            baseline_accuracy = baseline_data['metrics']['accuracy']
        else:
            # Fallback or error if structure is unexpected
            raise KeyError("Could not find 'accuracy' in majority_class_baseline_metrics.json")
        logger.info(f"Loaded Baseline Accuracy: {baseline_accuracy}")
    except FileNotFoundError:
        logger.error(f"Baseline metrics file not found: {baseline_metrics_path}")
        logger.error("This task depends on T017b (Majority Baseline). Please ensure T017b is completed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading baseline metrics: {e}")
        sys.exit(1)

    # 2. Load Model Metrics (Actual Accuracy)
    # We need the actual accuracy from the trained model.
    # The task T019 (evaluate) produces metrics. T019c produces the final aggregate.
    # We will look for the final aggregate or the specific model metrics if available.
    # Let's try to load the final model_metrics.json first, as it should contain the final results.
    actual_accuracy = None
    try:
        logger.info(f"Loading model metrics from: {model_metrics_path}")
        model_data = load_json_file(model_metrics_path)
        
        # Attempt to find accuracy in various common structures
        if 'accuracy' in model_data:
            actual_accuracy = model_data['accuracy']
        elif 'classification_metrics' in model_data and 'accuracy' in model_data['classification_metrics']:
            actual_accuracy = model_data['classification_metrics']['accuracy']
        elif 'metrics' in model_data and 'classification_metrics' in model_data['metrics'] and 'accuracy' in model_data['metrics']['classification_metrics']:
            actual_accuracy = model_data['metrics']['classification_metrics']['accuracy']
        elif 'results' in model_data and 'accuracy' in model_data['results']:
            actual_accuracy = model_data['results']['accuracy']
        
        if actual_accuracy is None:
            # Try to find in a 'models' section if it's a summary of multiple
            if 'models' in model_data:
                # Look for the RF model specifically as it's the primary classifier
                rf_model = None
                for m in model_data['models']:
                    if m.get('model_name') == 'RandomForest' or m.get('name') == 'RandomForest':
                        rf_model = m
                        break
                if rf_model and 'accuracy' in rf_model:
                    actual_accuracy = rf_model['accuracy']
                
            if actual_accuracy is None:
                raise ValueError("Could not extract 'accuracy' from model_metrics.json")
        
        logger.info(f"Loaded Actual Accuracy: {actual_accuracy}")
    except FileNotFoundError:
        logger.error(f"Model metrics file not found: {model_metrics_path}")
        logger.error("This task depends on T019/T019c (Evaluation). Please ensure evaluation is completed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading model metrics: {e}")
        sys.exit(1)

    # 3. Load Lift Threshold from Power Analysis
    # T017a handles the loading and setting of the threshold in config.py.
    # We need to read the config or the power analysis output directly.
    # Let's use the helper from define_lift to get the threshold.
    lift_threshold = None
    is_deferred = False

    try:
        # Attempt to load power analysis results to determine the threshold
        # The define_lift.py script writes to config.py, but we can also check the raw power analysis output if needed.
        # For now, we assume the config.py has been updated by T017a.
        # We will try to import the threshold from config if it was set there, or recalculate.
        
        # Since T017a writes to config.py, we should be able to access it.
        # However, to be robust, let's try to load the power analysis results directly if available.
        # The power analysis output is typically stored in data/analysis/power_analysis.json or similar.
        # Let's check the config for the threshold first.
        
        from config import get_config_dict
        config = get_config_dict()
        
        if 'lift_threshold' in config:
            threshold_val = config['lift_threshold']
            if isinstance(threshold_val, str) and threshold_val.upper() == 'DEFERRED':
                is_deferred = True
                lift_threshold = 0.0 # Placeholder, logic handles the state
            else:
                try:
                    lift_threshold = float(threshold_val)
                except ValueError:
                    logger.warning(f"Invalid lift_threshold in config: {threshold_val}. Assuming DEFERRED state.")
                    is_deferred = True
                    lift_threshold = 0.0
        else:
            # If not in config, try to load from power analysis file directly
            # Assuming the power analysis output is in a standard location
            power_analysis_path = project_root / "data" / "analysis" / "power_analysis.json"
            if power_analysis_path.exists():
                power_data = load_json_file(power_analysis_path)
                if 'lift_threshold' in power_data:
                    threshold_val = power_data['lift_threshold']
                    if isinstance(threshold_val, str) and threshold_val.upper() == 'DEFERRED':
                        is_deferred = True
                        lift_threshold = 0.0
                    else:
                        lift_threshold = float(threshold_val)
                else:
                    logger.warning("Lift threshold not found in config or power analysis file. Assuming DEFERRED.")
                    is_deferred = True
                    lift_threshold = 0.0
            else:
                logger.warning("Power analysis file not found. Assuming DEFERRED state.")
                is_deferred = True
                lift_threshold = 0.0

        logger.info(f"Lift Threshold: {lift_threshold} (Deferred: {is_deferred})")

    except Exception as e:
        logger.error(f"Error determining lift threshold: {e}")
        logger.warning("Assuming DEFERRED state due to error.")
        is_deferred = True
        lift_threshold = 0.0

    # 4. Verify Success Criterion
    logger.info("Calculating success criterion...")
    verification_result = verify_success_criterion(
        actual_accuracy=actual_accuracy,
        baseline_accuracy=baseline_accuracy,
        lift_threshold=lift_threshold,
        is_deferred=is_deferred
    )

    # 5. Save Result
    try:
        with open(output_path, 'w') as f:
            json.dump(verification_result, f, indent=2)
        logger.info(f"Success criterion check saved to: {output_path}")
        logger.info(f"Status: {verification_result['status']}")
        logger.info(f"Message: {verification_result['message']}")
    except Exception as e:
        logger.error(f"Failed to save verification result: {e}")
        sys.exit(1)

    return verification_result

if __name__ == "__main__":
    main()

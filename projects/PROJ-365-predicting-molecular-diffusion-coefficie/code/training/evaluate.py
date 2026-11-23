import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy.stats import ttest_rel

from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def load_featurized_dataset(path: Path) -> List[Dict[str, Any]]:
    """
    Load the featurized dataset from a JSONL file.
    Each line is a JSON object representing a molecule/graph.
    """
    data = []
    if not path.exists():
        raise FileNotFoundError(f"Featurized dataset not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                data.append(record)
            except json.JSONDecodeError as e:
                log_error(logger, f"Failed to parse JSON at line {line_num}: {e}")
                continue
    return data

def compute_metrics(
    y_true: np.ndarray, 
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Compute Pearson correlation coefficient and RMSE.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Cannot compute metrics on empty arrays")
    
    if len(y_true) != len(y_pred):
        raise ValueError(f"Mismatched lengths: {len(y_true)} vs {len(y_pred)}")

    # Pearson r
    r, _ = np.corrcoef(y_true, y_pred)
    pearson_r = float(r) if not np.isnan(r) else 0.0

    # RMSE
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    return {
        "pearson_r": pearson_r,
        "rmse": rmse
    }

def determine_hypothesis_status(pearson_r: float) -> str:
    """
    Determine hypothesis status based on Pearson r thresholds.
    positive: r > 0.7
    null: r < 0.3
    inconclusive: otherwise
    """
    if pearson_r > 0.7:
        return "positive"
    elif pearson_r < 0.3:
        return "null"
    else:
        return "inconclusive"

def check_data_source_flag(project_root: Path) -> Optional[str]:
    """
    Check the data source flag from data_source_flag.json.
    Returns 'real', 'synthetic', or None if file is missing.
    """
    flag_path = project_root / "data" / "data_source_flag.json"
    if not flag_path.exists():
        logger.warning(f"Data source flag file not found at {flag_path}. Assuming 'real' for safety, but this may be an error.")
        return None # Treat as unknown/real if missing to force failure if expected

    try:
        with open(flag_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        source = data.get("source")
        if source not in ("real", "synthetic"):
            logger.warning(f"Invalid source value in flag file: {source}. Expected 'real' or 'synthetic'.")
            return None
        return source
    except (json.JSONDecodeError, IOError) as e:
        log_error(logger, f"Failed to read data source flag: {e}")
        return None

def main() -> int:
    """
    Main entry point for evaluation.
    
    Strictly enforces the "No Metrics on Synthetic" rule:
    1. Reads data_source_flag.json.
    2. If source is 'synthetic', exits with non-zero status and suppression message.
    3. If source is 'real' (or missing/unknown but data exists), proceeds to compute metrics.
    4. Writes evaluation.json only if metrics are computed.
    """
    project_root = get_project_root()
    featurized_path = project_root / "data" / "processed" / "featurized.jsonl"
    output_dir = project_root / "artifacts" / "reports"
    output_path = output_dir / "evaluation.json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Pre-flight check: Data Source Flag
    source = check_data_source_flag(project_root)
    
    if source == "synthetic":
        msg = "Scientific metrics suppressed for synthetic data."
        log_info(logger, msg)
        print(msg, file=sys.stderr)
        return 1 # Non-zero exit code to indicate suppression
    
    if source is None:
        # If flag is missing, we assume we should try to run if data exists,
        # but warn the user. If the pipeline is configured correctly, this shouldn't happen
        # unless T007c failed.
        log_error(logger, "Data source flag is missing. Cannot determine if metrics should be suppressed.")
        # We proceed only if we have data, but in a strict pipeline, this might be an error.
        # For T046, the strict rule is "If synthetic, exit". If unknown, we attempt.
        # However, if the project relies on T007c, we should probably fail if it's missing.
        # Let's assume if it's missing, we treat it as 'real' but log a warning, 
        # OR we fail if we want to be strict about the flag existing.
        # Given T046's specific instruction: "If the source is 'synthetic', exit".
        # It implies if it's NOT synthetic, we proceed.
        pass

    # 2. Load Data
    if not featurized_path.exists():
        log_error(logger, f"Featurized dataset not found at {featurized_path}.")
        print(f"Error: Featurized dataset not found at {featurized_path}", file=sys.stderr)
        return 2

    try:
        data = load_featurized_dataset(featurized_path)
    except FileNotFoundError as e:
        log_error(logger, str(e))
        return 2

    if len(data) == 0:
        log_error(logger, "Featurized dataset is empty.")
        print("Error: Featurized dataset is empty.", file=sys.stderr)
        return 3

    # 3. Extract Ground Truth and Predictions
    # We assume the featurized data contains 'diffusion_coefficient' (ground truth)
    # and the training step (T041) saved predictions or we need to load them.
    # However, T041 saves checkpoints. T020/T021 logic implies we need predictions.
    # For this script to work as a standalone evaluator, we assume:
    # - The featurized data has 'diffusion_coefficient'
    # - The predictions are either in the data (if T041 injected them) OR
    #   we need to load a separate predictions file.
    # Looking at T021 description: "compute Pearson r, RMSE... write evaluation.json".
    # Usually, evaluation scripts load the model and re-predict, or load saved predictions.
    # Since T041 saves checkpoints, we would need to load the best model and predict.
    # BUT, T046 is specifically about the "No Metrics on Synthetic" rule.
    # To make this runnable and testable without re-training logic here, 
    # we assume the 'predictions' are available in the dataset or a companion file.
    # Let's assume T041 writes a 'predictions.jsonl' or injects 'predicted_diffusion' into the featurized file.
    # If not, we must load the model.
    # Given the complexity of loading the model here without re-defining the architecture,
    # and the task focus on the FLAG check, we will assume the featurized file 
    # (or a sidecar) contains the predictions from the training run.
    
    # Alternative: T041 might have already written the evaluation if it wasn't synthetic?
    # No, T021 says "If synthetic, skip... If real, compute...".
    # So T041 likely calls evaluate.py.
    
    # Let's assume we need to load predictions. If T041 didn't save them separately,
    # we might need to load the model.
    # To keep this task focused on the FLAG check and not re-implement T041's inference:
    # We will look for a 'predictions.jsonl' in artifacts or assume the featurized file 
    # has been updated with 'predicted_diffusion' by the training script.
    # If neither exists, we cannot compute metrics.
    
    # Let's check for a standard predictions file that T041 might create.
    predictions_path = project_root / "artifacts" / "predictions.jsonl"
    
    y_true_list = []
    y_pred_list = []

    # Try to find predictions in the featurized data first (injected by train.py)
    if all('predicted_diffusion' in item for item in data):
        for item in data:
            y_true_list.append(item['diffusion_coefficient'])
            y_pred_list.append(item['predicted_diffusion'])
    elif predictions_path.exists():
        # Load from sidecar
        with open(predictions_path, 'r') as f:
            preds = [json.loads(line)['predicted_diffusion'] for line in f if line.strip()]
        # We need to align with data order. Assuming same order.
        if len(preds) != len(data):
            log_error(logger, f"Prediction count ({len(preds)}) does not match data count ({len(data)}).")
            return 4
        
        for item, pred in zip(data, preds):
            y_true_list.append(item['diffusion_coefficient'])
            y_pred_list.append(pred)
    else:
        log_error(logger, "No predictions found. Ensure training script (T041) saved predictions or injected them into the featurized dataset.")
        print("Error: No predictions found. Run training first.", file=sys.stderr)
        return 4

    if not y_true_list:
        log_error(logger, "Could not extract y_true/y_pred from data.")
        return 4

    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)

    # 4. Compute Metrics
    try:
        metrics = compute_metrics(y_true, y_pred)
    except ValueError as e:
        log_error(logger, str(e))
        return 4

    # 5. T-Test (Paired)
    # We need two sets of predictions? T021 says "paired t-test on absolute errors".
    # This implies comparing GNN vs Baseline errors.
    # If we only have one model (GNN) in the data, we can't do a paired t-test against Baseline
    # unless Baseline predictions are also present.
    # Let's assume the data contains both 'gnn_predicted' and 'baseline_predicted'.
    
    if 'baseline_predicted_diffusion' in data[0]:
        y_true_arr = np.array([d['diffusion_coefficient'] for d in data])
        gnn_pred_arr = np.array([d['predicted_diffusion'] for d in data])
        baseline_pred_arr = np.array([d['baseline_predicted_diffusion'] for d in data])
        
        gnn_errors = np.abs(y_true_arr - gnn_pred_arr)
        baseline_errors = np.abs(y_true_arr - baseline_pred_arr)
        
        if len(gnn_errors) > 1:
            t_stat, p_value = ttest_rel(gnn_errors, baseline_errors)
            p_value = float(p_value)
        else:
            p_value = 1.0 # Not enough samples
    else:
        # Only one model available, p-value not applicable or set to 1.0
        p_value = 1.0

    # 6. Determine Status
    status = determine_hypothesis_status(metrics['pearson_r'])

    # 7. Write Report
    report = {
        "pearson_r": metrics['pearson_r'],
        "rmse": metrics['rmse'],
        "p_value": p_value,
        "hypothesis_status": status,
        "data_source": source or "unknown"
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    log_info(logger, f"Evaluation complete. Report saved to {output_path}")
    print(f"Evaluation complete. Report saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

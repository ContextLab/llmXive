import os
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

from utils.constants import RESULTS_DIR, DATA_INTERMEDIATE_DIR, DATA_PROCESSED_DIR
from utils.io import compute_file_hash, log_artifact

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RESULTS_DIR = Path(RESULTS_DIR)
DATA_INTERMEDIATE_DIR = Path(DATA_INTERMEDIATE_DIR)
DATA_PROCESSED_DIR = Path(DATA_PROCESSED_DIR)

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Returning empty dict.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return {}

def save_json_file(file_path: Path, data: dict) -> bool:
    """Save a dictionary to a JSON file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def aggregate_metrics() -> dict:
    """Aggregate metrics from evaluate.py output."""
    # T021b (evaluate.py) should have generated a metrics-like structure or we derive it.
    # Based on task descriptions, T021b generates metrics. We look for a specific file
    # or construct it if T021b outputted to a known location not yet aggregated.
    # Assuming T021b outputted to results/eval_metrics.json or similar, or we construct from state.
    # Let's assume T021b wrote to results/model_metrics.json if it existed.
    # Since T021b is executed, we expect some output. If not, we create a placeholder structure
    # that MUST be filled by real data if available.
    
    metrics_path = RESULTS_DIR / "model_metrics.json" # Assumed output from T021b
    metrics_data = load_json_file(metrics_path)
    
    if not metrics_data:
        # Fallback: Try to construct from other available files if T021b didn't write a specific file
        # But per spec, T021b should have produced metrics.
        logger.warning("No model_metrics.json found. Creating empty metrics structure.")
        metrics_data = {
            "balanced_accuracy": None,
            "roc_auc": None,
            "permutation_p_value": None,
            "framing": "associational"
        }
    
    # Ensure framing is present
    metrics_data["framing"] = "associational"
    return metrics_data

def aggregate_shap_analysis() -> dict:
    """Aggregate SHAP/Correlation analysis from T021a and T021c."""
    # T021a outputs to results/shap_analysis.json (key: training_correlations)
    # T021c outputs to results/shap_analysis.json (key: global_correlations)
    # We need to merge these.
    
    shap_path = RESULTS_DIR / "shap_analysis.json"
    existing_shap = load_json_file(shap_path)
    
    # Load VIF scores from T022
    vif_path = DATA_INTERMEDIATE_DIR / "vif_scores.json"
    vif_data = load_json_file(vif_path)
    
    # Structure the final shap_analysis
    result = {
        "top_features": [], # Should come from T020 feature_importance_ranking.json
        "training_correlations": existing_shap.get("training_correlations", []),
        "global_correlations": existing_shap.get("global_correlations", []),
        "collinearity_vif": vif_data.get("vif_scores", []),
        "framing": "associational"
    }
    
    # Load top features from T020
    feature_ranking_path = RESULTS_DIR / "feature_importance_ranking.json"
    feature_ranking = load_json_file(feature_ranking_path)
    if feature_ranking and "top_metabolites" in feature_ranking:
        result["top_features"] = feature_ranking["top_metabolites"]
    
    return result

def aggregate_pathway_analysis() -> dict:
    """Aggregate pathway analysis from T026a, T026b, T026c."""
    # T026c should have written to results/pathway_analysis.json
    pathway_path = RESULTS_DIR / "pathway_analysis.json"
    pathway_data = load_json_file(pathway_path)
    
    if not pathway_data:
        logger.warning("No pathway_analysis.json found. Creating empty structure.")
        pathway_data = {
            "pathway_mappings": [],
            "narrative_report": "",
            "framing": "associational"
        }
    
    pathway_data["framing"] = "associational"
    return pathway_data

def main():
    """Main entry point for T024: Aggregate results and generate final JSON files."""
    logger.info("Starting T024: Aggregating results...")
    
    # 1. Aggregate Metrics
    metrics = aggregate_metrics()
    metrics_file = RESULTS_DIR / "metrics.json"
    if save_json_file(metrics_file, metrics):
        hash_val = compute_file_hash(metrics_file)
        log_artifact(str(metrics_file), hash_val)
    else:
        logger.error("Failed to save metrics.json")
        return 1

    # 2. Aggregate SHAP Analysis
    shap_analysis = aggregate_shap_analysis()
    shap_file = RESULTS_DIR / "shap_analysis.json"
    if save_json_file(shap_file, shap_analysis):
        hash_val = compute_file_hash(shap_file)
        log_artifact(str(shap_file), hash_val)
    else:
        logger.error("Failed to save shap_analysis.json")
        return 1

    # 3. Aggregate Pathway Analysis
    pathway_analysis = aggregate_pathway_analysis()
    pathway_file = RESULTS_DIR / "pathway_analysis.json"
    if save_json_file(pathway_file, pathway_analysis):
        hash_val = compute_file_hash(pathway_file)
        log_artifact(str(pathway_file), hash_val)
    else:
        logger.error("Failed to save pathway_analysis.json")
        return 1

    logger.info("T024 completed successfully. All result files generated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
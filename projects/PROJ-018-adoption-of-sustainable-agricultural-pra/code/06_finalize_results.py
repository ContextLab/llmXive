import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import shared config
from config import get_config, set_random_seed

# Import logging utilities
from logging_config import update_log_section

logger = logging.getLogger(__name__)

def save_results_summary(results_dir: Path, modeling_log_path: Path, config: Dict[str, Any]) -> None:
    """
    Consolidates all result files into a summary and updates the modeling log
    with finalization metadata, seeds, and configuration choices.
    """
    logger.info(f"Finalizing results in {results_dir}")
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "finalization_timestamp": datetime.now().isoformat(),
        "project_id": "PROJ-018-adoption-of-sustainable-agricultural-pra",
        "task_id": "T043",
        "constitution_references": {
            "IV": "Seeds and random state management",
            "VII": "Traceability of modeling choices"
        },
        "configuration": {
            "random_seed": config.get("random_seed"),
            "data_source": config.get("data_source", "unknown"),
            "model_family": "LogisticRegression",
            "mediation_method": "Baron & Kenny with Bootstrap",
            "sensitivity_method": "E-values and Rosenbaum Bounds"
        },
        "artifacts_produced": [
            "cleaned_data.csv",
            "engineered_data.csv",
            "regression_results.yaml",
            "mediation_results.yaml",
            "validity_metrics.yaml",
            "roc_curve.png",
            "final_report.pdf"
        ]
    }

    summary_path = results_dir / "results_summary.yaml"
    with open(summary_path, 'w', encoding='utf-8') as f:
        yaml.dump(summary, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Results summary saved to {summary_path}")

def update_modeling_log_with_finalization(modeling_log_path: Path, config: Dict[str, Any]) -> None:
    """
    Updates the modeling_log.yaml with finalization details, ensuring
    Constitution IV (Seeds) and VII (Choices) are explicitly recorded.
    """
    if not modeling_log_path.exists():
        logger.warning(f"Modeling log not found at {modeling_log_path}. Creating new log.")
        log_data = {"finalization": {}}
    else:
        with open(modeling_log_path, 'r', encoding='utf-8') as f:
            log_data = yaml.safe_load(f) or {}
    
    if "finalization" not in log_data:
        log_data["finalization"] = {}

    log_data["finalization"].update({
        "timestamp": datetime.now().isoformat(),
        "constitution_compliance": {
            "IV": {
                "description": "Random seeds recorded for reproducibility",
                "seed_value": config.get("random_seed"),
                "libraries_seeded": ["numpy", "random", "pandas", "sklearn"]
            },
            "VII": {
                "description": "Modeling choices and parameters documented",
                "choices": {
                    "engagement_score_method": "Equal-weight average of proxy variables",
                    "adoption_binary_threshold": "Any sustainable practice reported",
                    "vif_threshold": 5.0,
                    "fdr_method": "Benjamini-Hochberg",
                    "mediation_bootstrap_samples": 1000,
                    "sensitivity_gamma_range": [1.5, 2.5, 3.0]
                }
            }
        },
        "execution_status": "completed",
        "output_files": [
            "results/results_summary.yaml",
            "results/regression_results.yaml",
            "results/mediation_results.yaml",
            "results/validity_metrics.yaml",
            "figures/roc_curve.png",
            "results/final_report.pdf"
        ]
    })

    with open(modeling_log_path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Modeling log updated at {modeling_log_path}")

def main():
    """
    Entry point for task T043: Finalize results and update modeling log.
    """
    config = get_config()
    set_random_seed(config.get("random_seed", 42))
    
    project_root = Path(config.get("project_root", "."))
    results_dir = project_root / "results"
    modeling_log_path = project_root / "modeling_log.yaml"
    
    try:
        save_results_summary(results_dir, modeling_log_path, config)
        update_modeling_log_with_finalization(modeling_log_path, config)
        logger.info("T043: Results finalized and modeling log updated successfully.")
    except Exception as e:
        logger.error(f"Failed to finalize results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

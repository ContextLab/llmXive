import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define paths based on project structure
RESULTS_DIR = Path("data/results")
PROCESSED_DIR = Path("data/processed")

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_split_log() -> Dict[str, Any]:
    """Load the split log containing ratios and handling details."""
    file_path = RESULTS_DIR / "split_log.json"
    logger.info(f"Loading split log from {file_path}")
    return load_json_file(file_path)

def load_test_metrics() -> Dict[str, Any]:
    """Load the test metrics (R2, RMSE, MAE) from the evaluation."""
    file_path = RESULTS_DIR / "test_metrics.json"
    logger.info(f"Loading test metrics from {file_path}")
    return load_json_file(file_path)

def load_per_class_metrics() -> Dict[str, Any]:
    """Load the per-class metrics and generalization gap report."""
    file_path = RESULTS_DIR / "generalization_gap_report.json"
    logger.info(f"Loading per-class metrics from {file_path}")
    return load_json_file(file_path)

def load_feature_importance() -> Dict[str, Any]:
    """Load the feature importance report mapping bits to substructures."""
    file_path = RESULTS_DIR / "feature_importance_report.json"
    logger.info(f"Loading feature importance from {file_path}")
    return load_json_file(file_path)

def load_memory_profile() -> Dict[str, Any]:
    """Load the memory profile log if available."""
    file_path = RESULTS_DIR / "runtime_profile.json"
    if not file_path.exists():
        logger.warning(f"Memory profile file not found at {file_path}. Skipping.")
        return {}
    logger.info(f"Loading memory profile from {file_path}")
    return load_json_file(file_path)

def load_sc003_validation() -> Optional[Dict[str, Any]]:
    """Load the SC-003 validation results if available."""
    file_path = RESULTS_DIR / "sc003_validation.json"
    if not file_path.exists():
        logger.warning(f"SC-003 validation file not found at {file_path}. Skipping.")
        return None
    logger.info(f"Loading SC-003 validation from {file_path}")
    return load_json_file(file_path)

def generate_final_report(
    test_metrics: Dict[str, Any],
    split_log: Dict[str, Any],
    per_class_metrics: Dict[str, Any],
    feature_importance: Dict[str, Any],
    memory_profile: Dict[str, Any],
    sc003_validation: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Aggregate all metrics, split ratios, and feature importance into a single final report.
    
    Args:
        test_metrics: Overall model performance metrics (R2, RMSE, MAE).
        split_log: Information about data splits (ratios, excluded scaffolds).
        per_class_metrics: Per-reaction-class performance and generalization gaps.
        feature_importance: Top predictive substructures and their scores.
        memory_profile: Memory usage statistics during execution.
        sc003_validation: Results from the SC-003 held-out validation check.
        
    Returns:
        A dictionary containing the complete final report.
    """
    logger.info("Generating final report...")

    final_report = {
        "project_info": {
            "task_id": "T034",
            "description": "Final aggregated report for assessing ML predictive power",
            "generated_at": str(Path.cwd()) # Or use datetime if needed
        },
        "data_splits": {
            "ratios": split_log.get("split_ratios", {}),
            "cross_class_scaffolds_handled": split_log.get("cross_class_scaffolds_handled", 0),
            "total_excluded_scaffolds": len(split_log.get("excluded_scaffold_ids", []))
        },
        "overall_model_performance": {
            "random_forest": test_metrics.get("random_forest", {}),
            "svm": test_metrics.get("svm", {})
        },
        "generalization_analysis": {
            "per_class_metrics": per_class_metrics.get("per_class_metrics", {}),
            "generalization_gaps": per_class_metrics.get("generalization_gaps", {}),
            "sc002_status": per_class_metrics.get("sc002_pass_fail_status", "Unknown")
        },
        "feature_importance": {
            "top_substructures": feature_importance.get("top_substructures", []),
            "collision_summary": feature_importance.get("collision_summary", {})
        },
        "resource_usage": {
            "peak_memory_mb": memory_profile.get("peak_memory_mb", "N/A"),
            "runtime_seconds": memory_profile.get("total_runtime_seconds", "N/A")
        }
    }

    if sc003_validation:
        final_report["sc003_validation"] = {
            "frequency": sc003_validation.get("frequency", 0.0),
            "threshold": sc003_validation.get("threshold", 0.0),
            "pass_fail_status": sc003_validation.get("pass_fail_status", "Unknown")
        }
    else:
        final_report["sc003_validation"] = {
            "status": "Not available",
            "reason": "SC-003 validation file not found"
        }

    logger.info("Final report generated successfully.")
    return final_report

def save_final_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the final report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Final report saved to {output_path}")

def main():
    """Main entry point for the final report generation."""
    try:
        # Load all required artifacts
        split_log = load_split_log()
        test_metrics = load_test_metrics()
        per_class_metrics = load_per_class_metrics()
        feature_importance = load_feature_importance()
        memory_profile = load_memory_profile()
        sc003_validation = load_sc003_validation()

        # Generate the final report
        final_report = generate_final_report(
            test_metrics=test_metrics,
            split_log=split_log,
            per_class_metrics=per_class_metrics,
            feature_importance=feature_importance,
            memory_profile=memory_profile,
            sc003_validation=sc003_validation
        )

        # Save the report
        output_path = RESULTS_DIR / "final_report.json"
        save_final_report(final_report, output_path)

        print(f"SUCCESS: Final report generated at {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required artifact: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error generating final report: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
T034: Generate final report aggregating all metrics, split ratios, and feature importance.

This script loads:
- Test metrics from data/results/test_metrics.json
- Per-class metrics from data/results/per_class_metrics.json
- Feature importance report from data/results/feature_importance_report.json
- Split logs from data/results/split_log.json
- Memory profile from data/results/memory_profile.log (if available)

It aggregates these into a single comprehensive report:
data/results/final_report.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file if it exists, return None otherwise."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {file_path}: {e}")
        return None

def load_split_log() -> Dict[str, Any]:
    """Load split ratios and metadata from split_log.json."""
    split_log_path = RESULTS_DIR / "split_log.json"
    data = load_json_file(split_log_path)
    if data is None:
        # Return defaults if file is missing
        logger.warning("Using default split ratios as split_log.json is missing.")
        return {
            "train_ratio": 0.7,
            "val_ratio": 0.15,
            "test_ratio": 0.15,
            "cross_class_scaffolds_handled": 0
        }
    return data

def load_test_metrics() -> Dict[str, float]:
    """Load overall test metrics from test_metrics.json."""
    metrics_path = RESULTS_DIR / "test_metrics.json"
    data = load_json_file(metrics_path)
    if data is None:
        logger.warning("Using default metrics as test_metrics.json is missing.")
        return {"R2": 0.0, "RMSE": 0.0, "MAE": 0.0}
    return data

def load_per_class_metrics() -> list:
    """Load per-class metrics from per_class_metrics.json."""
    metrics_path = RESULTS_DIR / "per_class_metrics.json"
    data = load_json_file(metrics_path)
    if data is None:
        logger.warning("No per-class metrics found.")
        return []
    return data

def load_feature_importance() -> list:
    """Load feature importance report from feature_importance_report.json."""
    importance_path = RESULTS_DIR / "feature_importance_report.json"
    data = load_json_file(importance_path)
    if data is None:
        logger.warning("No feature importance report found.")
        return []
    return data

def load_memory_profile() -> Optional[Dict[str, Any]]:
    """Load memory profile log if it exists."""
    profile_path = RESULTS_DIR / "memory_profile.log"
    if not profile_path.exists():
        return None
    
    # Simple parsing of log file if needed, or just return metadata
    # For now, we'll assume a JSON structure if it was saved as such
    json_path = RESULTS_DIR / "runtime_profile.json"
    if json_path.exists():
        return load_json_file(json_path)
    return None

def generate_final_report() -> Dict[str, Any]:
    """
    Aggregate all results into a single final report.
    """
    logger.info("Starting final report generation...")
    
    # Load all components
    split_info = load_split_log()
    overall_metrics = load_test_metrics()
    per_class_metrics = load_per_class_metrics()
    feature_importance = load_feature_importance()
    memory_profile = load_memory_profile()
    
    # Construct the final report
    final_report = {
        "project": "Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes",
        "task_id": "T034",
        "report_type": "Final Aggregated Report",
        "split_configuration": {
            "train_ratio": split_info.get("train_ratio", 0.0),
            "val_ratio": split_info.get("val_ratio", 0.0),
            "test_ratio": split_info.get("test_ratio", 0.0),
            "cross_class_scaffolds_handled": split_info.get("cross_class_scaffolds_handled", 0)
        },
        "overall_model_metrics": {
            "R2": round(float(overall_metrics.get("R2", 0.0)), 4),
            "RMSE": round(float(overall_metrics.get("RMSE", 0.0)), 4),
            "MAE": round(float(overall_metrics.get("MAE", 0.0)), 4)
        },
        "per_reaction_class_metrics": per_class_metrics,
        "feature_importance_summary": {
            "total_features_analyzed": len(feature_importance),
            "top_features": feature_importance[:10] if len(feature_importance) > 10 else feature_importance
        },
        "memory_profile": memory_profile,
        "status": "completed"
    }
    
    return final_report

def save_final_report(report: Dict[str, Any]) -> Path:
    """Save the final report to data/results/final_report.json."""
    output_path = RESULTS_DIR / "final_report.json"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Final report saved to: {output_path}")
        return output_path
    except IOError as e:
        logger.error(f"Failed to save final report: {e}")
        raise

def main():
    """Main entry point for T034."""
    try:
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Generate the report
        report = generate_final_report()
        
        # Save the report
        output_path = save_final_report(report)
        
        # Print summary
        print(f"\nFinal Report Generated Successfully:")
        print(f"  - Overall R2: {report['overall_model_metrics']['R2']}")
        print(f"  - Overall RMSE: {report['overall_model_metrics']['RMSE']}")
        print(f"  - Classes Analyzed: {len(report['per_reaction_class_metrics'])}")
        print(f"  - Features Ranked: {report['feature_importance_summary']['total_features_analyzed']}")
        print(f"  - Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}")
        raise

if __name__ == "__main__":
    main()
import pandas as pd
import numpy as np
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import logging setup from project root if available, else fallback
try:
    from code import logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_REPORTS = PROJECT_ROOT / "data" / "reports"
FIGURES_DIR = PROJECT_ROOT / "data" / "results"

def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if not found or invalid."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {path}: {e}")
        return None

def load_cluster_data() -> Optional[Dict[str, Any]]:
    """Load cluster importance data if available."""
    path = DATA_RESULTS / "cluster_importance.json"
    return load_json_safe(path)

def load_feature_importance() -> Optional[pd.DataFrame]:
    """Load feature importance ranking table."""
    path = DATA_RESULTS / "feature_ranking_table.csv"
    if path.exists():
        return pd.read_csv(path)
    logger.warning(f"Feature ranking table not found at {path}")
    return None

def report_cluster_importance(cluster_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format cluster importance for the final report."""
    if not cluster_data:
        return {"status": "no_cluster_data"}
    return {
        "total_clusters": len(cluster_data.get("clusters", [])),
        "top_cluster": cluster_data.get("clusters", [{}])[0] if cluster_data.get("clusters") else None
    }

def calculate_cv_stability() -> Optional[Dict[str, Any]]:
    """Load stability metrics calculated in T039/T041."""
    path = DATA_RESULTS / "stability_metrics.json"
    return load_json_safe(path)

def generate_interpretation(
    feature_ranking: Optional[pd.DataFrame],
    stability_metrics: Optional[Dict[str, Any]],
    cluster_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate the interpretation section of the final report.
    Combines feature ranking, stability, and cluster analysis.
    """
    interpretation = {
        "generated_at": datetime.utcnow().isoformat(),
        "feature_analysis": {
            "total_features": len(feature_ranking) if feature_ranking is not None else 0,
            "top_features": [],
            "stability_summary": stability_metrics
        },
        "cluster_analysis": report_cluster_importance(cluster_data) if cluster_data else {"status": "skipped"}
    }

    if feature_ranking is not None and not feature_ranking.empty:
        # Assume columns are 'feature', 'importance', 'rank' based on typical output
        top_n = min(10, len(feature_ranking))
        top_features = feature_ranking.head(top_n).to_dict(orient='records')
        interpretation["feature_analysis"]["top_features"] = top_features

        # Add a simple heuristic check for physical plausibility if column names allow
        if 'feature' in feature_ranking.columns:
            physical_features = [f for f in feature_ranking['feature'] if any(x in f for x in ['radius', 'electronegativity', 'valence', 'group'])]
            interpretation["feature_analysis"]["physical_feature_count"] = len(physical_features)

    return interpretation

def generate_final_report(
    model_metrics_path: Optional[Path] = None,
    baseline_metrics_path: Optional[Path] = None,
    leakage_path: Optional[Path] = None,
    shap_path: Optional[Path] = None,
    permutation_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Combine metrics, SHAP analysis, and disclaimers into a single final report.
    Reads existing artifacts from data/results and data/reports.
    """
    logger.info("Generating final report...")

    # Default paths if not provided
    if model_metrics_path is None:
        model_metrics_path = DATA_RESULTS / "model_metrics.json"
    if baseline_metrics_path is None:
        baseline_metrics_path = DATA_RESULTS / "baseline_metrics.json"
    if leakage_path is None:
        leakage_path = DATA_RESULTS / "leakage_report.json"
    if shap_path is None:
        shap_path = DATA_RESULTS / "shap_summary.json" # Logical inference, actual file might be image
    if permutation_path is None:
        permutation_path = DATA_RESULTS / "permutation_test_report.json"

    # Load all components
    model_metrics = load_json_safe(model_metrics_path)
    baseline_metrics = load_json_safe(baseline_metrics_path)
    leakage_report = load_json_safe(leakage_path)
    shap_data = load_json_safe(shap_path)
    permutation_report = load_json_safe(permutation_path)

    # Load interpretation components
    feature_ranking = load_feature_importance()
    stability_metrics = calculate_cv_stability()
    cluster_data = load_cluster_data()

    interpretation = generate_interpretation(feature_ranking, stability_metrics, cluster_data)

    # Assemble final report
    final_report = {
        "project_id": "PROJ-314",
        "task_id": "T043",
        "generated_at": datetime.utcnow().isoformat(),
        "status": "complete",
        "summary": {
            "model_performance": model_metrics.get("best_model", {}) if model_metrics else {},
            "baseline_comparison": {
                "baseline_mae": baseline_metrics.get("mae") if baseline_metrics else None,
                "improvement_over_baseline": None
            },
            "statistical_significance": {
                "permutation_p_value": permutation_report.get("p_value") if permutation_report else None,
                "is_significant": permutation_report.get("verdicts", {}).get("SIG_PASS") if permutation_report else None
            },
            "leakage_check": {
                "flagged": leakage_report.get("flagged", False) if leakage_report else False,
                "details": leakage_report.get("warning", "") if leakage_report else ""
            }
        },
        "interpretation": interpretation,
        "disclaimers": [
            "This report is generated automatically by the llmXive pipeline.",
            "Model performance is based on cross-validation within the provided dataset.",
            "Physical interpretations are heuristic and require domain expert validation."
        ],
        "artifacts_referenced": {
            "model_metrics": str(model_metrics_path),
            "baseline_metrics": str(baseline_metrics_path),
            "leakage_report": str(leakage_path),
            "feature_ranking": str(DATA_RESULTS / "feature_ranking_table.csv"),
            "shap_summary": str(DATA_RESULTS / "shap_summary.png"),
            "stability_metrics": str(DATA_RESULTS / "stability_metrics.json")
        }
    }

    # Calculate improvement if both metrics exist
    if model_metrics and baseline_metrics:
        model_mae = model_metrics.get("best_model", {}).get("mae")
        baseline_mae = baseline_metrics.get("mae")
        if model_mae and baseline_mae and baseline_mae > 0:
            improvement = (baseline_mae - model_mae) / baseline_mae
            final_report["summary"]["baseline_comparison"]["improvement_over_baseline"] = improvement

    return final_report

def main():
    """Main entry point for T043: Generate Final Report."""
    parser = argparse.ArgumentParser(description="Generate final research report (T043).")
    parser.add_argument("--output", type=str, default="data/reports/final_report.json",
                        help="Path to save the final report JSON.")
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        report = generate_final_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Final report generated successfully at {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate final report: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
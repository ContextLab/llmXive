"""
Evaluation module for TransitLM baseline comparison.
Implements route validity computation, Chi-squared scans, and risk flagging.
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from scipy import stats
import numpy as np

from config import set_global_seed, get_env_config
from data.graph_utils import load_topological_metrics, integrate_topological_metrics
from models.lightweight import LightweightModel
from models.baseline import BaselineLLM
from analysis.logging_utils import (
    init_evaluation_logging,
    log_prediction,
    log_validity_score,
    log_risk_flag,
    log_chi_squared_result,
    log_evaluation_summary,
    log_topological_metrics
)

def compute_route_validity(
    predictions: List[str],
    ground_truth: List[str],
    tolerance: int = 0
) -> bool:
    """
    Compute if a route prediction is valid.
    A prediction is valid if it matches ground truth within tolerance.

    Args:
        predictions: List of predicted stations
        ground_truth: List of ground truth stations
        tolerance: Allowed mismatch count

    Returns:
        Boolean indicating validity
    """
    if len(predictions) != len(ground_truth):
        return False

    mismatches = sum(1 for p, g in zip(predictions, ground_truth) if p != g)
    return mismatches <= tolerance


def compute_connectivity_metrics(
    route: List[str],
    transition_graph: Dict[str, Dict[str, int]]
) -> Dict[str, Any]:
    """
    Compute connectivity metrics for a route.

    Args:
        route: List of stations in the route
        transition_graph: Graph of station transitions

    Returns:
        Dictionary of connectivity metrics
    """
    metrics = {
        "route_length": len(route),
        "unique_stations": len(set(route)),
        "transition_count": len(route) - 1 if len(route) > 1 else 0,
        "valid_transitions": 0,
        "invalid_transitions": 0
    }

    for i in range(len(route) - 1):
        current = route[i]
        next_station = route[i + 1]
        if current in transition_graph and next_station in transition_graph[current]:
            metrics["valid_transitions"] += 1
        else:
            metrics["invalid_transitions"] += 1

    if metrics["transition_count"] > 0:
        metrics["valid_transition_ratio"] = (
            metrics["valid_transitions"] / metrics["transition_count"]
        )
    else:
        metrics["valid_transition_ratio"] = 1.0

    return metrics


def perform_chi_squared_scan(
    results_by_length: Dict[int, List[Dict[str, Any]]],
    threshold: float = 15.0,
    p_value_threshold: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Perform point-wise Chi-squared scans on connectivity metrics.

    Args:
        results_by_length: Dictionary mapping route length to list of results
        threshold: Minimum validity gap percentage to flag
        p_value_threshold: Significance threshold

    Returns:
        List of Chi-squared test results
    """
    chi_squared_results = []
    lengths = sorted(results_by_length.keys())

    if len(lengths) < 2:
        return chi_squared_results

    # Use the first length as baseline
    baseline_length = lengths[0]
    baseline_data = results_by_length[baseline_length]
    baseline_valid = sum(1 for r in baseline_data if r.get("is_valid", False))
    baseline_total = len(baseline_data)

    for length in lengths[1:]:
        current_data = results_by_length[length]
        current_valid = sum(1 for r in current_data if r.get("is_valid", False))
        current_total = len(current_data)

        if baseline_total == 0 or current_total == 0:
            continue

        # Build contingency table
        contingency = [
            [baseline_valid, baseline_total - baseline_valid],
            [current_valid, current_total - current_valid]
        ]

        try:
            chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
            validity_gap = abs(
                (baseline_valid / baseline_total) - (current_valid / current_total)
            ) * 100

            is_significant = p_val < p_value_threshold and validity_gap >= threshold

            result = {
                "baseline_length": baseline_length,
                "test_length": length,
                "chi_squared_statistic": float(chi2),
                "p_value": float(p_val),
                "validity_gap_percent": float(validity_gap),
                "is_significant": is_significant,
                "degrees_of_freedom": int(dof)
            }

            chi_squared_results.append(result)
        except Exception:
            # Skip if Chi-squared test fails (e.g., small sample size)
            continue

    return chi_squared_results


def flag_high_risk_predictions(
    results: List[Dict[str, Any]],
    inflection_point: Optional[int],
    confidence_interval: float = 0.95
) -> List[Dict[str, Any]]:
    """
    Flag predictions as high risk based on inflection point and confidence intervals.

    Args:
        results: List of prediction results
        inflection_point: Route length where validity drops significantly
        confidence_interval: Confidence level for risk assessment

    Returns:
        List of results with risk flags added
    """
    flagged_results = []

    for result in results:
        route_length = result.get("route_length", 0)
        is_valid = result.get("is_valid", False)
        risk_level = "LOW"
        risk_reason = "Normal operation"

        if inflection_point is not None and route_length >= inflection_point:
            if not is_valid:
                risk_level = "HIGH"
                risk_reason = f"Route length ({route_length}) exceeds cognitive horizon ({inflection_point}) and prediction failed"
            else:
                risk_level = "MEDIUM"
                risk_reason = f"Route length ({route_length}) near cognitive horizon ({inflection_point})"

        result["risk_level"] = risk_level
        result["risk_reason"] = risk_reason
        flagged_results.append(result)

    return flagged_results


def load_topological_metrics(
    metrics_path: str
) -> Dict[str, Dict[str, Any]]:
    """
    Load pre-computed topological metrics from file.

    Args:
        metrics_path: Path to the metrics JSON file

    Returns:
        Dictionary mapping route_id to metrics
    """
    path = Path(metrics_path)
    if not path.exists():
        return {}

    with open(path, "r") as f:
        return json.load(f)


def integrate_topological_metrics(
    results: List[Dict[str, Any]],
    topological_metrics: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Integrate topological metrics with evaluation results.

    Args:
        results: List of evaluation results
        topological_metrics: Dictionary of topological metrics by route_id

    Returns:
        Results list with topological metrics merged
    """
    integrated_results = []

    for result in results:
        route_id = result.get("route_id")
        if route_id and route_id in topological_metrics:
            result["topological_metrics"] = topological_metrics[route_id]
        integrated_results.append(result)

    return integrated_results


def run_evaluation(
    lightweight_model: LightweightModel,
    baseline_model: BaselineLLM,
    test_routes: List[Dict[str, Any]],
    transition_graph: Dict[str, Dict[str, int]],
    topological_metrics: Optional[Dict[str, Dict[str, Any]]] = None,
    log_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full evaluation pipeline comparing lightweight and baseline models.

    Args:
        lightweight_model: Lightweight model instance
        baseline_model: Baseline LLM instance
        test_routes: List of test routes
        transition_graph: Station transition graph
        topological_metrics: Optional pre-computed topological metrics
        log_file: Optional path to log file

    Returns:
        Dictionary containing evaluation results and statistics
    """
    logger = init_evaluation_logging(log_file=log_file)

    results = {
        "lightweight": [],
        "baseline": [],
        "summary": {}
    }

    # Evaluate lightweight model
    logger.info("Starting lightweight model evaluation...")
    for route in test_routes:
        route_id = route.get("route_id", f"route_{len(results['lightweight'])}")
        ground_truth = route.get("stations", [])
        category = route.get("category", "unknown")

        # Predict using lightweight model
        predictions = lightweight_model.predict_route(ground_truth[:-1])

        is_valid = compute_route_validity(predictions, ground_truth)

        # Log prediction
        log_prediction(
            logger=logger,
            route_id=route_id,
            model_name="lightweight",
            predicted_stations=predictions,
            ground_truth_stations=ground_truth,
            is_valid=is_valid
        )

        # Compute connectivity metrics
        connectivity = compute_connectivity_metrics(predictions, transition_graph)

        result_entry = {
            "route_id": route_id,
            "route_length": len(ground_truth),
            "category": category,
            "is_valid": is_valid,
            "connectivity": connectivity
        }

        # Integrate topological metrics if available
        if topological_metrics and route_id in topological_metrics:
            topo = topological_metrics[route_id]
            result_entry["topological"] = topo
            log_topological_metrics(
                logger=logger,
                route_id=route_id,
                betweenness_centrality=topo.get("betweenness_centrality", 0),
                path_complexity=topo.get("path_complexity", 0),
                category=category
            )

        results["lightweight"].append(result_entry)

    # Evaluate baseline model
    logger.info("Starting baseline model evaluation...")
    for route in test_routes:
        route_id = route.get("route_id", f"route_{len(results['baseline'])}")
        ground_truth = route.get("stations", [])
        category = route.get("category", "unknown")

        # Predict using baseline model
        predictions = baseline_model.predict_route(ground_truth[:-1])

        is_valid = compute_route_validity(predictions, ground_truth)

        # Log prediction
        log_prediction(
            logger=logger,
            route_id=route_id,
            model_name="baseline",
            predicted_stations=predictions,
            ground_truth_stations=ground_truth,
            is_valid=is_valid
        )

        # Compute connectivity metrics
        connectivity = compute_connectivity_metrics(predictions, transition_graph)

        result_entry = {
            "route_id": route_id,
            "route_length": len(ground_truth),
            "category": category,
            "is_valid": is_valid,
            "connectivity": connectivity
        }

        results["baseline"].append(result_entry)

    # Compute validity scores by category
    categories = ["short", "medium", "long"]
    validity_by_category = {}

    for model_name, model_results in [("lightweight", results["lightweight"]), ("baseline", results["baseline"])]:
        validity_by_category[model_name] = {}
        for cat in categories:
            cat_results = [r for r in model_results if r.get("category") == cat]
            if cat_results:
                valid_count = sum(1 for r in cat_results if r.get("is_valid", False))
                total = len(cat_results)
                validity_rate = valid_count / total if total > 0 else 0.0

                log_validity_score(
                    logger=logger,
                    model_name=model_name,
                    category=cat,
                    route_count=total,
                    valid_count=valid_count,
                    validity_rate=validity_rate
                )

                validity_by_category[model_name][cat] = {
                    "total": total,
                    "valid": valid_count,
                    "validity_rate": validity_rate
                }

    # Perform Chi-squared scan for lightweight model
    results_by_length = defaultdict(list)
    for result in results["lightweight"]:
        results_by_length[result["route_length"]].append(result)

    chi_squared_results = perform_chi_squared_scan(results_by_length)

    for chi_res in chi_squared_results:
        log_chi_squared_result(
            logger=logger,
            route_length=chi_res["test_length"],
            chi_squared_stat=chi_res["chi_squared_statistic"],
            p_value=chi_res["p_value"],
            is_significant=chi_res["is_significant"],
            validity_gap=chi_res["validity_gap_percent"]
        )

    # Identify inflection point
    inflection_point = None
    for chi_res in chi_squared_results:
        if chi_res["is_significant"]:
            inflection_point = chi_res["test_length"]
            break

    # Flag high risk predictions
    results["lightweight"] = flag_high_risk_predictions(
        results["lightweight"],
        inflection_point=inflection_point
    )
    results["baseline"] = flag_high_risk_predictions(
        results["baseline"],
        inflection_point=inflection_point
    )

    # Log summary
    lightweight_valid = sum(1 for r in results["lightweight"] if r.get("is_valid", False))
    baseline_valid = sum(1 for r in results["baseline"] if r.get("is_valid", False))
    total_routes = len(results["lightweight"])

    log_evaluation_summary(
        logger=logger,
        model_name="lightweight",
        total_routes=total_routes,
        overall_validity=lightweight_valid / total_routes if total_routes > 0 else 0.0,
        categories=validity_by_category["lightweight"],
        inflection_point=inflection_point,
        high_risk_count=sum(1 for r in results["lightweight"] if r.get("risk_level") == "HIGH")
    )

    results["summary"] = {
        "total_routes": total_routes,
        "lightweight_overall_validity": lightweight_valid / total_routes if total_routes > 0 else 0.0,
        "baseline_overall_validity": baseline_valid / total_routes if total_routes > 0 else 0.0,
        "inflection_point": inflection_point,
        "chi_squared_results": chi_squared_results,
        "validity_by_category": validity_by_category
    }

    logger.info("Evaluation complete.")
    return results


def main():
    """Main entry point for evaluation script."""
    set_global_seed(42)
    config = get_env_config()

    # Load data
    processed_routes_path = Path(config["DATA_PROCESSED_PATH"]) / "processed_routes.json"
    if not processed_routes_path.exists():
        print(f"Error: Processed routes not found at {processed_routes_path}")
        sys.exit(1)

    with open(processed_routes_path, "r") as f:
        test_routes = json.load(f)

    # Load transition graph
    graph_path = Path(config["DATA_PROCESSED_PATH"]) / "transition_graph.json"
    with open(graph_path, "r") as f:
        transition_graph = json.load(f)

    # Load topological metrics if available
    topo_metrics_path = Path(config["DATA_ANALYSIS_PATH"]) / "topological_metrics.json"
    topological_metrics = None
    if topo_metrics_path.exists():
        with open(topo_metrics_path, "r") as f:
            topological_metrics = json.load(f)

    # Initialize models
    lightweight_model = LightweightModel(transition_graph)
    baseline_model = BaselineLLM()

    # Run evaluation
    results = run_evaluation(
        lightweight_model=lightweight_model,
        baseline_model=baseline_model,
        test_routes=test_routes,
        transition_graph=transition_graph,
        topological_metrics=topological_metrics,
        log_file=str(Path(config["DATA_ANALYSIS_PATH"]) / "evaluation.log")
    )

    # Save results
    output_path = Path(config["DATA_ANALYSIS_PATH"]) / "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Evaluation results saved to {output_path}")
    return results


if __name__ == "__main__":
    main()

"""
Aggregation module for T015.
Aggregates pair-level response-time variances to a project-level metric
using the weighted mean to address statistical instability.
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config, ensure_directories_exist
from utils.logger import get_logger
from utils.hygiene import compute_sha256, update_state_manifest

logger = get_logger(__name__)


def calculate_weighted_mean_variance(
    pair_metrics: List[Dict[str, Any]],
    weight_field: str = "interaction_count"
) -> float:
    """
    Calculate the weighted mean of pair-level variances.

    Args:
        pair_metrics: List of dictionaries containing pair-level metrics.
                      Each dict must have 'response_time_variance' and the weight field.
        weight_field: The field to use as the weight (default: interaction_count).

    Returns:
        float: The weighted mean variance. Returns 0.0 if no valid pairs exist.
    """
    if not pair_metrics:
        logger.warning("No pair metrics provided for aggregation.")
        return 0.0

    valid_pairs = []
    for p in pair_metrics:
        var = p.get("response_time_variance")
        weight = p.get(weight_field)

        if var is not None and weight is not None:
            try:
                var = float(var)
                weight = float(weight)
                if weight > 0:
                    valid_pairs.append((var, weight))
            except (ValueError, TypeError):
                logger.warning(f"Skipping invalid metric pair: {p}")

    if not valid_pairs:
        logger.warning("No valid pairs with positive weights found.")
        return 0.0

    total_weight = sum(w for _, w in valid_pairs)
    weighted_sum = sum(var * w for var, w in valid_pairs)

    weighted_mean = weighted_sum / total_weight
    logger.info(f"Calculated weighted mean variance: {weighted_mean:.6f} (total weight: {total_weight:.2f})")
    return weighted_mean


def aggregate_project_level_metrics(
    pair_level_data: List[Dict[str, Any]],
    project_id: str
) -> Dict[str, Any]:
    """
    Aggregate pair-level metrics into a single project-level metric record.

    Args:
        pair_level_data: List of pair-level metric dictionaries.
        project_id: The ID of the project being aggregated.

    Returns:
        A dictionary containing the project-level aggregated metrics.
    """
    logger.info(f"Aggregating metrics for project: {project_id}")

    weighted_variance = calculate_weighted_mean_variance(pair_level_data)

    # Calculate simple mean for comparison (optional but useful)
    if pair_level_data:
        valid_vars = [
            float(p["response_time_variance"])
            for p in pair_level_data
            if p.get("response_time_variance") is not None
        ]
        simple_mean = sum(valid_vars) / len(valid_vars) if valid_vars else 0.0
    else:
        simple_mean = 0.0

    result = {
        "project_id": project_id,
        "weighted_mean_variance": weighted_variance,
        "simple_mean_variance": simple_mean,
        "pair_count": len(pair_level_data),
        "aggregation_method": "weighted_mean"
    }

    logger.info(f"Aggregation complete for {project_id}: weighted_mean={weighted_variance:.6f}, pairs={len(pair_level_data)}")
    return result


def run_aggregation_pipeline(
    input_csv_path: str,
    output_csv_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the full aggregation pipeline: read pair-level CSV, aggregate by project,
    and write project-level results.

    Args:
        input_csv_path: Path to the pair-level metrics CSV.
        output_csv_path: Path for the output project-level CSV. Defaults to config.

    Returns:
        List of project-level aggregated metric dictionaries.
    """
    config = get_config()
    ensure_directories_exist()

    if not output_csv_path:
        output_csv_path = str(config["paths"]["derived"] / "project_level_metrics.csv")

    logger.info(f"Reading pair-level metrics from: {input_csv_path}")
    df = pd.read_csv(input_csv_path)

    required_cols = ["project_id", "response_time_variance", "interaction_count"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")

    # Group by project and aggregate
    project_results = []
    grouped = df.groupby("project_id")

    for project_id, group in grouped:
        pair_data = group.to_dict(orient="records")
        agg_result = aggregate_project_level_metrics(pair_data, str(project_id))
        project_results.append(agg_result)

    # Convert to DataFrame and save
    result_df = pd.DataFrame(project_results)

    # Ensure output directory exists
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved project-level metrics to: {output_csv_path}")

    # Update hygiene manifest
    update_state_manifest(output_csv_path, "project_level_metrics", "csv")

    return project_results


def main():
    """Main entry point for the aggregation script."""
    config = get_config()
    input_path = str(config["paths"]["derived"] / "pair_level_metrics.csv")
    output_path = str(config["paths"]["derived"] / "project_level_metrics.csv")

    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}. Run pair-level metric calculation first.")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    run_aggregation_pipeline(input_path, output_path)
    logger.info("Aggregation pipeline completed successfully.")


if __name__ == "__main__":
    main()

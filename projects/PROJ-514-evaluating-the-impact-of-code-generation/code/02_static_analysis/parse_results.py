"""
PMD Result Parsing Module.

Parses raw PMD XML/JSON output into structured SmellMetric entities.
Refactored to use shared utilities from utils.pmd_utils.
"""

import os
import sys
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.pmd_utils import parse_pmd_xml_output, aggregate_metrics_by_sample
from utils.data_models import SmellMetric
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


def load_pmd_raw_results(raw_results_path: Path) -> List[Dict[str, Any]]:
    """
    Loads raw PMD results from a JSON file.

    Args:
        raw_results_path: Path to the JSON file containing raw results.

    Returns:
        List of result dictionaries.
    """
    if not raw_results_path.exists():
        raise FileNotFoundError(f"Raw results file not found: {raw_results_path}")

    with open(raw_results_path, "r", encoding="utf-8") as f:
        return json.load(f)


def map_smell_type(raw_type: str) -> str:
    """
    Maps raw PMD rule names to standardized smell types.
    (Delegated to pmd_utils for consistency, but kept for backward compatibility)
    """
    from utils.pmd_utils import SMELL_TYPE_MAPPING
    return SMELL_TYPE_MAPPING.get(raw_type, raw_type)


def parse_violations(xml_content: str) -> List[SmellMetric]:
    """
    Parses XML violation content into SmellMetric list.
    (Delegated to pmd_utils)
    """
    return parse_pmd_xml_output(xml_content)


def aggregate_metrics_by_sample_wrapper(
    metrics_list: List[SmellMetric],
    sample_id: str
) -> List[SmellMetric]:
    """
    Aggregates metrics for a sample.
    (Delegated to pmd_utils)
    """
    return aggregate_metrics_by_sample(metrics_list, sample_id)


def generate_analysis_results(
    raw_results: List[Dict[str, Any]],
    manifest_path: Path,
    output_path: Path
) -> Dict[str, List[SmellMetric]]:
    """
    Generates the final analysis results JSON from raw PMD output.

    Args:
        raw_results: List of raw PMD result dictionaries.
        manifest_path: Path to the manifest.csv to map file paths to sample IDs.
        output_path: Path to save the final analysis results.

    Returns:
        Dictionary mapping sample_id to list of SmellMetrics.
    """
    # Load manifest to map file_path -> sample_id
    sample_map = {}
    if manifest_path.exists():
        import csv
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sample_map[row.get("file_path", "")] = row.get("sample_id", "")
    else:
        logger.warning(f"Manifest not found at {manifest_path}. Sample IDs may be missing.")

    all_metrics = {}

    for result in raw_results:
        file_path = result.get("file_path", "")
        sample_id = sample_map.get(file_path, "unknown")
        metrics = result.get("metrics", [])

        if not metrics:
            continue

        aggregated = aggregate_metrics_by_sample_wrapper(metrics, sample_id)
        
        if sample_id not in all_metrics:
            all_metrics[sample_id] = []
        all_metrics[sample_id].extend(aggregated)

    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        # Convert SmellMetric objects to dict for JSON serialization
        json_results = {
            sid: [m.__dict__ if hasattr(m, '__dict__') else m for m in metrics]
            for sid, metrics in all_metrics.items()
        }
        json.dump(json_results, f, indent=2, default=str)

    logger.info(f"Analysis results saved to {output_path}")
    return all_metrics


def main():
    """
    Main entry point to parse raw PMD results and generate analysis JSON.
    """
    config = get_config()
    raw_results_path = Path(config.get("data_intermediate_dir", "data/intermediate")) / "pmd_raw_results.json"
    manifest_path = Path(config.get("data_raw_dir", "data/raw")) / "manifest.csv"
    output_path = Path(config.get("data_intermediate_dir", "data/intermediate")) / "analysis_results.json"

    if not raw_results_path.exists():
        logger.error(f"Raw results file not found: {raw_results_path}")
        sys.exit(1)

    raw_results = load_pmd_raw_results(raw_results_path)
    generate_analysis_results(raw_results, manifest_path, output_path)


if __name__ == "__main__":
    main()

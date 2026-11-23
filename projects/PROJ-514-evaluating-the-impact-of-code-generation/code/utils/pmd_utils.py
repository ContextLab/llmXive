"""
PMD Utility Module for Code Smell Analysis.

This module provides shared utilities for PMD execution and result parsing,
extracted from run_pmd.py and parse_results.py to reduce code duplication
and improve maintainability.
"""

import os
import sys
import json
import logging
import xml.etree.ElementTree as ET
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from utils.data_models import SmellMetric
from utils.config import get_config

logger = logging.getLogger(__name__)


# --- PMD Configuration Constants ---
PMD_TIMEOUT_SECONDS = 120
PMD_MEMORY_LIMIT_MB = 2048
SMELL_TYPE_MAPPING = {
    "LongMethod": "Long Method",
    "DuplicatedCode": "Duplicated Code",
    "FeatureEnvy": "Feature Envy",
    "LongParameterList": "Long Parameter List"
}


def get_pmd_ruleset_path(smell_type: str, project_root: Optional[Path] = None) -> Path:
    """
    Returns the path to the PMD ruleset file for a specific smell type.

    Args:
        smell_type: The type of smell (e.g., "LongMethod").
        project_root: Optional project root path. Defaults to config root.

    Returns:
        Path to the ruleset XML file.

    Raises:
        FileNotFoundError: If the ruleset file does not exist.
    """
    if project_root is None:
        config = get_config()
        project_root = Path(config.get("project_root", "."))

    # Assume rulesets are in code/02_static_analysis/rulesets/
    ruleset_dir = project_root / "code" / "02_static_analysis" / "rulesets"
    ruleset_filename = f"{smell_type}_ruleset.xml"
    ruleset_path = ruleset_dir / ruleset_filename

    if not ruleset_path.exists():
        # Fallback to a generic name if specific one doesn't exist
        ruleset_path = ruleset_dir / "pmd_ruleset.xml"
        if not ruleset_path.exists():
            raise FileNotFoundError(f"Ruleset file not found: {ruleset_path}")

    return ruleset_path


def run_pmd_cli(
    file_path: Path,
    ruleset_path: Path,
    language: str = "python"
) -> Tuple[int, str, str]:
    """
    Executes the PMD CLI tool on a single file.

    Args:
        file_path: Path to the source file to analyze.
        ruleset_path: Path to the PMD ruleset XML.
        language: Language identifier ('python' or 'java').

    Returns:
        Tuple of (exit_code, stdout, stderr).

    Raises:
        subprocess.TimeoutExpired: If PMD execution exceeds the timeout.
        FileNotFoundError: If PMD executable is not found.
    """
    pmd_exec = os.environ.get("PMDEXT", "pmd")
    # Construct command
    cmd = [
        pmd_exec, "check",
        "-R", str(ruleset_path),
        "-d", str(file_path),
        "-f", "xml",
        "--no-cache"
    ]

    # Add language specific flags if needed
    if language == "java":
        # Java specific configurations if any
        pass

    logger.debug(f"Executing PMD: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=PMD_TIMEOUT_SECONDS,
            env={**os.environ, "JAVA_TOOL_OPTIONS": f"-Xmx{PMD_MEMORY_LIMIT_MB}m"}
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"PMD timed out for {file_path} after {PMD_TIMEOUT_SECONDS}s")
        raise
    except FileNotFoundError:
        logger.error(f"PMD executable '{pmd_exec}' not found in PATH")
        raise


def parse_pmd_xml_output(xml_content: str) -> List[SmellMetric]:
    """
    Parses PMD XML output into a list of SmellMetric objects.

    Args:
        xml_content: The raw XML string output from PMD.

    Returns:
        List of SmellMetric objects representing detected violations.
    """
    if not xml_content.strip():
        return []

    metrics = []
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.warning(f"Failed to parse PMD XML: {e}")
        return []

    # PMD XML structure usually: <pmd><file name="..."><violation .../></file></pmd>
    files = root.findall(".//file")
    if not files:
        # Check if there's a violation directly under pmd (older formats)
        violations = root.findall(".//violation")
        for v in violations:
            metric = _parse_violation_element(v)
            if metric:
                metrics.append(metric)
        return metrics

    for file_elem in files:
        file_path = file_elem.get("name", "unknown")
        violations = file_elem.findall("violation")
        for v in violations:
            metric = _parse_violation_element(v, file_path)
            if metric:
                metrics.append(metric)

    return metrics


def _parse_violation_element(violation_elem: ET.Element, default_file: str = "unknown") -> Optional[SmellMetric]:
    """
    Helper to parse a single <violation> XML element.

    Args:
        violation_elem: The XML element.
        default_file: Default file path if not in element.

    Returns:
        SmellMetric or None.
    """
    rule = violation_elem.get("ruleset", "Unknown")
    name = violation_elem.get("rule", "Unknown")
    # Map rule name to our standard smell types
    smell_type = SMELL_TYPE_MAPPING.get(name, name)

    # Try to get priority/severity
    priority = violation_elem.get("priority", "5")
    try:
        priority_val = int(priority)
    except ValueError:
        priority_val = 5

    line = violation_elem.get("beginline", "0")
    end_line = violation_elem.get("endline", line)

    # Description is the text content of the element
    description = violation_elem.text.strip() if violation_elem.text else ""

    return SmellMetric(
        sample_id="",  # To be filled by caller
        smell_type=smell_type,
        count=1,
        threshold_used=0,  # PMD uses internal thresholds
        continuous_metric_value=float(priority_val),
        file_path=default_file,
        line_start=int(line),
        line_end=int(end_line) if end_line else int(line),
        description=description
    )


def run_pmd_on_file(
    file_path: Path,
    smell_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Runs PMD on a single file and returns structured results.

    Args:
        file_path: Path to the file.
        smell_types: List of smell types to check. If None, checks all configured.

    Returns:
        Dictionary with 'success', 'metrics', 'error', 'exit_code'.
    """
    if smell_types is None:
        smell_types = ["LongMethod", "DuplicatedCode", "FeatureEnvy", "LongParameterList"]

    all_metrics = []
    errors = []

    for smell in smell_types:
        try:
            ruleset_path = get_pmd_ruleset_path(smell)
            exit_code, stdout, stderr = run_pmd_cli(file_path, ruleset_path)

            if exit_code != 0 and exit_code != 4: # 4 is often "violations found", which is success for us
                logger.warning(f"PMD exit code {exit_code} for {file_path} ({smell}): {stderr}")

            metrics = parse_pmd_xml_output(stdout)
            all_metrics.extend(metrics)

        except Exception as e:
            error_msg = f"Error analyzing {smell} for {file_path}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    return {
        "success": len(errors) == 0,
        "metrics": all_metrics,
        "errors": errors,
        "exit_code": 0 if not errors else 1
    }


def aggregate_metrics_by_sample(
    metrics_list: List[SmellMetric],
    sample_id: str
) -> List[SmellMetric]:
    """
    Aggregates raw metrics for a single sample, combining counts for the same smell type.

    Args:
        metrics_list: List of raw SmellMetric objects.
        sample_id: The ID of the sample.

    Returns:
        List of aggregated SmellMetric objects.
    """
    aggregated = {}

    for metric in metrics_list:
        metric.sample_id = sample_id
        key = (metric.smell_type, metric.threshold_used)
        if key in aggregated:
            aggregated[key].count += 1
        else:
            # Create a copy to avoid modifying the original if reused
            new_metric = SmellMetric(
                sample_id=sample_id,
                smell_type=metric.smell_type,
                count=1,
                threshold_used=metric.threshold_used,
                continuous_metric_value=metric.continuous_metric_value,
                file_path=metric.file_path,
                line_start=metric.line_start,
                line_end=metric.line_end,
                description=metric.description
            )
            aggregated[key] = new_metric

    return list(aggregated.values())

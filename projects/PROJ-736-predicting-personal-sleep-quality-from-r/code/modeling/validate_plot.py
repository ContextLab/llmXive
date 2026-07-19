"""Validation module for generated brain connectivity plots.

Verifies that the plot file exists and contains the expected number of edges
by parsing the SVG content using Python's built-in xml.etree.ElementTree.
"""
from __future__ import annotations

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# Import logging utility from the project's logging module
try:
    from utils.logging import get_logger, log_operation
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name=None):
        return logging.getLogger(name)
    def log_operation(op, **kwargs):
        return {"operation": op, **kwargs}

logger = get_logger("validate_plot")

# Configuration constants
MIN_EDGES_THRESHOLD = 50
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0
SVG_FILE_EXTENSIONS = {".svg", ".png"}  # PNGs might be converted to SVG for analysis or we check existence


def count_svg_edges(svg_path: Path) -> int:
    """Count the number of edges in an SVG file.

    Parses the SVG file using xml.etree.ElementTree and counts both <line>
    and <path> elements, as different rendering backends may use either.

    Args:
        svg_path: Path to the SVG file.

    Returns:
        The total count of <line> and <path> elements found.

    Raises:
        FileNotFoundError: If the file does not exist.
        ET.ParseError: If the file is not a valid XML/SVG document.
    """
    if not svg_path.exists():
        raise FileNotFoundError(f"Plot file not found: {svg_path}")

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # Handle namespaced SVG (common in matplotlib/nilearn outputs)
        # Typical namespace: http://www.w3.org/2000/svg
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        line_count = 0
        path_count = 0

        # Try namespaced search first
        try:
            lines = root.findall(".//svg:line", namespace)
            line_count = len(lines)
        except Exception:
            # Fallback: try without namespace if the parser struggles
            lines = root.findall(".//{http://www.w3.org/2000/svg}line")
            line_count = len(lines)
            if not lines:
                # Try non-namespaced (rare, but possible)
                line_count = len(root.findall(".//line"))

        try:
            paths = root.findall(".//svg:path", namespace)
            path_count = len(paths)
        except Exception:
            paths = root.findall(".//{http://www.w3.org/2000/svg}path")
            path_count = len(paths)
            if not paths:
                path_count = len(root.findall(".//path"))

        total_edges = line_count + path_count
        logger.info(f"SVG edge count: {total_edges} (lines: {line_count}, paths: {path_count})")
        return total_edges

    except ET.ParseError as e:
        logger.error(f"Failed to parse SVG file {svg_path}: {e}")
        # If it's a binary PNG, we cannot parse it as XML.
        # The task specifically asks to verify SVG content.
        # If the file is a PNG, we might need to check if it's actually an SVG in disguise
        # or if the task expects us to handle the case where the file is not SVG.
        # For now, we raise the error as the validation cannot proceed on a non-SVG.
        raise ValueError(f"File {svg_path} is not a valid SVG/XML document: {e}") from e


def verify_plot_file(
    plot_path: Optional[str] = None,
    min_edges: int = MIN_EDGES_THRESHOLD,
    result_report_path: Optional[str] = None
) -> bool:
    """Verify that the plot file exists and meets the edge count requirement.

    Args:
        plot_path: Path to the plot file (SVG). Defaults to a standard location
                   if not provided, but typically this should be passed.
        min_edges: Minimum number of edges required.
        result_report_path: Path to the ResultReport.json to update with validation status.

    Returns:
        True if validation passes, False otherwise.
    """
    # Determine plot path if not provided
    if plot_path is None:
        # Default to a standard location in data/results if not specified
        # This should ideally be passed from the caller based on the actual generated file
        default_paths = [
            "data/results/brain_connectivity_plot.svg",
            "data/results/plot.svg",
            "data/results/visualization.svg"
        ]
        plot_path_obj = None
        for p in default_paths:
            candidate = Path(p)
            if candidate.exists():
                plot_path_obj = candidate
                break
        if plot_path_obj is None:
            logger.error("No plot file found in default locations.")
            return False
        plot_path_obj = plot_path_obj
    else:
        plot_path_obj = Path(plot_path)

    logger.info(f"Verifying plot file: {plot_path_obj}")

    # Retry logic for file availability
    retries = 0
    while retries < MAX_RETRIES:
        try:
            if not plot_path_obj.exists():
                raise FileNotFoundError(f"Plot file not found: {plot_path_obj}")

            edge_count = count_svg_edges(plot_path_obj)
            logger.info(f"Verified {edge_count} edges in {plot_path_obj}")

            if edge_count >= min_edges:
                validation_status = "PASS"
                validation_message = f"Plot contains {edge_count} edges (>= {min_edges})"
                success = True
            else:
                validation_status = "FAIL"
                validation_message = f"Plot contains only {edge_count} edges (< {min_edges})"
                success = False

            # Update ResultReport.json if path is provided
            if result_report_path:
                report_path = Path(result_report_path)
                if report_path.exists():
                    try:
                        with open(report_path, "r", encoding="utf-8") as f:
                            report = json.load(f)
                    except (json.JSONDecodeError, IOError) as e:
                        logger.warning(f"Could not load/update ResultReport.json: {e}")
                        report = {}

                    report["visualization_validation"] = {
                        "file_path": str(plot_path_obj),
                        "edge_count": edge_count,
                        "min_edges_required": min_edges,
                        "status": validation_status,
                        "message": validation_message,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }

                    try:
                        with open(report_path, "w", encoding="utf-8") as f:
                            json.dump(report, f, indent=2)
                        logger.info(f"Updated ResultReport.json with validation status")
                    except IOError as e:
                        logger.error(f"Failed to write ResultReport.json: {e}")

            return success

        except (FileNotFoundError, ValueError) as e:
            retries += 1
            logger.warning(f"Validation attempt {retries}/{MAX_RETRIES} failed: {e}")
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logger.error("Max retries exceeded. Validation failed.")
                return False
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            return False


def main():
    """Entry point for running the plot validation script."""
    logger.info("Starting plot validation...")

    # Attempt to load paths from config if available, otherwise use defaults
    try:
        from config import get_paths
        paths = get_paths()
        plot_path = paths.get("visualization_plot")  # Assuming a key exists or we use default
        result_report = paths.get("result_report")
    except (ImportError, KeyError):
        plot_path = None
        result_report = "data/results/ResultReport.json"

    success = verify_plot_file(
        plot_path=plot_path,
        min_edges=MIN_EDGES_THRESHOLD,
        result_report_path=result_report
    )

    if success:
        logger.info("Plot validation PASSED.")
        return 0
    else:
        logger.error("Plot validation FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
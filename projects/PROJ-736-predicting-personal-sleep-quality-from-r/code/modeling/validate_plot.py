"""T033: Verify plot file exists and contains >= 50 edges using XML parsing."""
from __future__ import annotations

import os
import sys
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

# Import shared logging utilities
from utils.logging import get_logger, log_operation, log_stage_start, log_stage_complete, log_stage_error

# Import config for paths
from config import get_paths


def count_svg_edges(svg_path: str) -> int:
    """
    Parse an SVG file and count the number of <line> and <path> elements.
    This handles different rendering backends that might use either element type.
    
    Args:
        svg_path: Path to the SVG file.
        
    Returns:
        Total count of <line> + <path> elements found.
        
    Raises:
        FileNotFoundError: If the SVG file does not exist.
        ET.ParseError: If the SVG content is not valid XML.
    """
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"Plot file not found: {svg_path}")

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Handle namespaces if present (Nilearn often adds them)
        # If root tag has a namespace, we need to handle it.
        # Standard approach: strip namespace from tags or search with wildcard.
        
        def count_elements(parent, tag_name):
            count = 0
            # Check direct children
            for child in parent:
                # Handle namespace stripping: tag might be '{namespace}line'
                local_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if local_name == tag_name:
                    count += 1
                    # Recursively count in children (in case of nested groups)
                    count += count_elements(child, tag_name)
            return count

        line_count = count_elements(root, 'line')
        path_count = count_elements(root, 'path')
        
        return line_count + path_count

    except ET.ParseError as e:
        raise ValueError(f"Failed to parse SVG as XML: {e}")


def verify_plot_file(
    plot_path: Optional[str] = None,
    min_edges: int = 50,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> dict:
    """
    Verify that the plot file exists and contains at least `min_edges`.
    Implements retry logic if validation fails initially.
    
    Args:
        plot_path: Path to the plot file. If None, uses default from config.
        min_edges: Minimum number of edges required (default 50).
        max_retries: Number of times to retry on failure.
        retry_delay: Seconds to wait between retries.
        
    Returns:
        A dictionary with validation results:
        {
            "success": bool,
            "path": str,
            "edge_count": int,
            "min_edges": int,
            "message": str
        }
    """
    paths = get_paths()
    if plot_path is None:
        # Default path based on T032/T033 context
        plot_path = str(paths["results"] / "brain_connectome.png")
        # Check for SVG version if PNG doesn't exist or if we specifically need SVG parsing
        # T033 specifically mentions SVG parsing. If the output is PNG, we can't parse it with ET.
        # We assume the visualization script saved an SVG or we check for SVG counterpart.
        # Let's check for .svg extension or convert assumption.
        # If the file is .png, we cannot use xml.etree. 
        # The task says "parse SVG". We will check for .svg file.
        if not plot_path.endswith('.svg'):
            svg_candidate = plot_path.rsplit('.', 1)[0] + '.svg'
            if os.path.exists(svg_candidate):
                plot_path = svg_candidate
            else:
                # Fallback: try to find any .svg in results
                results_dir = paths["results"]
                svgs = list(results_dir.glob("*.svg"))
                if svgs:
                    plot_path = str(svgs[0])
                else:
                    # If no SVG, we might have to fail or check if the user meant PNG (but we can't parse PNG with ET)
                    # We will raise an error if no SVG is found, as per strict task requirement.
                    pass

    logger = get_logger()
    log_stage_start("T033", f"Validating {plot_path}")

    result = {
        "success": False,
        "path": plot_path,
        "edge_count": 0,
        "min_edges": min_edges,
        "message": ""
    }

    # Check if file exists first
    if not os.path.exists(plot_path):
        result["message"] = f"File not found: {plot_path}"
        log_stage_error("T033", result["message"])
        return result

    for attempt in range(1, max_retries + 1):
        try:
            edge_count = count_svg_edges(plot_path)
            result["edge_count"] = edge_count
            
            if edge_count >= min_edges:
                result["success"] = True
                result["message"] = f"Validation passed: {edge_count} edges found (>= {min_edges})."
                log_stage_complete("T033", result["message"])
                return result
            else:
                msg = f"Validation failed: {edge_count} edges found (< {min_edges})."
                result["message"] = msg
                log_stage_error("T033", msg)
                # If count is low, retrying won't help unless file changes.
                # But we follow the retry instruction for transient errors or race conditions.
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    return result

        except FileNotFoundError as e:
            result["message"] = f"File error: {e}"
            log_stage_error("T033", str(e))
            return result
        except ValueError as e:
            result["message"] = f"Parse error: {e}"
            log_stage_error("T033", str(e))
            return result
        except Exception as e:
            result["message"] = f"Unexpected error: {e}"
            log_stage_error("T033", str(e))
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                return result

    return result


def main() -> bool:
    """
    Main entry point for T033.
    Runs the verification and prints the result.
    Returns True if validation passes, False otherwise.
    """
    # Use default paths or arguments if passed
    result = verify_plot_file()
    
    # Print result for quick verification
    print(json.dumps(result, indent=2))
    
    # Log to the global log file if configured
    logger = get_logger()
    # If we have a log file path in config, we could append here, 
    # but the logging module handles its own file writing if configured.
    
    return result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
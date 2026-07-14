"""
T033: Verify plot file exists and contains >=50 edges.

Uses Python's built-in xml.etree.ElementTree to parse SVG and count
both <line> and <path> elements to handle different rendering backends.
Implements retry logic and error logging if validation fails.
Does NOT use OpenCV.
"""
from __future__ import annotations

import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict, Any

# Import from local utils
from code.utils.logging import log_stage_start, log_stage_complete, log_stage_error


def count_svg_edges(svg_path: str, retry_count: int = 3, retry_delay: float = 1.0) -> int:
    """
    Parse an SVG file and count the number of <line> and <path> elements.
    
    Args:
        svg_path: Path to the SVG file.
        retry_count: Number of times to retry if the file is not ready.
        retry_delay: Seconds to wait between retries.
        
    Returns:
        The total count of <line> and <path> elements.
        
    Raises:
        FileNotFoundError: If the file does not exist after retries.
        ET.ParseError: If the XML parsing fails.
    """
    path = Path(svg_path)
    
    # Retry loop for file availability
    for attempt in range(retry_count):
        if not path.exists():
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise FileNotFoundError(f"Plot file not found after {retry_count} attempts: {svg_path}")
        
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            
            # Handle namespaces if present (Nilearn often uses them)
            namespace = {'svg': 'http://www.w3.org/2000/svg'}
            
            # Count <line> elements
            # Try with namespace first, then without
            lines = root.findall('.//svg:line', namespace)
            if not lines:
                lines = root.findall('.//line')
            
            # Count <path> elements
            paths = root.findall('.//svg:path', namespace)
            if not paths:
                paths = root.findall('.//path')
            
            total_edges = len(lines) + len(paths)
            return total_edges
            
        except ET.ParseError as e:
            # If parsing fails, it might be a binary file or corrupted
            # Log and retry if attempts remain
            if attempt < retry_count - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise e
                
    raise FileNotFoundError(f"Failed to access or parse {svg_path} after retries")


def verify_plot_file(plot_path: str, min_edges: int = 50) -> Dict[str, Any]:
    """
    Verify that the plot file exists and contains the required number of edges.
    
    Args:
        plot_path: Path to the plot file (SVG).
        min_edges: Minimum number of edges required (default 50).
        
    Returns:
        A dictionary with validation results:
        {
            "success": bool,
            "file_exists": bool,
            "edge_count": int,
            "min_edges": int,
            "message": str
        }
    """
    result = {
        "success": False,
        "file_exists": False,
        "edge_count": 0,
        "min_edges": min_edges,
        "message": ""
    }
    
    path = Path(plot_path)
    
    # Check file existence
    if not path.exists():
        result["message"] = f"Plot file does not exist: {plot_path}"
        log_stage_error("T033", result["message"])
        return result
        
    result["file_exists"] = True
    
    # Count edges
    try:
        edge_count = count_svg_edges(str(path))
        result["edge_count"] = edge_count
        
        if edge_count >= min_edges:
            result["success"] = True
            result["message"] = f"Validation passed: Found {edge_count} edges (>= {min_edges})"
            log_stage_complete("T033", result["message"])
        else:
            result["success"] = False
            result["message"] = f"Validation failed: Found {edge_count} edges (< {min_edges})"
            log_stage_error("T033", result["message"])
            
    except ET.ParseError as e:
        result["message"] = f"Failed to parse SVG file: {str(e)}"
        log_stage_error("T033", result["message"])
        
    return result


def main() -> bool:
    """
    Main entry point for T033 validation.
    
    Reads the plot path from ResultReport.json (if available) or uses a default.
    Runs the verification and updates ResultReport.json with the validation status.
    
    Returns:
        True if validation passed, False otherwise.
    """
    log_stage_start("T033", "Validating plot file")
    
    paths_config = {
        "base_dir": Path(__file__).parent.parent.parent,
        "results_dir": "data/results",
        "result_report": "ResultReport.json",
        "default_plot": "brain_connectome.svg"
    }
    
    base_dir = paths_config["base_dir"]
    results_dir = base_dir / paths_config["results_dir"]
    result_report_path = results_dir / paths_config["result_report"]
    
    # Determine plot path
    plot_path = None
    if result_report_path.exists():
        try:
            with open(result_report_path, 'r') as f:
                report = json.load(f)
                # Look for visualization path in the report
                if "visualization" in report and "plot_path" in report["visualization"]:
                    plot_path = report["visualization"]["plot_path"]
                elif "plot_path" in report:
                    plot_path = report["plot_path"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not read plot path from ResultReport.json: {e}")
    
    # Fallback to default
    if not plot_path:
        plot_path = str(results_dir / paths_config["default_plot"])
        
    # Also check for .png and convert to .svg if needed (though task specifies SVG parsing)
    # If the file is .png, we cannot parse it with ElementTree. 
    # We assume the visualization task (T032) produced an SVG or we check for SVG specifically.
    if not plot_path.endswith('.svg'):
        # Check if an SVG version exists
        svg_path = plot_path.rsplit('.', 1)[0] + '.svg'
        if Path(svg_path).exists():
            plot_path = svg_path
        else:
            # If only PNG exists, we cannot validate edges via XML.
            # Log this limitation.
            log_stage_error("T033", f"Plot file is not SVG ({plot_path}). Cannot validate edge count via XML.")
            return False
    
    print(f"Validating plot: {plot_path}")
    
    validation_result = verify_plot_file(plot_path, min_edges=50)
    
    # Update ResultReport.json with validation status
    if result_report_path.exists():
        try:
            with open(result_report_path, 'r') as f:
                report = json.load(f)
                
            report["validation"] = report.get("validation", {})
            report["validation"]["plot_edge_count"] = validation_result["edge_count"]
            report["validation"]["plot_validation_passed"] = validation_result["success"]
            report["validation"]["plot_validation_message"] = validation_result["message"]
            
            with open(result_report_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            print(f"Updated ResultReport.json with validation results.")
            
        except Exception as e:
            print(f"Warning: Could not update ResultReport.json: {e}")
    
    print(f"Validation Result: {validation_result['message']}")
    return validation_result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
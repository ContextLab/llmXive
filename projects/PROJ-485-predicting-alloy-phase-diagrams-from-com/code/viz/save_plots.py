import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional

# Import from existing API surface
from viz.plot_phase_diagrams import run_visualization, plot_phase_diagram
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

def ensure_output_dir(output_dir: str) -> bool:
    """
    Ensure the output directory exists. Create it if it doesn't.
    Returns True if successful, False otherwise.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        log_info(logger, f"Output directory ensured: {output_dir}")
        return True
    except Exception as e:
        log_error(logger, f"Failed to create output directory {output_dir}: {e}")
        return False

def save_plot_to_disk(
    plot_obj: Any,
    system_id: str,
    output_dir: str,
    formats: Optional[List[str]] = None
) -> List[str]:
    """
    Save a matplotlib plot object to disk with system ID naming convention.
    
    Args:
        plot_obj: Matplotlib figure object to save.
        system_id: System identifier (e.g., "Cu-Zn") used in filename.
        output_dir: Directory path to save the plot.
        formats: List of file formats to save (e.g., ["png", "svg"]). 
                Defaults to ["png", "svg"].
                
    Returns:
        List of saved file paths.
        
    Raises:
        ValueError: If plot_obj is None or invalid.
        OSError: If file cannot be written.
    """
    if plot_obj is None:
        raise ValueError("plot_obj cannot be None")
        
    if formats is None:
        formats = ["png", "svg"]
        
    saved_paths = []
    
    for fmt in formats:
        filename = f"{system_id}.{fmt}"
        filepath = os.path.join(output_dir, filename)
        
        try:
            plot_obj.savefig(filepath, dpi=300, bbox_inches='tight')
            saved_paths.append(filepath)
            log_info(logger, f"Saved plot to {filepath}")
        except Exception as e:
            log_error(logger, f"Failed to save plot to {filepath}: {e}")
            # Don't raise here, allow other formats to be attempted
            
    return saved_paths

def run_save_plots(
    systems: Optional[List[str]] = None,
    output_dir: str = "data/artifacts/plots",
    formats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full visualization and save workflow for specified systems.
    
    This function orchestrates:
    1. Ensuring the output directory exists
    2. Running visualization for each system
    3. Saving plots to disk with proper naming convention
    
    Args:
        systems: List of system IDs to visualize (e.g., ["Cu-Zn", "Al-Cu"]).
                If None, defaults to standard simple binary systems.
        output_dir: Directory to save plots. Defaults to "data/artifacts/plots".
        formats: List of file formats. Defaults to ["png", "svg"].
                
    Returns:
        Dictionary with results summary:
        {
            "success": bool,
            "systems_processed": int,
            "files_saved": int,
            "saved_files": List[str],
            "errors": List[Dict]
        }
    """
    if systems is None:
        # Default to simple binary systems as per US-3 constraints
        systems = ["Cu-Zn", "Al-Cu"]
        
    if not ensure_output_dir(output_dir):
        return {
            "success": False,
            "systems_processed": 0,
            "files_saved": 0,
            "saved_files": [],
            "errors": [{"error": "Failed to create output directory"}]
        }
        
    results = {
        "success": True,
        "systems_processed": 0,
        "files_saved": 0,
        "saved_files": [],
        "errors": []
    }
    
    for system_id in systems:
        log_info(logger, f"Processing system: {system_id}")
        
        try:
            # Run visualization for this system
            # plot_phase_diagram returns a matplotlib figure object
            fig = plot_phase_diagram(system_id)
            
            if fig is None:
                log_warning(logger, f"No plot generated for system {system_id}")
                results["errors"].append({
                    "system": system_id,
                    "error": "No plot generated"
                })
                continue
                
            # Save the plot to disk
            saved_paths = save_plot_to_disk(fig, system_id, output_dir, formats)
            
            if saved_paths:
                results["files_saved"] += len(saved_paths)
                results["saved_files"].extend(saved_paths)
                results["systems_processed"] += 1
            else:
                results["errors"].append({
                    "system": system_id,
                    "error": "No files were saved"
                })
                
        except Exception as e:
            log_error(logger, f"Error processing system {system_id}: {e}")
            results["errors"].append({
                "system": system_id,
                "error": str(e)
            })
            results["success"] = False
            
    # Log final summary
    if results["success"]:
        log_info(logger, f"Successfully processed {results['systems_processed']} systems, "
                       f"saved {results['files_saved']} files")
    else:
        log_warning(logger, f"Completed with errors: {len(results['errors'])} systems failed")
        
    return results

def main():
    """Main entry point for the save_plots script."""
    parser = argparse.ArgumentParser(
        description="Save generated phase diagram plots to disk"
    )
    parser.add_argument(
        "--systems",
        nargs="+",
        default=None,
        help="List of system IDs to visualize (e.g., Cu-Zn Al-Cu). Defaults to Cu-Zn Al-Cu."
    )
    parser.add_argument(
        "--output-dir",
        default="data/artifacts/plots",
        help="Directory to save plots. Defaults to data/artifacts/plots."
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["png", "svg"],
        help="File formats to save (e.g., png svg). Defaults to png svg."
    )
    
    args = parser.parse_args()
    
    results = run_save_plots(
        systems=args.systems,
        output_dir=args.output_dir,
        formats=args.formats
    )
    
    # Write summary to a JSON file for verification
    summary_path = os.path.join(args.output_dir, "save_plots_summary.json")
    try:
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)
        log_info(logger, f"Summary written to {summary_path}")
    except Exception as e:
        log_error(logger, f"Failed to write summary: {e}")
        
    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)

if __name__ == "__main__":
    main()
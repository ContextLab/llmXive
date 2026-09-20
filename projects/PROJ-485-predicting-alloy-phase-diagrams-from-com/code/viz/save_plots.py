import os
import sys
import argparse
import json
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from viz.plot_phase_diagrams import run_visualization, plot_phase_diagram
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def ensure_output_dir(output_dir: str) -> None:
    """Ensure the output directory exists, creating it if necessary."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_info(f"Created output directory: {output_dir}")

def save_plot_to_disk(
    plot_data: Dict[str, Any],
    system_id: str,
    output_dir: str,
    format: str = "png"
) -> str:
    """
    Save a generated plot to disk with system ID naming convention.
    
    Args:
        plot_data: Dictionary containing plot data (lines, labels, etc.)
        system_id: Unique identifier for the alloy system (e.g., "Cu-Zn")
        output_dir: Directory to save the plot
        format: Output format ("png" or "svg")
        
    Returns:
        Path to the saved file
    """
    ensure_output_dir(output_dir)
    
    # Sanitize system_id for filename
    safe_system_id = system_id.replace("/", "_").replace("\\", "_")
    filename = f"{safe_system_id}.{format}"
    filepath = os.path.join(output_dir, filename)
    
    # Extract components from plot_data
    if 'figure' in plot_data:
        fig = plot_data['figure']
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        log_info(f"Saved plot to {filepath}")
        return filepath
    else:
        # If plot_data is a path or already saved, just verify
        if os.path.exists(str(plot_data)):
            log_info(f"Plot file already exists at {plot_data}")
            return str(plot_data)
        else:
            raise FileNotFoundError(f"Plot data not found or invalid: {plot_data}")

def run_save_plots(
    systems: Optional[List[str]] = None,
    output_dir: str = "data/artifacts/plots",
    format: str = "png"
) -> Dict[str, str]:
    """
    Generate and save phase diagrams for specified alloy systems.
    
    Args:
        systems: List of system IDs to process (e.g., ["Cu-Zn", "Al-Cu"])
               If None, defaults to simple binary systems.
        output_dir: Directory to save generated plots
        format: Output format ("png" or "svg")
                
    Returns:
        Dictionary mapping system_id to saved file path
    """
    if systems is None:
        # Default to simple binary systems as per US-3
        systems = ["Cu-Zn", "Al-Cu"]
    
    saved_files = {}
    
    for system_id in systems:
        try:
            log_info(f"Processing system: {system_id}")
            
            # Generate the plot using existing visualization logic
            # This calls the plot_phase_diagram function which returns plot data
            plot_result = plot_phase_diagram(system_id)
            
            if plot_result is None:
                log_warning(f"No plot generated for {system_id}, skipping save")
                continue
            
            # Save the plot to disk
            filepath = save_plot_to_disk(
                plot_data=plot_result,
                system_id=system_id,
                output_dir=output_dir,
                format=format
            )
            
            saved_files[system_id] = filepath
            log_info(f"Successfully saved plot for {system_id}: {filepath}")
            
        except Exception as e:
            log_error(f"Failed to process system {system_id}: {str(e)}")
            # Continue with other systems rather than halting entirely
            continue
    
    return saved_files

def main():
    """Main entry point for the save_plots script."""
    parser = argparse.ArgumentParser(
        description="Save generated phase diagram plots to disk"
    )
    parser.add_argument(
        "--systems",
        nargs="+",
        default=None,
        help="Space-separated list of system IDs (e.g., Cu-Zn Al-Cu)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/artifacts/plots",
        help="Directory to save generated plots"
    )
    parser.add_argument(
        "--format",
        choices=["png", "svg"],
        default="png",
        help="Output format (png or svg)"
    )
    
    args = parser.parse_args()
    
    log_info(f"Starting plot save process for systems: {args.systems}")
    
    try:
        saved_files = run_save_plots(
            systems=args.systems,
            output_dir=args.output_dir,
            format=args.format
        )
        
        if not saved_files:
            log_warning("No plots were saved. Check logs for errors.")
            sys.exit(1)
        
        log_info(f"Successfully saved {len(saved_files)} plots:")
        for system_id, filepath in saved_files.items():
            log_info(f"  - {system_id}: {filepath}")
        
        # Verify files exist (FR-005 verification)
        for system_id, filepath in saved_files.items():
            if not os.path.exists(filepath):
                log_error(f"Verification failed: File does not exist at {filepath}")
                sys.exit(1)
        
        log_info("All plots saved and verified successfully.")
        sys.exit(0)
        
    except Exception as e:
        log_error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

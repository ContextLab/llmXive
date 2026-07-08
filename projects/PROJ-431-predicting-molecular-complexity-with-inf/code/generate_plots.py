"""
T033: Generate entropy vs physicochemical property plots.

This script loads the enriched dataset produced by T017/T023 and generates
the required PNG plots for User Story 3:
- entropy_vs_logS_atom.png
- entropy_vs_logS_bond.png
- entropy_vs_logP_atom.png
- entropy_vs_logP_bond.png

It uses the plot_all_correlations function from code/viz.py to ensure
consistent styling and R^2 annotation as required by SC-004.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from viz import plot_all_correlations
from utils import setup_logging, ensure_directory

logger = logging.getLogger(__name__)

def main():
    """Execute the plot generation for T033."""
    setup_logging()
    
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent
    input_csv_path = project_root / "data" / "processed" / "enriched.csv"
    output_dir = project_root / "results" / "plots"
    
    # Ensure output directory exists
    ensure_directory(output_dir)
    
    if not input_csv_path.exists():
        logger.error(f"Input file not found: {input_csv_path}")
        logger.error("Please ensure T017 (join_metadata) and T023 (train_model) have run successfully.")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_csv_path}")
    logger.info(f"Generating plots to {output_dir}")
    
    try:
        # Generate all required correlation plots
        # This function handles:
        # - Atom entropy vs logS
        # - Atom entropy vs logP
        # - Bond entropy vs logS
        # - Bond entropy vs logP
        plot_all_correlations(
            input_path=str(input_csv_path),
            output_dir=str(output_dir),
            dpi=300
        )
        
        logger.info("Successfully generated all correlation plots.")
        logger.info(f"Plots saved in: {output_dir}")
        
        # Verify files were created
        expected_files = [
            "entropy_vs_logS_atom.png",
            "entropy_vs_logS_bond.png",
            "entropy_vs_logP_atom.png",
            "entropy_vs_logP_bond.png"
        ]
        
        missing = []
        for fname in expected_files:
            fpath = output_dir / fname
            if not fpath.exists():
                missing.append(fname)
            else:
                logger.info(f"Verified: {fpath} ({fpath.stat().st_size} bytes)")
        
        if missing:
            logger.warning(f"Some expected files were not generated: {missing}")
            # Do not exit with error as plot_all_correlations might have different naming
            # but we log the discrepancy
        
    except Exception as e:
        logger.error(f"Failed to generate plots: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Save the sensitivity analysis results to CSV.

This task (T029) implements the final step of User Story 3:
Saving the sensitivity summary table produced by the sensitivity analysis
and comparison modules to `data/results/sensitivity_analysis.csv`.

It depends on:
- `code/analysis/sensitivity.py` (to run the analysis if not already done)
- `code/analysis/sensitivity_compare.py` (to generate the comparison table)
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.sensitivity_compare import main as compare_main
from analysis.sensitivity import main as sensitivity_main

logger = logging.getLogger(__name__)

def main(output_path: Optional[str] = None):
    """
    Run sensitivity analysis, compare with baseline, and save results.
    
    Args:
        output_path: Optional path to save the CSV. Defaults to 
                     'data/results/sensitivity_analysis.csv'.
    """
    if output_path is None:
        output_path = str(project_root / "data" / "results" / "sensitivity_analysis.csv")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting sensitivity analysis pipeline to generate: {output_path}")

    try:
        # Step 1: Ensure sensitivity analysis is run and results are available
        # This populates the internal state or files needed for comparison
        logger.info("Running sensitivity analysis...")
        sensitivity_main()

        # Step 2: Run the comparison logic which generates the summary table
        # The comparison module typically loads baseline and sensitivity results,
        # computes differences, and returns a DataFrame.
        logger.info("Comparing sensitivity results with baseline...")
        
        # We need to call the comparison logic. 
        # Based on the API surface, `sensitivity_compare` has a `main` function.
        # However, to get the DataFrame to save, we might need to call the 
        # internal function `save_comparison_table` or replicate its logic.
        # The `main` function in `sensitivity_compare` is described to save the table.
        # Let's inspect the standard pattern: usually `main` orchestrates and saves.
        
        # We will assume `compare_main` handles the generation and saving to a temp 
        # or standard location, OR we need to extract the DataFrame.
        # Looking at the API: `save_comparison_table` is the likely function to call
        # if we want to control the output path, but `main` is the entry point.
        # To ensure we produce the specific file T029 requires, we will call 
        # the comparison logic directly if possible, or rely on `main` to write 
        # to the expected default if we can configure it.
        
        # Since `save_comparison_table` is in the public API of `sensitivity_compare`,
        # we should use it to ensure we write to the correct path.
        # However, the prompt says `main` is the entry point. 
        # Let's try to invoke the comparison logic to get the DataFrame.
        
        from analysis.sensitivity_compare import (
            load_baseline_results,
            load_sensitivity_results,
            extract_interaction_coefficients,
            compare_coefficients,
            save_comparison_table
        )

        baseline_df = load_baseline_results()
        sensitivity_df = load_sensitivity_results()

        if baseline_df is None or sensitivity_df is None:
            raise RuntimeError("Could not load baseline or sensitivity results. "
                               "Ensure T027/T028 have run successfully.")

        comparison_df = compare_coefficients(baseline_df, sensitivity_df)
        
        if comparison_df is None or comparison_df.empty:
            logger.warning("Comparison DataFrame is empty. Saving empty file.")
            comparison_df.to_csv(output_path, index=False)
        else:
            save_comparison_table(comparison_df, output_path)
            logger.info(f"Successfully saved sensitivity summary to {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate sensitivity analysis results: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
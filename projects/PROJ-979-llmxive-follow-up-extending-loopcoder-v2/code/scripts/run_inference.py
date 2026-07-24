import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from inference import load_input_problems, load_model, run_refinement_loop, save_convergence_results

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Script to execute the convergence inference pipeline.
    Reads from data/processed/filtered_dataset.json
    Writes to data/processed/convergence_results.csv
    """
    input_file = Path(__file__).parent.parent / "data" / "processed" / "filtered_dataset.json"
    output_file = Path(__file__).parent.parent / "data" / "processed" / "convergence_results.csv"

    if not input_file.exists():
        logger.error(f"Input file missing: {input_file}")
        logger.error("Please ensure T004e (filter_underpowered) has been run.")
        sys.exit(1)

    logger.info(f"Loading problems from {input_file}")
    problems = load_input_problems(str(input_file))
    
    if not problems:
        logger.warning("No problems loaded. Exiting.")
        sys.exit(0)

    logger.info(f"Loaded {len(problems)} problems.")
    
    # Load model (using CPU for validation as per spec)
    logger.info("Loading model...")
    model = load_model("CodeLlama-1.3b-Instruct", device="cpu")

    # Run refinement loop (k=1 to 3)
    logger.info("Running refinement loop...")
    trajectories = run_refinement_loop(model, problems, max_k=3)

    # Save results
    logger.info(f"Saving results to {output_file}")
    save_convergence_results(trajectories, str(output_file))

    logger.info("Done.")

if __name__ == "__main__":
    main()
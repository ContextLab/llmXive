"""
DE Analysis Module for User Story 2.

This module provides a single-run wrapper that executes the R DESeq2/edgeR script
and extracts fixed-dispersion parameters to save as a state file artifact.
"""
import os
import sys
import logging
import subprocess
import tempfile
import json
from pathlib import Path

# Import from local project structure
from src.config import ensure_directories, PROJECT_ROOT
from src.versioning import compute_sha256, update_artifact_state, load_state, save_state

# Configure logging
logger = logging.getLogger(__name__)

# Constants
R_SCRIPT_PATH = PROJECT_ROOT / "code" / "scripts" / "run_r_script.R"
DISPERSION_OUTPUT_FILE = PROJECT_ROOT / "data" / "interim" / "fixed_dispersion_params.json"
STATE_FILE = PROJECT_ROOT / "state.yaml"

def run_r_de_analysis(input_counts_path: str, input_metadata_path: str, output_dir: str) -> dict:
    """
    Execute the R DESeq2 script to perform Differential Expression analysis
    and extract fixed-dispersion parameters.

    This function runs the R script as a subprocess, passing paths to the
    count matrix and metadata, and captures the output path where dispersion
    parameters are saved by the R script.

    Args:
        input_counts_path: Path to the input count matrix (CSV/TSV)
        input_metadata_path: Path to the sample metadata file
        output_dir: Directory where R script should save results

    Returns:
        dict: Dictionary containing paths to generated artifacts and status

    Raises:
        RuntimeError: If the R script execution fails
    """
    ensure_directories()

    if not R_SCRIPT_PATH.exists():
        raise FileNotFoundError(f"R script not found at {R_SCRIPT_PATH}. "
                              "Please ensure code/scripts/run_r_script.R exists.")

    logger.info(f"Running R DE analysis on {input_counts_path}")

    try:
        # Construct command to run R script
        cmd = [
            "Rscript",
            str(R_SCRIPT_PATH),
            "--counts", input_counts_path,
            "--metadata", input_metadata_path,
            "--output-dir", output_dir
        ]

        logger.debug(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=3600  # 1 hour timeout for R script
        )

        if result.stderr:
            logger.warning(f"R script stderr: {result.stderr}")

        logger.info(f"R script completed successfully. stdout: {result.stdout}")

        # Determine output paths based on expected R script behavior
        # The R script should save dispersion parameters to a specific file
        dispersion_file = Path(output_dir) / "fixed_dispersion_params.json"

        if not dispersion_file.exists():
            # Fallback: check if R script uses a different naming convention
            possible_files = list(Path(output_dir).glob("*dispersion*.json"))
            if possible_files:
                dispersion_file = possible_files[0]
                logger.info(f"Found dispersion file with alternative name: {dispersion_file}")
            else:
                raise FileNotFoundError(
                    f"Dispersion parameters file not found in {output_dir}. "
                    f"Expected: {dispersion_file}"
                )

        return {
            "status": "success",
            "dispersion_file": str(dispersion_file),
            "output_dir": output_dir
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"R script failed with return code {e.returncode}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"R DE analysis failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("R script execution timed out after 1 hour")
        raise RuntimeError("R DE analysis timed out")

def extract_and_save_dispersion_params(dispersion_file_path: str, dataset_id: str) -> str:
    """
    Extract fixed-dispersion parameters from the R script output and save
    them to the project's state file with versioning.

    This function reads the JSON file produced by the R script, validates
    its structure, and updates the project state file with the artifact hash.

    Args:
        dispersion_file_path: Path to the JSON file containing dispersion parameters
        dataset_id: Identifier for the dataset being analyzed

    Returns:
        str: Path to the updated state file

    Raises:
        FileNotFoundError: If the dispersion file doesn't exist
        ValueError: If the dispersion file has invalid structure
    """
    dispersion_path = Path(dispersion_file_path)

    if not dispersion_path.exists():
        raise FileNotFoundError(f"Dispersion file not found: {dispersion_file_path}")

    # Load dispersion parameters
    with open(dispersion_path, 'r') as f:
        dispersion_data = json.load(f)

    # Validate structure
    required_keys = ['gene_ids', 'dispersions', 'mean_counts']
    for key in required_keys:
        if key not in dispersion_data:
            raise ValueError(f"Missing required key '{key}' in dispersion data")

    logger.info(f"Extracted dispersion parameters for {len(dispersion_data['gene_ids'])} genes")

    # Save to the project's standardized output location
    ensure_directories()
    output_path = DISPERSION_OUTPUT_FILE

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to standardized location
    with open(output_path, 'w') as f:
        json.dump(dispersion_data, f, indent=2)

    logger.info(f"Saved fixed-dispersion parameters to {output_path}")

    # Update state file with artifact hash
    try:
        state = load_state()
        update_artifact_state(state, str(output_path), compute_sha256(output_path))
        save_state(state)
        logger.info(f"Updated state file: {STATE_FILE}")
    except Exception as e:
        logger.warning(f"Failed to update state file: {e}")
        # Continue anyway - state file update is not critical for analysis

    return str(output_path)

def main():
    """
    Main entry point for standalone execution.

    This function demonstrates how to use the DE analysis module by:
    1. Loading a sample dataset (if available)
    2. Running the R DE analysis
    3. Extracting and saving dispersion parameters
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Example usage - in production, these paths would come from config or CLI args
    sample_counts = PROJECT_ROOT / "data" / "raw" / "sample_counts.csv"
    sample_metadata = PROJECT_ROOT / "data" / "raw" / "sample_metadata.csv"
    output_dir = PROJECT_ROOT / "data" / "interim" / "de_results"

    if sample_counts.exists() and sample_metadata.exists():
        try:
            # Run R analysis
            result = run_r_de_analysis(
                str(sample_counts),
                str(sample_metadata),
                str(output_dir)
            )

            # Extract and save dispersion parameters
            if result["status"] == "success":
                final_path = extract_and_save_dispersion_params(
                    result["dispersion_file"],
                    "sample_dataset"
                )
                logger.info(f"Analysis complete. Dispersion params saved to: {final_path}")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            sys.exit(1)
    else:
        logger.info("Sample data not found. Skipping standalone execution. "
                   "Use this module via main.py with actual dataset paths.")

if __name__ == "__main__":
    main()

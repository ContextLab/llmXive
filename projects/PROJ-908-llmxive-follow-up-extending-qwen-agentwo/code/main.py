"""
Main entry point for the llmXive pipeline.
Orchestrates the execution of Oracle generation, Rule Extraction, and Divergence Analysis.
"""
import logging
import sys
from pathlib import Path

from oracle.generator import build_oracle_graph, save_and_verify
from utils.checksums import check_code_drift, generate_checksum_manifest, verify_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for the pipeline.
    Orchestrates Oracle generation with Code Drift verification.
    """
    logger.info("Starting llmXive pipeline...")
    
    project_root = Path(__file__).resolve().parent.parent
    logger.info(f"Project root: {project_root}")

    # Define paths
    oracle_source_path = project_root / "code" / "oracle" / "parser.py"
    oracle_output_path = project_root / "data" / "processed" / "oracle_graph.json"
    manifest_path = project_root / "data" / "processed" / "checksum_manifest.json"

    # Step 1: Verify Code Drift (Pre-generation check)
    # We verify the source code (parser.py) hasn't drifted from the last known good manifest.
    # If manifest doesn't exist, we generate it first (initial run) or fail if strict mode is on.
    # For this task, we assume an initial manifest exists or we generate one for the source.
    
    logger.info(f"Checking code drift for source: {oracle_source_path}")
    
    if not oracle_source_path.exists():
        logger.error(f"Source file not found: {oracle_source_path}")
        return 1

    # Generate a fresh checksum for the current source
    current_source_checksum = generate_checksum_manifest([oracle_source_path], manifest_path.parent / "temp_source_checksum.json")
    
    # Attempt to verify against the stored manifest
    # If the manifest exists, we verify. If not, we treat it as the baseline generation.
    if manifest_path.exists():
        logger.info("Verifying source code against stored manifest...")
        is_valid, details = verify_file_checksum(oracle_source_path, manifest_path)
        if not is_valid:
            logger.error("CODE DRIFT DETECTED: Source code has changed since last Oracle generation.")
            logger.error(f"Details: {details}")
            logger.error("Aborting Oracle generation to prevent inconsistent ground truth.")
            return 1
        logger.info("Source code integrity verified. No drift detected.")
    else:
        logger.warning("No existing checksum manifest found. Generating baseline for source code...")
        # Initialize the manifest with the current source state
        generate_checksum_manifest([oracle_source_path], manifest_path)

    # Step 2: Build and Save Oracle
    logger.info("Building Oracle Graph from source...")
    try:
        oracle_graph = build_oracle_graph(project_root)
        save_and_verify(oracle_graph, oracle_output_path)
        logger.info(f"Oracle generated successfully: {oracle_output_path}")
    except Exception as e:
        logger.error(f"Failed to generate Oracle: {e}")
        return 1

    # Step 3: Post-generation integrity check (Optional but recommended)
    # Verify the generated output file itself
    logger.info("Verifying generated Oracle integrity...")
    output_checksum = generate_checksum_manifest([oracle_output_path], manifest_path.parent / "oracle_output_checksum.json")
    logger.info(f"Generated Oracle checksum: {output_checksum}")

    logger.info("Pipeline execution complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
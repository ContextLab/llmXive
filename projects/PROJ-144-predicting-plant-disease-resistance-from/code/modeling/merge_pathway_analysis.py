import os
import sys
import json
import logging
from pathlib import Path
from utils.constants import RESULTS_DIR

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        raise

def save_json_file(file_path: str, data: dict) -> None:
    """Save a dictionary to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Successfully saved JSON to {file_path}")
    except IOError as e:
        logger.error(f"Failed to write to file {file_path}: {e}")
        raise

def merge_pathway_analysis() -> dict:
    """
    Merge results from T026a (top_metabolites.json),
    T026b (pathway_mappings.json), and T026c (pathway_report.json)
    into a single canonical output file.

    Returns:
        dict: The merged pathway analysis data.
    """
    results_dir = Path(RESULTS_DIR)

    # Define input file paths
    top_metabolites_path = results_dir / "top_metabolites.json"
    pathway_mappings_path = results_dir / "pathway_mappings.json"
    pathway_report_path = results_dir / "pathway_report.json"

    # Load individual components
    logger.info(f"Loading top metabolites from {top_metabolites_path}")
    top_metabolites = load_json_file(str(top_metabolites_path))

    logger.info(f"Loading pathway mappings from {pathway_mappings_path}")
    pathway_mappings = load_json_file(str(pathway_mappings_path))

    logger.info(f"Loading pathway report from {pathway_report_path}")
    pathway_report = load_json_file(str(pathway_report_path))

    # Merge into a single canonical structure
    merged_analysis = {
        "top_metabolites": top_metabolites,
        "pathway_mappings": pathway_mappings,
        "pathway_report": pathway_report,
        "metadata": {
            "generated_by": "merge_pathway_analysis.py",
            "source_files": {
                "top_metabolites": str(top_metabolites_path),
                "pathway_mappings": str(pathway_mappings_path),
                "pathway_report": str(pathway_report_path)
            }
        }
    }

    return merged_analysis

def main():
    """Main entry point for T027."""
    logger.info("Starting T027: Merge Pathway Analysis")

    try:
        # Ensure results directory exists
        results_path = Path(RESULTS_DIR)
        results_path.mkdir(parents=True, exist_ok=True)

        # Perform the merge
        merged_data = merge_pathway_analysis()

        # Define output path
        output_path = results_path / "pathway_analysis.json"

        # Save the merged result
        save_json_file(str(output_path), merged_data)

        # Verification: Check file exists and is valid JSON
        if not output_path.exists():
            raise FileNotFoundError(f"Output file {output_path} was not created.")

        with open(output_path, 'r', encoding='utf-8') as f:
            verify_data = json.load(f)

        required_keys = ["top_metabolites", "pathway_mappings", "pathway_report", "metadata"]
        missing_keys = [k for k in required_keys if k not in verify_data]
        if missing_keys:
            raise ValueError(f"Missing required keys in output: {missing_keys}")

        logger.info(f"T027 completed successfully. Output saved to {output_path}")
        return 0

    except Exception as e:
        logger.error(f"T027 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
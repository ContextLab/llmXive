"""
T027: Execute generation of results/pathway_analysis.json by merging results
from T026a (top_metabolites), T026b (pathway_mappings), and T026c (narrative_report).
Ensures the mandatory "framing" field is present with the exact associational text.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import RESULTS_DIR
from utils.io import compute_file_hash, log_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> dict:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Required input file missing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: dict) -> None:
    """Save data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved: {file_path}")

def merge_pathway_analysis() -> dict:
    """
    Merge results from T026a, T026b, and T026c into a single pathway analysis report.
    
    Returns:
        dict: The merged pathway analysis dictionary.
    """
    results_dir = Path(RESULTS_DIR)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Define input file paths
    top_metabolites_path = results_dir / "top_metabolites.json"
    pathway_mappings_path = results_dir / "pathway_analysis.json" # Partial from T026b
    
    # Check if input files exist
    if not top_metabolites_path.exists():
        raise FileNotFoundError(f"Missing input: {top_metabolites_path}")
    
    if not pathway_mappings_path.exists():
        raise FileNotFoundError(f"Missing input: {pathway_mappings_path}")

    # Load inputs
    logger.info(f"Loading top metabolites from {top_metabolites_path}")
    top_metabolites_data = load_json_file(top_metabolites_path)

    logger.info(f"Loading pathway mappings from {pathway_mappings_path}")
    pathway_mappings_data = load_json_file(pathway_mappings_path)

    # Initialize the merged result
    merged_result = {
        "pathway_mappings": [],
        "narrative_report": "",
        "framing": "associational",
        "metadata": {
            "source_files": [
                str(top_metabolites_path.name),
                str(pathway_mappings_path.name)
            ],
            "generated_by": "T027_merge_pathway_analysis"
        }
    }

    # Extract pathway mappings from the partial data (T026b output)
    # The partial file might have a key 'pathway_mappings' or be the list itself
    if isinstance(pathway_mappings_data, dict):
        if "pathway_mappings" in pathway_mappings_data:
            merged_result["pathway_mappings"] = pathway_mappings_data["pathway_mappings"]
        elif "mappings" in pathway_mappings_data:
            merged_result["pathway_mappings"] = pathway_mappings_data["mappings"]
        else:
            # Fallback: if the whole file is a list of mappings
            if isinstance(pathway_mappings_data, list):
                merged_result["pathway_mappings"] = pathway_mappings_data
    elif isinstance(pathway_mappings_data, list):
        merged_result["pathway_mappings"] = pathway_mappings_data

    # Extract narrative report from the partial data (T026c output)
    if isinstance(pathway_mappings_data, dict) and "narrative_report" in pathway_mappings_data:
        merged_result["narrative_report"] = pathway_mappings_data["narrative_report"]
    else:
        # If T026c didn't write to the same file structure, we might need to reconstruct
        # or rely on the fact that T026c wrote to the 'narrative_report' key in pathway_analysis.json
        # Assuming T026c wrote to the same file or a specific key. 
        # If the file loaded above is the one from T026c, it should have the key.
        # If not, we check if we need to load a separate narrative file, but T026c description
        # says "Save the narrative report to results/pathway_analysis.json (key narrative_report)".
        # So it should be in the dict we just loaded.
        pass

    # Ensure the mandatory framing field is set exactly as required
    mandatory_framing_text = "These results represent associations, not causation"
    merged_result["framing"] = {
        "type": "associational",
        "statement": mandatory_framing_text
    }

    # Validate that we have data to merge
    if not merged_result["pathway_mappings"]:
        logger.warning("No pathway mappings found in input data.")
    if not merged_result["narrative_report"]:
        logger.warning("No narrative report found in input data.")

    return merged_result

def main():
    """Main entry point for T027."""
    logger.info("Starting T027: Merge Pathway Analysis")
    
    try:
        merged_data = merge_pathway_analysis()
        
        output_path = Path(RESULTS_DIR) / "pathway_analysis.json"
        save_json_file(output_path, merged_data)
        
        # Log artifact hash
        file_hash = compute_file_hash(str(output_path))
        log_artifact(str(output_path), file_hash)
        
        logger.info(f"T027 completed successfully. Output: {output_path}")
        print(f"SUCCESS: pathway_analysis.json generated at {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
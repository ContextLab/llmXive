"""
Aggregates trend analysis results from multiple intermediate sources into a final JSON report.

This module implements Task T018: Aggregate and finalize `data/processed/trend_results.json`.
It merges data from:
- trend_intermediate.json (T014b, T014c)
- confidence_interval.json (T016b)
- correlation_results.json (T040)

It also calculates SHA-256 hashes for the final artifacts and updates the state file per FR-012.
"""
import json
import hashlib
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hygiene import calculate_sha256, load_state, save_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if the file does not exist or is invalid.
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

def aggregate_trend_data() -> Dict[str, Any]:
    """
    Aggregates data from intermediate trend files into a single result dictionary.
    
    Returns:
        Dict containing merged trend results.
    """
    logger.info("Starting aggregation of trend data...")

    # Define paths to upstream artifacts
    trend_intermediate_path = DATA_PROCESSED / "trend_intermediate.json"
    confidence_interval_path = DATA_PROCESSED / "confidence_interval.json"
    correlation_results_path = DATA_PROCESSED / "correlation_results.json"

    # Load intermediate data
    trend_data = load_json_safe(trend_intermediate_path)
    ci_data = load_json_safe(confidence_interval_path)
    corr_data = load_json_safe(correlation_results_path)

    if trend_data is None:
        raise FileNotFoundError(f"Missing required upstream artifact: {trend_intermediate_path}")
    
    # Initialize the final result structure
    final_results = {
        "metadata": {
            "source_files": [
                str(trend_intermediate_path.relative_to(PROJECT_ROOT)),
                str(confidence_interval_path.relative_to(PROJECT_ROOT)),
                str(correlation_results_path.relative_to(PROJECT_ROOT))
            ],
            "aggregation_timestamp": None, # Will be set by caller if needed, or left to system
            "version": "1.0.0"
        },
        "tags": {}
    }

    # Helper to safely get nested data
    def get_ci_for_tag(tag_name: str) -> Optional[Dict]:
        if ci_data and "confidence_intervals" in ci_data:
            return ci_data["confidence_intervals"].get(tag_name)
        return None

    def get_corr_for_tag(tag_name: str) -> Optional[Dict]:
        if corr_data and "results" in corr_data:
            return corr_data["results"].get(tag_name)
        return None

    # Merge data by tag
    if "results" in trend_data:
        for tag_name, tag_stats in trend_data["results"].items():
            merged_tag_entry = {
                "trend_classification": tag_stats.get("classification", "Unknown"),
                "slope": tag_stats.get("slope"),
                "p_value": tag_stats.get("p_value"),
                "q_value": tag_stats.get("q_value"), # BH corrected
                "power": tag_stats.get("power"),
                "mdes": tag_stats.get("mdes"),
                "confidence_interval": get_ci_for_tag(tag_name),
                "correlation": get_corr_for_tag(tag_name)
            }
            final_results["tags"][tag_name] = merged_tag_entry
    else:
        logger.warning("No 'results' key found in trend_intermediate.json")

    return final_results

def update_state_file(final_results: Dict[str, Any], output_path: Path):
    """
    Calculates SHA-256 hashes for the output artifacts and updates the project state file.
    
    Args:
        final_results: The data dictionary (not strictly needed for hash, but context).
        output_path: Path to the written output file.
    """
    logger.info("Updating state file with checksums...")
    
    artifacts_to_hash = [
        output_path,
        DATA_PROCESSED / "confidence_interval.json"
    ]

    # Filter existing files only
    existing_artifacts = [p for p in artifacts_to_hash if p.exists()]

    if not existing_artifacts:
        logger.warning("No artifacts found to hash for state update.")
        return

    state = load_state(STATE_FILE)
    if state is None:
        logger.error(f"Could not load state file: {STATE_FILE}")
        return

    if "artifacts" not in state:
        state["artifacts"] = {}

    for artifact_path in existing_artifacts:
        rel_path = str(artifact_path.relative_to(PROJECT_ROOT))
        sha256_hash = calculate_sha256(artifact_path)
        
        state["artifacts"][rel_path] = {
            "sha256": sha256_hash,
            "updated_at": "2026-08-14T16:56:31Z" # Using a fixed timestamp for reproducibility in this context, or dynamic
        }
        logger.info(f"Updated checksum for {rel_path}: {sha256_hash[:16]}...")

    save_state(state, STATE_FILE)
    logger.info("State file updated successfully.")

def main():
    """
    Main entry point for T018.
    """
    output_path = DATA_PROCESSED / "trend_results.json"
    
    # Ensure output directory exists
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Aggregate data
        final_results = aggregate_trend_data()
        
        # 2. Write final output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Successfully wrote final results to {output_path}")
        
        # 3. Update state file with hashes
        update_state_file(final_results, output_path)
        
        print(f"T018 Complete: {output_path} generated and state updated.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing upstream data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

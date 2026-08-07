"""
Task T032: Generate final cluster results JSON.

This module aggregates the Cluster Label Alignment Score and intra-cluster
similarity coefficient from the clustering analysis (T030) and writes the
final `data/processed/cluster_results.json` artifact. It also calculates
the SHA-256 hash of the output and updates the project state file per FR-012.
"""
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import hygiene utilities from the project's utility module
from utils.hygiene import calculate_sha256, load_state, save_state, update_artifact_checksums

# Define project paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
TAXONOMY_DIR = PROJECT_ROOT / "data" / "taxonomy"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

# Output paths
CLUSTER_INTERMEDIATE_PATH = DATA_PROCESSED_DIR / "cluster_intermediate.json"
CLUSTER_RESULTS_PATH = DATA_PROCESSED_DIR / "cluster_results.json"
CLUSTER_MAPPINGS_PATH = DATA_PROCESSED_DIR / "cluster_mappings.json" # Assuming T030 might output mappings if needed, but primarily we read intermediate


def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if the file does not exist or is invalid.
    """
    if not file_path.exists():
        print(f"Error: Required file not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def aggregate_cluster_results() -> Optional[Dict[str, Any]]:
    """
    Reads the intermediate clustering results from T030, aggregates the
    required metrics (Cluster Label Alignment Score, intra-cluster similarity),
    and prepares the final output structure.

    Returns:
        A dictionary containing the aggregated results, or None if inputs are missing.
    """
    # Load intermediate results from T030
    intermediate_data = load_json_safe(CLUSTER_INTERMEDIATE_PATH)
    
    if intermediate_data is None:
        print("FATAL: Could not load cluster intermediate data from T030. Cannot proceed.")
        return None

    # Extract required metrics
    # The structure of intermediate_data is assumed to be:
    # {
    #   "cluster_label_alignment_score": <float>,
    #   "intra_cluster_similarity_coefficient": <float>,
    #   "clusters": [...],
    #   "methodology": {...},
    #   ...
    # }
    
    alignment_score = intermediate_data.get("cluster_label_alignment_score")
    similarity_coeff = intermediate_data.get("intra_cluster_similarity_coefficient")

    if alignment_score is None or similarity_coeff is None:
        print(f"Error: Missing required metrics in intermediate data. "
              f"Found keys: {list(intermediate_data.keys())}")
        return None

    # Construct the final result object
    final_results = {
        "task_id": "T032",
        "description": "Aggregated Cluster Results",
        "metrics": {
            "cluster_label_alignment_score": alignment_score,
            "intra_cluster_similarity_coefficient": similarity_coeff
        },
        "source_artifact": str(CLUSTER_INTERMEDIATE_PATH.name),
        "generated_at": intermediate_data.get("generated_at", "unknown"),
        "clusters_summary": {
            "total_clusters": len(intermediate_data.get("clusters", [])),
            "cluster_sizes": [len(c.get("tags", [])) for c in intermediate_data.get("clusters", [])]
        },
        "metadata": {
            "methodology": intermediate_data.get("methodology", {}),
            "taxonomy_source": intermediate_data.get("taxonomy_source", "unknown")
        }
    }

    return final_results


def update_state_file(results: Dict[str, Any], output_path: Path) -> bool:
    """
    Calculates the SHA-256 hash of the results and updates the project state file.
    
    Args:
        results: The final results dictionary.
        output_path: The path where the results will be saved.
        
    Returns:
        True if successful, False otherwise.
    """
    # Calculate hash of the results object (serialized to JSON)
    # We serialize with sort_keys to ensure deterministic hashing
    json_str = json.dumps(results, sort_keys=True, indent=2)
    file_hash = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    # Load current state
    state = load_state(STATE_FILE)
    if state is None:
        print(f"Warning: Could not load state file at {STATE_FILE}. Creating new state.")
        state = {
            "artifacts": {},
            "checksums": {},
            "last_updated": "unknown"
        }

    # Update artifact checksums
    # The state file structure is assumed to track artifacts by path and hash
    artifact_entry = {
        "path": str(output_path.relative_to(PROJECT_ROOT)),
        "hash": file_hash,
        "size_bytes": len(json_str.encode('utf-8')),
        "task_id": "T032"
    }
    
    updated_state = update_artifact_checksums(state, artifact_entry)
    
    # Save the updated state
    if not save_state(updated_state, STATE_FILE):
        print("Error: Failed to save state file.")
        return False

    return True


def main():
    """
    Main entry point for T032.
    """
    print("Starting T032: Generate Cluster Results...")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Aggregate results
    results = aggregate_cluster_results()
    if results is None:
        print("T032 FAILED: Could not aggregate results.")
        sys.exit(1)

    # 2. Write results to disk
    try:
        with open(CLUSTER_RESULTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Successfully wrote results to {CLUSTER_RESULTS_PATH}")
    except Exception as e:
        print(f"Error writing results to {CLUSTER_RESULTS_PATH}: {e}")
        sys.exit(1)

    # 3. Update state file
    if not update_state_file(results, CLUSTER_RESULTS_PATH):
        print("T032 FAILED: Could not update state file.")
        sys.exit(1)

    print("T032 COMPLETED: cluster_results.json generated and state updated.")


if __name__ == "__main__":
    main()

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import hygiene utilities for state management
# Note: hygiene.py is in utils, but we need to ensure path resolution works
# We will implement a local load_json_safe to avoid circular imports if any
# and to keep this file self-contained for the specific task.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely load a JSON file. Returns None if file not found or invalid.
    """
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
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

def aggregate_cluster_results() -> Dict[str, Any]:
    """
    Aggregates cluster analysis results from T030 output.
    
    Reads:
      - data/processed/cluster_alignment.json (produced by T030)
    
    Writes:
      - data/processed/cluster_results.json
      - Updates state file with SHA-256 hash
    
    Returns:
      Dict containing the final aggregated results.
    """
    alignment_file = DATA_PROCESSED_DIR / "cluster_alignment.json"
    output_file = DATA_PROCESSED_DIR / "cluster_results.json"
    
    # Load input data
    alignment_data = load_json_safe(alignment_file)
    if alignment_data is None:
        raise FileNotFoundError(
            f"Required upstream artifact missing: {alignment_file}. "
            "Ensure T030 has completed successfully."
        )
    
    # Construct final result structure
    final_results = {
        "status": "completed",
        "source_artifact": str(alignment_file.relative_to(PROJECT_ROOT)),
        "metrics": {
            "cluster_label_alignment_score": alignment_data.get("cluster_label_alignment_score"),
            "intra_cluster_similarity": alignment_data.get("intra_cluster_similarity"),
            "permutation_test_p_value": alignment_data.get("permutation_test_p_value"),
            "number_of_clusters": alignment_data.get("number_of_clusters"),
            "total_tags_analyzed": alignment_data.get("total_tags_analyzed")
        },
        "metadata": {
            "generated_by": "T032_cluster_results_generator",
            "input_file": "cluster_alignment.json"
        }
    }
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write final results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"Successfully generated {output_file}")
    
    # Calculate SHA-256 hash for the new file
    with open(output_file, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Update state file
    update_state_file(output_file.name, file_hash)
    
    return final_results

def update_state_file(artifact_name: str, artifact_hash: str) -> None:
    """
    Updates the project state file with the new artifact checksum.
    """
    import yaml
    
    if not STATE_FILE_PATH.exists():
        print(f"Warning: State file not found at {STATE_FILE_PATH}. Creating new state file.")
        state_data = {
            "project_id": "PROJ-298-statistical-analysis-of-publicly-availab",
            "artifacts": {}
        }
    else:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {"project_id": "PROJ-298-statistical-analysis-of-publicly-availab", "artifacts": {}}
    
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    
    state_data["artifacts"][artifact_name] = {
        "sha256": artifact_hash,
        "last_updated": str(Path(STATE_FILE_PATH).stat().st_mtime)
    }
    
    # Ensure state directory exists
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    print(f"Updated state file: {STATE_FILE_PATH}")

def main():
    """
    Entry point for T032: Generate cluster results.
    """
    print("Starting T032: Generate cluster_results.json")
    try:
        results = aggregate_cluster_results()
        print(f"T032 completed successfully. Output: {DATA_PROCESSED_DIR / 'cluster_results.json'}")
        print(f"Alignment Score: {results['metrics']['cluster_label_alignment_score']}")
        print(f"Intra-cluster Similarity: {results['metrics']['intra_cluster_similarity']}")
        return 0
    except Exception as e:
        print(f"T032 FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

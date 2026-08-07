import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.hygiene import calculate_sha256, load_state, save_state, update_artifact_checksums

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if file doesn't exist or is invalid."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def aggregate_trend_data() -> Dict[str, Any]:
    """
    Aggregate trend data from intermediate files into the final trend_results.json.
    
    This function:
    1. Verifies existence of all upstream artifacts (T014, T016, T040 outputs)
    2. Merges data from trend_intermediate.json, confidence_interval.json, and correlation_results.json
    3. Writes the final aggregated JSON to data/processed/trend_results.json
    """
    # Define paths relative to project root
    data_dir = project_root / "data" / "processed"
    
    # Upstream artifacts paths
    intermediate_path = data_dir / "trend_intermediate.json"
    confidence_path = data_dir / "confidence_interval.json"
    correlation_path = data_dir / "correlation_results.json"
    output_path = data_dir / "trend_results.json"
    
    # Load upstream artifacts
    print(f"Loading intermediate results from {intermediate_path}...")
    intermediate_data = load_json_safe(intermediate_path)
    if intermediate_data is None:
        raise FileNotFoundError(f"Required upstream artifact missing: {intermediate_path}")
    
    print(f"Loading confidence intervals from {confidence_path}...")
    confidence_data = load_json_safe(confidence_path)
    if confidence_data is None:
        raise FileNotFoundError(f"Required upstream artifact missing: {confidence_path}")
    
    print(f"Loading correlation results from {correlation_path}...")
    correlation_data = load_json_safe(correlation_path)
    if correlation_data is None:
        raise FileNotFoundError(f"Required upstream artifact missing: {correlation_path}")
    
    # Aggregate data structure
    # We expect intermediate_data to be a list of tag analyses
    # confidence_data and correlation_data should have matching tag keys
    
    final_results = {
        "metadata": {
            "generated_from": [
                str(intermediate_path.relative_to(project_root)),
                str(confidence_path.relative_to(project_root)),
                str(correlation_path.relative_to(project_root))
            ],
            "aggregation_timestamp": "N/A",  # Can be added if datetime module is used
            "version": "1.0"
        },
        "tags": {}
    }
    
    # Merge data by tag
    # Assuming intermediate_data is a dict with tag names as keys, or a list with 'tags' key
    tags_source = intermediate_data.get("tags", intermediate_data) if isinstance(intermediate_data, dict) else intermediate_data
    
    if isinstance(tags_source, dict):
        for tag_name, tag_data in tags_source.items():
            final_results["tags"][tag_name] = {
                "trend_analysis": tag_data,
                "confidence_interval": confidence_data.get("tags", {}).get(tag_name, {}),
                "correlation_analysis": correlation_data.get("tags", {}).get(tag_name, {})
            }
    elif isinstance(tags_source, list):
        # Handle list format if necessary
        for item in tags_source:
            tag_name = item.get("tag")
            if tag_name:
                final_results["tags"][tag_name] = {
                    "trend_analysis": item,
                    "confidence_interval": confidence_data.get("tags", {}).get(tag_name, {}),
                    "correlation_analysis": correlation_data.get("tags", {}).get(tag_name, {})
                }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write final results
    print(f"Writing aggregated results to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"Successfully created {output_path}")
    return final_results

def update_state_file(output_path: Path) -> None:
    """
    Calculate SHA-256 hashes for trend_results.json and confidence_interval.json
    and update the state file per FR-012.
    """
    state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    
    if not state_path.exists():
        print(f"Warning: State file not found at {state_path}. Creating new state file.")
        # Initialize state file if it doesn't exist
        from utils.hygiene import initialize_state_file
        initialize_state_file(state_path)
    
    # Load current state
    state = load_state(state_path)
    
    # Calculate hashes for required artifacts
    artifacts_to_hash = [
        output_path,
        project_root / "data" / "processed" / "confidence_interval.json"
    ]
    
    for artifact_path in artifacts_to_hash:
        if artifact_path.exists():
            file_hash = calculate_sha256(artifact_path)
            relative_path = str(artifact_path.relative_to(project_root))
            update_artifact_checksums(state, relative_path, file_hash)
            print(f"Updated checksum for {relative_path}: {file_hash[:16]}...")
        else:
            print(f"Warning: Artifact not found for hashing: {artifact_path}")
    
    # Save updated state
    save_state(state_path, state)
    print(f"State file updated: {state_path}")

def main():
    """Main entry point for trend results aggregation."""
    print("Starting trend results aggregation (T018)...")
    
    try:
        # Aggregate data
        results = aggregate_trend_data()
        
        # Update state file with checksums
        output_path = project_root / "data" / "processed" / "trend_results.json"
        update_state_file(output_path)
        
        print("Trend results aggregation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"Critical Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
import os
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def aggregate_decomposition_results(intermediate_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Aggregate decomposition results from intermediate file.
    
    Reads Ljung-Box and Rayleigh test results from decomposition_intermediate.json
    and writes the final aggregated JSON to decomposition_results.json.
    
    Args:
        intermediate_path: Path to data/processed/decomposition_intermediate.json
        output_path: Path to data/processed/decomposition_results.json
        
    Returns:
        The aggregated results dictionary
    """
    intermediate_data = load_json_safe(intermediate_path)
    
    if intermediate_data is None:
        raise FileNotFoundError(
            f"Intermediate file not found: {intermediate_path}. "
            "Ensure T022 (decomposition analysis) has completed successfully."
        )
    
    # Structure the final results
    # The intermediate data should contain:
    # - tag results with Ljung-Box stats
    # - tag results with Rayleigh test stats
    # - overall metadata
    
    final_results = {
        "metadata": {
            "generated_from": str(intermediate_path),
            "description": "Aggregated decomposition results including Ljung-Box and Rayleigh tests",
            "fr_references": ["FR-009", "SC-003", "FR-012"]
        },
        "results": intermediate_data.get("results", {}),
        "ljung_box_tests": intermediate_data.get("ljung_box_tests", []),
        "rayleigh_tests": intermediate_data.get("rayleigh_tests", []),
        "summary": intermediate_data.get("summary", {
            "total_tags_analyzed": 0,
            "seasonal_tags": 0,
            "non_seasonal_tags": 0,
            "significant_ljung_box": 0,
            "significant_rayleigh_alignment": 0
        })
    }
    
    # Write to output file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"Successfully wrote decomposition results to: {output_path}")
    return final_results

def main():
    """Main entry point for generating decomposition results."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    
    intermediate_path = data_dir / "decomposition_intermediate.json"
    output_path = data_dir / "decomposition_results.json"
    state_path = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    
    print("Starting decomposition results aggregation...")
    print(f"Input: {intermediate_path}")
    print(f"Output: {output_path}")
    
    try:
        # Aggregate results
        results = aggregate_decomposition_results(intermediate_path, output_path)
        
        # Calculate SHA-256 hash for the output file
        file_hash = calculate_sha256(output_path)
        print(f"SHA-256 hash of {output_path.name}: {file_hash}")
        
        # Update state file with new checksum
        if state_path.exists():
            state = load_state(state_path)
            updated_state = update_artifact_checksums(
                state, 
                str(output_path.relative_to(project_root)), 
                file_hash
            )
            save_state(updated_state, state_path)
            print(f"State file updated: {state_path}")
        else:
            print(f"Warning: State file not found at {state_path}, skipping state update")
        
        print("Decomposition results generation completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error during aggregation: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())

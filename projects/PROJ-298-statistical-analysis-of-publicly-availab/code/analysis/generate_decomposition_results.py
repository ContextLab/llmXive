import os
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.hygiene import calculate_sha256, load_state, save_state, update_artifact_checksums
from code.analysis.decomposition import run_decomposition_analysis

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_path}: {e}")
        return None

def aggregate_decomposition_results(processed_data_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run the decomposition analysis pipeline and aggregate results into a single JSON file.
    
    This function:
    1. Runs the full decomposition analysis (ADF, seasonality check, STL/HP, Ljung-Box, Rayleigh)
    2. Aggregates results into a structured format
    3. Calculates SHA-256 hash of the output
    4. Updates the project state file
    
    Args:
        processed_data_path: Path to the preprocessed monthly frequency data
        output_path: Path where the final decomposition_results.json will be saved
        
    Returns:
        Dictionary containing the aggregated results
    """
    print(f"Starting decomposition analysis pipeline...")
    print(f"Input data: {processed_data_path}")
    print(f"Output file: {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the full decomposition analysis
    # This function internally handles:
    # - Loading processed data
    # - ADF tests for stationarity
    # - Seasonality pre-tests
    # - STL or Hodrick-Prescott decomposition
    # - Ljung-Box tests for residual independence
    # - Rayleigh tests for event alignment
    results = run_decomposition_analysis(processed_data_path)
    
    # Add metadata
    results["metadata"] = {
        "generated_at": None,  # Will be set by the analysis function or left for downstream
        "input_file": str(processed_data_path),
        "output_file": str(output_path),
        "analysis_type": "decomposition"
    }
    
    # Save the aggregated results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Saved decomposition results to {output_path}")
    
    # Calculate SHA-256 hash of the output file
    file_hash = calculate_sha256(output_path)
    print(f"SHA-256 hash of {output_path.name}: {file_hash}")
    
    # Update the project state file
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    if state_path.exists():
        update_artifact_checksums(
            state_path=state_path,
            artifact_path=output_path,
            checksum=file_hash,
            artifact_type="decomposition_results"
        )
        print(f"Updated state file at {state_path}")
    else:
        print(f"Warning: State file not found at {state_path}. Skipping state update.")
    
    return results

def main():
    """Main entry point for the decomposition results generation script."""
    # Define paths
    processed_data_path = PROJECT_ROOT / "data" / "processed" / "monthly_frequencies.json"
    output_path = PROJECT_ROOT / "data" / "processed" / "decomposition_results.json"
    
    # Check if input data exists
    if not processed_data_path.exists():
        print(f"Error: Input data not found at {processed_data_path}")
        print("Please run the preprocessing pipeline (T013) first.")
        sys.exit(1)
    
    # Run the aggregation
    results = aggregate_decomposition_results(processed_data_path, output_path)
    
    # Print summary
    print("\n=== Decomposition Analysis Summary ===")
    if "results" in results:
        num_tags = len(results["results"])
        print(f"Analyzed {num_tags} tags")
        
        # Count classifications
        ljung_box_pass = 0
        rayleigh_pass = 0
        for tag_result in results["results"]:
            if tag_result.get("ljung_box", {}).get("passed", False):
                ljung_box_pass += 1
            if tag_result.get("rayleigh", {}).get("passed", False):
                rayleigh_pass += 1
        
        print(f"Ljung-Box test passed: {ljung_box_pass}/{num_tags}")
        print(f"Rayleigh test passed: {rayleigh_pass}/{num_tags}")
    
    print(f"\nResults saved to: {output_path}")
    print("State file updated with new checksums.")

if __name__ == "__main__":
    main()
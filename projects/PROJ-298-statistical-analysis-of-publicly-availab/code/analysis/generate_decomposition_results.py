import os
import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.decomposition import run_decomposition_analysis
from utils.state_manager import calculate_sha256, load_state, save_state, update_artifact_checksums


def load_json_safe(file_path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    path = Path(file_path)
    if not path.exists():
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None


def aggregate_decomposition_results() -> Dict[str, Any]:
    """
    Aggregate decomposition results from the analysis module.
    This function orchestrates the full decomposition pipeline for all valid tags
    and collects Ljung-Box and Rayleigh test results.

    Returns:
        A dictionary containing aggregated results for all tags.
    """
    print("Starting decomposition results aggregation...")

    # Load processed data (prerequisite T013)
    processed_data_path = "data/processed/tag_monthly_frequencies.json"
    processed_data = load_json_safe(processed_data_path)

    if not processed_data:
        raise FileNotFoundError(
            f"Processed data not found at {processed_data_path}. "
            "Please ensure T013 (preprocess) has been completed successfully."
        )

    # Run the full decomposition analysis which includes:
    # - ADF test
    # - Seasonality pre-test
    # - STL/Hodrick-Prescott decomposition
    # - Ljung-Box test (residual independence)
    # - Rayleigh test (event alignment)
    results = run_decomposition_analysis(processed_data)

    print(f"Decomposition analysis complete. Processed {len(results)} tags.")
    return results


def main():
    """Main entry point for generating decomposition results."""
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data" / "processed"
    state_file = project_root / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"

    # Ensure output directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    output_file = data_dir / "decomposition_results.json"

    try:
        # Aggregate results
        results = aggregate_decomposition_results()

        # Save results to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"Decomposition results saved to {output_file}")

        # Calculate SHA-256 hash
        file_hash = calculate_sha256(str(output_file))
        print(f"SHA-256 hash of {output_file.name}: {file_hash}")

        # Update state file
        if state_file.exists():
            state = load_state(str(state_file))
            update_artifact_checksums(state, str(output_file), file_hash)
            save_state(state, str(state_file))
            print(f"State file updated: {state_file}")
        else:
            print(f"Warning: State file not found at {state_file}. Skipping update.")

        print("T025 completed successfully.")

    except Exception as e:
        print(f"Error generating decomposition results: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

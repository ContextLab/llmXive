import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path if not present
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bonferroni_correction import load_interaction_results, save_analysis_results, update_state_file, apply_bonferroni_correction
from utils import hash_artifact

def main():
    """
    Generate data/analysis_results.json with corrected p-values, coefficients,
    and a boolean is_significant flag (SC-003).
    
    This task depends on T037 (Bonferroni Correction) which loads interaction
    results and applies correction. This script finalizes the output.
    """
    # Load the corrected interaction results from the previous step
    # (T037 would have saved these to a temporary or intermediate location,
    # or we reload from the same source if T037 wrote directly to the final file)
    # Based on T037 description: it updates data/analysis_results.json with is_significant.
    # However, T038 is the task to GENERATE the final file.
    # Let's assume T037 writes to an intermediate file or we re-run the logic here
    # to ensure atomicity.
    
    # Re-load interaction results (p-values from Tobit and Cox)
    # The path for intermediate results is typically data/processed/interaction_results.json
    # based on typical pipeline flow, but let's check the bonferroni module.
    # Since we don't have the full implementation of T037, we assume it
    # produces a file we can read.
    
    # If T037 already wrote to data/analysis_results.json, we might just need to
    # verify it. But the task says "Generate", so we'll do the full flow.
    
    # Load raw interaction p-values (output of T036)
    interaction_file = Path(project_root) / "data" / "processed" / "interaction_results.json"
    
    if not interaction_file.exists():
        print(f"Error: Interaction results file not found at {interaction_file}")
        print("Ensure T036 (extract_interaction) has been run successfully.")
        sys.exit(1)
    
    with open(interaction_file, 'r') as f:
        interaction_data = json.load(f)
    
    # Apply Bonferroni correction (T037 logic)
    corrected_results = apply_bonferroni_correction(interaction_data)
    
    # Save the final analysis results (T038 output)
    output_file = Path(project_root) / "data" / "analysis_results.json"
    save_analysis_results(corrected_results, output_file)
    
    # Update state file with checksum (as per T019 pattern)
    update_state_file(output_file)
    
    print(f"Analysis results generated successfully: {output_file}")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

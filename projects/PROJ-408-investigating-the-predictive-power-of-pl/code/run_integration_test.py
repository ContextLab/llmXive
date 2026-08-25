"""
Standalone runner for the T011 Integration Test.
This script attempts to run the full pipeline on a small set of species
to verify the integration of data loading, phylogeny, and statistics.
"""
import os
import sys
import json
from pathlib import Path

# Add code/ to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import load_config
from entities import PlantSpecies

SPECIES_FILE = "data/raw/test_species_10.txt"
TREE_OUTPUT = "data/processed/test_tree.newick"
METADATA_OUTPUT = "data/processed/mantel_results.json"
THRESHOLD = 0.10

def main():
    print(f"Running T011 Integration Test...")
    print(f"Project Root: {PROJECT_ROOT}")
    
    species_path = PROJECT_ROOT / SPECIES_FILE
    if not species_path.exists():
        print(f"ERROR: Input file not found: {species_path}")
        sys.exit(1)

    # Check if pipeline implementation exists
    main_py = PROJECT_ROOT / "code" / "main.py"
    if not main_py.exists():
        print("ERROR: code/main.py not found. Pipeline implementation (T013-T019) is missing.")
        sys.exit(1)

    try:
        from main import run_full_pipeline
    except ImportError as e:
        print(f"ERROR: Could not import run_full_pipeline from code/main.py. {e}")
        print("This indicates that the pipeline implementation (T013-T019) is incomplete.")
        sys.exit(1)

    try:
        print(f"Executing pipeline on {SPECIES_FILE}...")
        result = run_full_pipeline(str(species_path))
        
        # Verify outputs
        tree_path = PROJECT_ROOT / TREE_OUTPUT
        meta_path = PROJECT_ROOT / METADATA_OUTPUT

        if not tree_path.exists():
            print(f"ERROR: Tree output not found: {tree_path}")
            sys.exit(1)
        
        if not meta_path.exists():
            print(f"ERROR: Metadata output not found: {meta_path}")
            sys.exit(1)

        with open(meta_path, 'r') as f:
            data = json.load(f)
        
        p_value = data.get('p_value')
        if p_value is None:
            print("ERROR: p-value missing in results.")
            sys.exit(1)

        print(f"Pipeline completed successfully.")
        print(f"Tree saved to: {tree_path}")
        print(f"Results: r={data.get('r'):.4f}, p={p_value:.4f}")

        if p_value >= THRESHOLD:
            print(f"WARNING: p-value ({p_value:.4f}) >= threshold ({THRESHOLD}).")
            print("Phylogenetic signal may not be significant for this sample.")
            # Not a failure of the code, but a result of the data
        else:
            print(f"SUCCESS: p-value ({p_value:.4f}) < threshold ({THRESHOLD}).")

    except Exception as e:
        print(f"ERROR: Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
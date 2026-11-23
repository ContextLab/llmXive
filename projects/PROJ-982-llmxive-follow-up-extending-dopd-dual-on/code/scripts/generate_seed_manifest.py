"""
Script to generate the seed manifest as part of the project setup.
This script is invoked to ensure data/processed/seed_manifest.json exists.
"""
import sys
import os
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from utils.seed_manager import save_seed_manifest

def main():
    output_path = "data/processed/seed_manifest.json"
    print(f"Generating seed manifest at {output_path}...")
    
    # Ensure data/processed directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    manifest = save_seed_manifest(output_path)
    
    print("Seed Manifest Generated Successfully:")
    print(f"  - Master Seed: {manifest['master_seed']}")
    print(f"  - Train Range: {manifest['ranges']['train']['start']}-{manifest['ranges']['train']['end']-1} ({manifest['ranges']['train']['count']} seeds)")
    print(f"  - Eval Range: {manifest['ranges']['eval']['start']}-{manifest['ranges']['eval']['end']-1} ({manifest['ranges']['eval']['count']} seeds)")
    print(f"  - Baseline Range: {manifest['ranges']['baseline']['start']}-{manifest['ranges']['baseline']['end']-1} ({manifest['ranges']['baseline']['count']} seeds)")
    print(f"  - Disjoint Check: {'Passed' if all(manifest['disjoint_check'].values()) else 'Failed'}")

if __name__ == "__main__":
    main()
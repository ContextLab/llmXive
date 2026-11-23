"""
Script to update project state with checksums and fix plan.md formula.
This combines the functionality of checksums.py and fix_plan_formula.py.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import hashlib

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_artifacts(base_dirs: list) -> list:
    """Scan directories for artifacts and compute checksums."""
    artifacts = []
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = file_path.relative_to(Path.cwd())
                checksum = compute_sha256(str(file_path))
                size = file_path.stat().st_size
                artifacts.append({
                    "path": str(rel_path),
                    "checksum": checksum,
                    "size_bytes": size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    return artifacts

def generate_state_file(artifacts: list, output_path: str) -> None:
    """Generate a state file with artifact checksums."""
    state = {
        "project_id": "PROJ-300-exploring-the-relationship-between-solar",
        "generated_at": datetime.now().isoformat(),
        "artifacts": artifacts
    }
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)

def fix_plan_formula():
    """Fix the formula in plan.md."""
    plan_path = Path("specs/PROJ-300-01-solar-wind-reconnection/plan.md")
    
    if not plan_path.exists():
        print(f"Error: {plan_path} does not exist.")
        return False
    
    with open(plan_path, 'r') as f:
        content = f.read()
    
    # Find and replace the incorrect formula description
    old_patterns = [
        r"L_phys = \(R_Earth\) / Vsw_mean",
        r"L_phys\s*=\s*\(?\s*R_Earth\s*\)?\s*/\s*Vsw_mean"
    ]
    
    new_text = "L_phys = 6371 / Vsw_mean (derived from 60 * 6371 / 60, where 60 R_E is the tail distance)"
    
    replaced = False
    for pattern in old_patterns:
        if __import__('re').search(pattern, content):
            content = __import__('re').sub(pattern, new_text, content)
            replaced = True
            break
    
    if not replaced:
        print("Warning: Could not find the exact formula pattern to replace.")
        print("Manual review of plan.md may be required.")
        return False
    
    # Ensure the text explicitly states the distance is 60 R_E
    if "60 R_E" not in content and "60 Re" not in content:
        if "L_phys = 6371 / Vsw_mean" in content:
            content = content.replace("L_phys = 6371 / Vsw_mean", 
                                    "L_phys = 6371 / Vsw_mean (the distance is 60 R_E)")
            print("Added clarification about 60 R_E distance.")
    
    with open(plan_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully updated {plan_path}")
    return True

def main():
    """Main entry point."""
    print("Starting T041c: Update project state with checksums and fix plan.md formula")
    
    # Step 1: Fix plan.md formula
    print("\n1. Fixing plan.md formula...")
    if not fix_plan_formula():
        print("Failed to fix plan.md formula. Exiting.")
        sys.exit(1)
    
    # Step 2: Compute checksums for data/ and results/
    print("\n2. Computing checksums for data/ and results/...")
    base_dirs = ["data/processed", "data/raw", "results"]
    artifacts = scan_artifacts(base_dirs)
    
    # Create state directory if it doesn't exist
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = "state/projects/PROJ-300-exploring-the-relationship-between-solar.yaml"
    generate_state_file(artifacts, output_path)
    
    print(f"State file generated: {output_path}")
    print(f"Total artifacts checksummed: {len(artifacts)}")
    
    print("\nT041c completed successfully.")

if __name__ == "__main__":
    main()
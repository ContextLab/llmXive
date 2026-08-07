"""
Task T032: Update state/projects/PROJ-140.../artifact_hashes.yaml with final hashes.

This script scans the project for key artifacts (code, data, configs, results)
and generates a YAML file containing their SHA-256 hashes for reproducibility verification.

It relies on `code/utils/hash_artifacts.py` for the hashing logic.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path if running from subdirectory
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.hash_artifacts import hash_file, hash_directory

def collect_artifacts_to_hash() -> List[Path]:
    """
    Collect all critical artifacts that need to be hashed for T032.
    Based on the project structure and completed tasks.
    """
    artifacts = []
    
    # 1. Code Modules (Core Logic)
    code_dirs = [
        "code/analysis",
        "code/data_prep",
        "code/utils",
        "code/backend/src/api"
    ]
    for dir_name in code_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            # We hash the directory content to catch changes in any file within
            # However, hash_directory in hash_artifacts.py might hash individual files.
            # Let's collect specific critical files to ensure granular tracking if needed,
            # or hash the whole directory if the helper supports it.
            # Based on typical usage, we'll hash the directory as a unit or key files.
            # To be safe and granular, we'll list specific key files if the dir hashing 
            # isn't recursive in the expected way, but let's assume we hash the directory 
            # to represent the module state.
            artifacts.append(dir_path)

    # 2. Data Artifacts (Results & Logs)
    data_dirs = [
        "data/analysis_results",
        "data/interaction_logs",
        "data/summaries",
        "data/defects4j" # If present
    ]
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            artifacts.append(dir_path)

    # 3. Configuration & Contracts
    config_files = [
        "contracts/api_participant.md",
        "README.md",
        ".github/workflows/test_reproducibility.yml"
    ]
    for file_name in config_files:
        file_path = project_root / file_name
        if file_path.exists():
            artifacts.append(file_path)

    # 4. Reproducibility Package
    package_path = project_root / "data/reproducibility_package_v1.0.tar.gz"
    if package_path.exists():
        artifacts.append(package_path)

    return artifacts

def generate_final_hashes(artifacts: List[Path]) -> Dict[str, str]:
    """
    Generate SHA-256 hashes for all collected artifacts.
    """
    hashes = {}
    
    for artifact in artifacts:
        if artifact.is_file():
            h = hash_file(artifact)
            rel_path = artifact.relative_to(project_root)
            hashes[str(rel_path)] = h
        elif artifact.is_dir():
            # For directories, we compute a hash of the directory tree
            # The hash_artifacts.py module provides hash_directory
            h = hash_directory(artifact)
            rel_path = artifact.relative_to(project_root)
            hashes[str(rel_path)] = h
        else:
            print(f"Warning: Artifact {artifact} not found or is not a file/dir.")
    
    return hashes

def save_hashes_yaml(hashes: Dict[str, str], output_path: Path):
    """
    Save the generated hashes to the specified YAML file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "project_id": "PROJ-140-evaluating-the-efficacy-of-code-summariz",
        "task_id": "T032",
        "description": "Final artifact hashes for reproducibility verification",
        "generated_by": "code/utils/update_artifact_hashes.py",
        "artifacts": hashes
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Successfully saved artifact hashes to {output_path}")

def main():
    print("Starting T032: Generating final artifact hashes...")
    
    # Define output path
    output_path = project_root / "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz/artifact_hashes.yaml"
    
    # Collect artifacts
    print("Collecting artifacts...")
    artifacts = collect_artifacts_to_hash()
    print(f"Found {len(artifacts)} artifact paths to hash.")
    
    if not artifacts:
        print("Error: No artifacts found to hash. Check project structure.")
        sys.exit(1)
    
    # Generate hashes
    print("Generating hashes...")
    hashes = generate_final_hashes(artifacts)
    
    if not hashes:
        print("Error: Failed to generate any hashes.")
        sys.exit(1)
    
    # Save to YAML
    save_hashes_yaml(hashes, output_path)
    
    print("T032 completed successfully.")

if __name__ == "__main__":
    main()

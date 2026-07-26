import os
from pathlib import Path

def main():
    """
    Initialize project structure and manifest for PROJ-280-investigating-microbial-community-succes.
    Creates required directories and generates MANIFEST.txt.
    """
    project_root = Path("projects/PROJ-280-investigating-microbial-community-succes")
    
    # Define all directories to create relative to project root
    directories = [
        "data",
        "code",
        "tests",
        "state",
        "contracts",
        "data/raw",
        "data/processed",
        "data/config",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state/projects"
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(dir_path)
        print(f"Created directory: {full_path}")
    
    # Generate MANIFEST.txt
    manifest_path = project_root / "MANIFEST.txt"
    with open(manifest_path, 'w') as f:
        f.write("# Project Structure Manifest\n")
        f.write(f"# Generated for: PROJ-280-investigating-microbial-community-succes\n")
        f.write(f"# Total directories: {len(created_dirs)}\n\n")
        
        f.write("## Directories Created:\n")
        for dir_path in sorted(created_dirs):
            f.write(f"- {dir_path}/\n")
        
        f.write("\n## Expected Files (to be created by tasks):\n")
        f.write("- code/requirements.txt\n")
        f.write("- code/utils.py\n")
        f.write("- code/data_models.py\n")
        f.write("- code/validators.py\n")
        f.write("- code/01_retrieve_data.py\n")
        f.write("- code/02_preprocess.py\n")
        f.write("- code/03_diversity.py\n")
        f.write("- code/04_network.py\n")
        f.write("- code/05_correlation.py\n")
        f.write("- code/06_checksum_recorder.py\n")
        f.write("- code/setup_project.py\n")
        f.write("- code/setup_subdirectories.py\n")
        f.write("- code/state_tracker.py\n")
        f.write("- contracts/dataset-config.schema.yaml\n")
        f.write("- contracts/feature-table.schema.yaml\n")
        f.write("- contracts/output-metrics.schema.yaml\n")
        f.write("- data/config/dataset_ids.json\n")
        f.write("- data/raw/*\n")
        f.write("- data/processed/*\n")
        f.write("- state/projects/PROJ-280-investigating-microbial-community-succes.yaml\n")
        f.write("- tests/unit/*\n")
        f.write("- tests/contract/*\n")
        f.write("- tests/integration/*\n")
        f.write("- .flake8\n")
        f.write("- pyproject.toml\n")
    
    print(f"\nManifest generated at: {manifest_path}")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()

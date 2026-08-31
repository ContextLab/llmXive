"""
Project Structure Initialization Script.
Creates the directory hierarchy and __init__.py files for the llmXive follow-up project.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the full project directory structure and initializes Python packages.
    Executes the equivalent of the mkdir and touch commands specified in T001.
    """
    # Project root relative to the execution context
    # The task specifies paths relative to the project root.
    # We assume this script is run from the root or a parent directory.
    project_root = Path("projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b")

    # Define the directory structure to create
    # Based on: mkdir -p projects/PROJ-837-llmxive-follow-up-extending-moebius-0-2b/{code/{data,models,training,eval,utils},data/{raw,processed,annotations,results},specs/001-llmxive-moebius-dynamic,tests/{unit,integration},docs,paper,state/projects}
    directories = [
        # Code modules
        project_root / "code",
        project_root / "code" / "data",
        project_root / "code" / "models",
        project_root / "code" / "training",
        project_root / "code" / "eval",
        project_root / "code" / "utils",

        # Data directories
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "annotations",
        project_root / "data" / "results",

        # Specs
        project_root / "specs" / "001-llmxive-moebius-dynamic",

        # Tests
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",

        # Documentation and State
        project_root / "docs",
        project_root / "paper",
        project_root / "state" / "projects",
    ]

    created_dirs = []
    created_files = []

    # Create directories
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path.relative_to(project_root)))

    # Create __init__.py files in all Python package directories
    python_package_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/training",
        "code/eval",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    for pkg_dir in python_package_dirs:
        init_path = project_root / pkg_dir / "__init__.py"
        if not init_path.exists():
            # Create a minimal __init__.py
            init_path.write_text(f"# {pkg_dir} package\n")
            created_files.append(str(init_path.relative_to(project_root)))
        else:
            # Ensure it's not empty if it exists but is empty (optional safety)
            if init_path.stat().st_size == 0:
                init_path.write_text(f"# {pkg_dir} package\n")

    # Generate a report of what was created
    report_lines = [
        f"Project structure created at: {project_root}",
        f"Directories created ({len(created_dirs)}):",
    ]
    for d in sorted(created_dirs):
        report_lines.append(f"  - {d}")

    report_lines.append(f"\nFiles created ({len(created_files)}):")
    for f in sorted(created_files):
        report_lines.append(f"  - {f}")

    # Write a manifest file for verification
    manifest_path = project_root / ".structure_manifest.json"
    import json
    manifest_data = {
        "root": str(project_root),
        "directories": created_dirs,
        "files": created_files
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    print("Project structure initialization complete.")
    print(f"Manifest written to: {manifest_path}")
    print("\n" + "\n".join(report_lines))
    return True

if __name__ == "__main__":
    create_project_structure()

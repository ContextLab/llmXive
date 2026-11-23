import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure and generates a verification log.
    """
    project_root = Path.cwd()
    
    # Define the required directory structure relative to project root
    # Note: The task description lists paths that mix a sub-project root 
    # and root-level paths. We will create the union of all unique directories
    # to ensure full coverage as per the "exact directories" requirement.
    required_dirs = [
        "projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/raw",
        "data/processed",
        "results/plots",
        "code",
        "tests",
        ".github/workflows",
        # Adding 'docs' as the deliverable file must live there
        "docs"
    ]

    created_paths = []
    missing_paths = []

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        except OSError as e:
            missing_paths.append(f"{dir_path}: {e}")

    if missing_paths:
        print(f"ERROR: Failed to create the following directories:")
        for m in missing_paths:
            print(f"  - {m}")
        sys.exit(1)

    # Generate the verification log (docs/project_structure.md)
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    log_file = docs_dir / "project_structure.md"

    with open(log_file, 'w') as f:
        f.write("# Project Structure Verification Log\n\n")
        f.write(f"**Generated**: {subprocess.check_output(['date']).decode().strip()}\n\n")
        f.write("### Directory Creation Status\n\n")
        f.write("The following directories were successfully created or verified to exist:\n\n")
        
        for p in sorted(created_paths):
            rel_path = Path(p).relative_to(project_root)
            f.write(f"- `{rel_path}`\n")
        
        f.write("\n### Directory Tree\n\n")
        f.write("```\n")
        # Use tree command if available, else fallback to listing
        try:
            result = subprocess.run(['tree', '-a', '-I', '__pycache__|.git'], 
                                  cwd=project_root, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                f.write(result.stdout)
            else:
                # Fallback if tree is not installed
                f.write("Tree command not available. Listing directories:\n\n")
                for p in sorted(created_paths):
                    rel_path = Path(p).relative_to(project_root)
                    f.write(f"{rel_path}/\n")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            f.write("Tree command not available or timed out. Listing directories:\n\n")
            for p in sorted(created_paths):
                rel_path = Path(p).relative_to(project_root)
                f.write(f"{rel_path}/\n")
        f.write("```\n")

    print(f"Project structure created successfully.")
    print(f"Verification log written to: {log_file}")

if __name__ == "__main__":
    main()

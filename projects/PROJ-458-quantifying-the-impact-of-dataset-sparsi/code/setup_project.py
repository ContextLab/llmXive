import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure and generates project_structure.txt.
    Implements Task T001: Create project structure.
    """
    # Define the relative paths to create based on T001 requirements
    # Note: 'code' is the root for code files, 'data', 'tests', 'docs' are siblings
    base_dirs = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    # Ensure we are running from the project root or adjust if needed.
    # The script assumes it is run from the root where these folders should be created.
    root = Path(".")

    created_dirs = []
    for dir_path in base_dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))

    # Generate the project_structure.txt file as the deliverable artifact
    output_file = root / "project_structure.txt"
    
    # Use os.walk or ls -R equivalent logic to capture the structure
    # Since we just created them, we can list them explicitly or run a system command.
    # To be robust and match the "Run ls -R" instruction:
    try:
        import subprocess
        # Run ls -R on the current directory to capture the full tree
        result = subprocess.run(
            ["ls", "-R"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True
        )
        content = result.stdout
    except Exception:
        # Fallback to manual generation if subprocess fails (e.g. Windows without ls)
        content = ""
        for dir_path in base_dirs:
            content += f"{dir_path}:\n"
            # Add placeholder content indication if needed, but task asks for directory listing
            content += "\n"
        # Include root
        content = "Project Root:\n" + content

    with open(output_file, "w") as f:
        f.write(content)

    print(f"Project structure created successfully.")
    print(f"Deliverable artifact: {output_file}")
    print(f"Contents preview:\n{content[:200]}...")

    return 0

if __name__ == "__main__":
    sys.exit(main())

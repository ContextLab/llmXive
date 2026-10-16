import os
from pathlib import Path
from llmxive_toolkit import paths

def create_structure():
    """
    Creates the required top-level directory layout for the project.
    Re-scoped to avoid writing to platform-owned 'state/' directory.
    """
    # Defined directory layout
    dirs = [
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
    ]

    # Ensure the root project folders exist
    # Note: paths.data/code/ etc. from toolkit handle base directory creation
    for d in dirs:
        # Use Path to ensure creation of parents (e.g., code/ before code/simulation)
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
    
    # Also ensure the top-level project-owned directories exist explicitly
    Path("code").mkdir(exist_ok=True)
    Path("tests").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)

def generate_dir_list(root_path: Path, max_level: int = 2):
    """
    Simulates 'tree -L 2' to record the directory structure.
    """
    lines = []
    root_name = root_path.name if root_path.name else "."
    lines.append(f"{root_name}/")
    
    # We only care about the top level directories requested in the task
    # to verify the layout.
    try:
        # Get items in root
        items = sorted([item for item in root_path.iterdir() if item.is_dir()])
        for item in items:
            lines.append(f"├── {item.name}/")
            # Level 2
            sub_items = sorted([sub for sub in item.iterdir() if sub.is_dir()])
            for sub in sub_items:
                lines.append(f"│   └── {sub.name}/")
    except Exception as e:
        lines.append(f"Error scanning directories: {e}")
    
    return "\n".join(lines)

def main():
    # 1. Create the directories
    create_structure()
    
    # 2. Generate the directory structure list
    # We scan from the project root
    structure = generate_dir_list(Path("."))
    
    # 3. Write to a project-owned path (data/dir_structure.txt)
    # as state/ is platform-owned and forbidden for project artifacts.
    output_file = paths.data("dir_structure.txt")
    with open(output_file, "w") as f:
        f.write(structure)
    
    print(f"Directory structure successfully recorded to {output_file}")

if __name__ == "__main__":
    main()
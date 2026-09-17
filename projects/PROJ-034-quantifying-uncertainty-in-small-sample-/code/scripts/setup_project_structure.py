import os
import sys
from pathlib import Path
import subprocess
import json

# Define the directory and file structure based on plan.md requirements
STRUCTURE = [
    # Code modules
    "code/simulation",
    "code/models",
    "code/metrics",
    "code/validation",
    "code/plots",
    "code/scripts",
    
    # Data directories
    "data/raw",
    "data/simulated",
    "data/results",
    
    # Test directories
    "tests/unit",
    "tests/integration",
    
    # Docs
    "docs/paper"
]

def create_directories():
    """Create the entire directory tree defined in plan.md."""
    root = Path(os.getcwd())
    created_paths = []
    
    for path_str in STRUCTURE:
        full_path = root / path_str
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path.resolve()))
        
        # Create .gitkeep files in data directories to ensure they are tracked
        if path_str.startswith("data/"):
            gitkeep_path = full_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            created_paths.append(str(gitkeep_path.resolve()))
    
    return created_paths

def generate_tree_manifest(created_paths):
    """Generate a JSON manifest of all created absolute paths."""
    # Sort paths for deterministic output
    created_paths.sort()
    
    manifest = {
        "description": "Project directory structure manifest for PROJ-034",
        "created_paths": created_paths,
        "total_items": len(created_paths)
    }
    
    output_path = Path(os.getcwd()) / "tree_manifest.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return str(output_path.resolve())

def build_tree_python():
    """Build the tree structure using subprocess if available, else fallback."""
    try:
        # Try using the system 'tree' command
        result = subprocess.run(
            ["tree", "-a", "."],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: generate a simple text representation if 'tree' is not installed
        lines = ["."]
        for root, dirs, files in os.walk("."):
            # Skip hidden directories and venv
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv']
            
            level = root.replace(".", "").count(os.sep)
            indent = " " * 2 * level
            lines.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = " " * 2 * (level + 1)
            for file in files:
                if file != ".gitkeep":
                    lines.append(f"{sub_indent}{file}")
                else:
                    lines.append(f"{sub_indent}.gitkeep")
        return "\n".join(lines)

def main():
    """Main entry point for setting up the project structure."""
    print("Creating project directory structure...")
    created_paths = create_directories()
    print(f"Created {len(created_paths)} paths.")
    
    print("Generating tree manifest...")
    manifest_path = generate_tree_manifest(created_paths)
    print(f"Manifest saved to: {manifest_path}")
    
    # Also generate a human-readable tree output for verification
    tree_output = build_tree_python()
    tree_txt_path = Path(os.getcwd()) / "tree_manifest.txt"
    with open(tree_txt_path, 'w', encoding='utf-8') as f:
        f.write(tree_output)
    print(f"Tree output saved to: {tree_txt_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

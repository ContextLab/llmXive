import os
import sys
from pathlib import Path
import subprocess
import json

def create_directories():
    """Create the entire project directory structure."""
    root = Path(__file__).parent.parent.parent
    
    directories = [
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        "data/raw",
        "data/simulated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "docs/paper",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories
    data_dirs = ["data/raw", "data/simulated", "data/results"]
    for dir_path in data_dirs:
        full_path = root / dir_path / ".gitkeep"
        full_path.touch()
        print(f"Created .gitkeep in: {full_path.parent}")
    
    return created_count

def generate_tree_manifest(root: Path) -> str:
    """Generate tree output and save to tree_manifest.txt."""
    try:
        # Try to use tree command if available
        result = subprocess.run(
            ["tree", "-a", "--noreport"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Fallback: generate tree output manually
    lines = []
    lines.append(f"{root.name}/")
    
    def walk_tree(path: Path, prefix: str = "", is_last: bool = True):
        items = sorted([p for p in path.iterdir() if not p.name.startswith('__')], 
                     key=lambda x: x.name)
        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{item.name}")
            
            if item.is_dir():
                extension = "    " if is_last_item else "│   "
                walk_tree(item, prefix + extension, is_last_item)
    
    walk_tree(root)
    return "\n".join(lines)

def build_tree_python(root: Path) -> str:
    """Build a Python representation of the tree structure."""
    tree_data = {}
    
    def build_dir(path: Path):
        items = {}
        for item in sorted(path.iterdir()):
            if item.is_dir():
                items[item.name] = build_dir(item)
            elif item.name != ".gitkeep":
                items[item.name] = "file"
        return items
    
    tree_data[root.name] = build_dir(root)
    return json.dumps(tree_data, indent=2)

def main():
    """Main entry point for project structure setup."""
    root = Path(__file__).parent.parent.parent
    
    print("Creating project directory structure...")
    created = create_directories()
    print(f"Created {created} new directories.")
    
    print("\nGenerating tree manifest...")
    tree_output = generate_tree_manifest(root)
    
    manifest_path = root / "tree_manifest.txt"
    with open(manifest_path, "w") as f:
        f.write(tree_output)
    
    print(f"Tree manifest saved to: {manifest_path}")
    print("\nTree structure:")
    print(tree_output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

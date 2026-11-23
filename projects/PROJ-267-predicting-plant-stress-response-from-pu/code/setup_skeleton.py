import os
from pathlib import Path
from llmxive_toolkit import paths

def main():
    """
    Create the project directory skeleton and generate the structure listing.
    """
    # Define required directories
    target_dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.logs(),
        paths.docs(),
        paths.results(),
    ]
    
    for d in target_dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked
        (d / ".gitkeep").touch()

    # Generate the directory tree listing for docs/structure.txt
    root = paths.root
    structure = ["."]
    
    # Walk the directory to build a tree-like list
    # We sort to ensure deterministic output
    for path in sorted(root.rglob('*')):
        # Skip hidden directories and files (like .git, .runtime-home)
        if any(part.startswith('.') for part in path.relative_to(root).parts):
            continue
        
        depth = len(path.relative_to(root).parts)
        indent = '  ' * (depth - 1)
        
        if path.is_dir():
            structure.append(f"{indent}├── {path.name}/")
        else:
            # Avoid including the structure.txt itself in the listing if possible
            if path.name == "structure.txt":
                continue
            structure.append(f"{indent}└── {path.name}")
    
    output_path = paths.docs("structure.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(structure))
    
    print(f"Project skeleton created. Structure written to {output_path}")

if __name__ == "__main__":
    main()

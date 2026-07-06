import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def create_directories(base_path: Path) -> None:
    """Create the required directory structure for the project."""
    dirs = [
        base_path / "src",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "logs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

def create_placeholder_files(base_path: Path) -> None:
    """Create empty placeholder files required for the project."""
    files = [
        base_path / "src" / "__init__.py",
        base_path / "tests" / "__init__.py",
        base_path / "requirements.txt",
    ]
    for f in files:
        f.touch()
        print(f"Created placeholder file: {f}")

def run_tree_command(base_path: Path, output_path: Path) -> None:
    """Run the 'tree' command to verify directory structure and save output."""
    try:
        # Try to run the system 'tree' command
        result = subprocess.run(
            ["tree", str(base_path)],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: generate a manual tree representation if 'tree' is not available
        output = generate_manual_tree(base_path)
    
    # Ensure logs directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output to file
    with open(output_path, "w") as f:
        f.write(f"# Directory Tree generated at {datetime.now().isoformat()}\n\n")
        f.write(output)
    
    print(f"Tree output saved to: {output_path}")

def generate_manual_tree(base_path: Path, prefix: str = "", is_last: bool = True) -> str:
    """Generate a manual tree-like string representation of the directory structure."""
    lines = []
    connector = "└── " if is_last else "├── "
    lines.append(prefix + connector + base_path.name)
    
    new_prefix = prefix + ("    " if is_last else "│   ")
    
    try:
        items = sorted(base_path.iterdir())
    except PermissionError:
        return "\n".join(lines)
    
    # Filter out hidden files/dirs and specific unwanted items
    items = [item for item in items if not item.name.startswith('.')]
    
    for i, item in enumerate(items):
        is_last_item = (i == len(items) - 1)
        if item.is_dir():
            lines.append(generate_manual_tree(item, new_prefix, is_last_item))
        else:
            lines.append(new_prefix + ("└── " if is_last_item else "├── ") + item.name)
    
    return "\n".join(lines)

def main() -> None:
    """Main entry point for project setup."""
    # Determine the project root based on the script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # code/scripts -> code -> project_root
    
    # The task specifies the path relative to the project root
    target_path = project_root / "projects" / "PROJ-329-quantifying-the-impact-of-data-quantizat" / "code"
    
    print(f"Setting up project structure at: {target_path}")
    
    # Create directories
    create_directories(target_path)
    
    # Create placeholder files
    create_placeholder_files(target_path)
    
    # Run tree command and save output
    logs_dir = target_path.parent / "logs"  # logs should be at project level or code level? 
    # Task says: saving output to `logs/setup_tree.txt`. Assuming relative to project root or code root.
    # Let's place it relative to the code directory created to keep it self-contained if needed, 
    # but usually logs are at root. The task says "saving output to logs/setup_tree.txt".
    # Let's create it inside the code directory's parent (the project specific folder) or just code/logs.
    # Given the task: `projects/.../code/` ... saving to `logs/setup_tree.txt`. 
    # It likely implies `projects/.../code/logs/setup_tree.txt`.
    output_file = target_path / "logs" / "setup_tree.txt"
    
    run_tree_command(target_path, output_file)
    
    print("Setup complete.")

if __name__ == "__main__":
    main()

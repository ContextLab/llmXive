import subprocess
from pathlib import Path
from llmxive_toolkit import paths

def main():
    """
    Establishes the project layout by creating all required directories
    and capturing the filesystem structure as evidence.
    """
    # Required directories as per T001 specification
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/validation",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "output",
        "logs",
    ]

    # Create directories relative to project root
    for d in required_dirs:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
    
    # Ensure we are using the toolkit's pathing for key areas to be safe
    paths.data("raw")
    paths.data("processed")
    paths.logs("")
    
    # Capture the directory structure for verification
    # Prefer 'tree -a -L 3', fallback to 'find'
    try:
        result = subprocess.run(
            ['tree', '-a', '-L', '3'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        structure_output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to find if tree is not installed
        result = subprocess.run(
            ['find', '.', '-maxdepth', '3', '-type', 'd'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        structure_output = result.stdout

    # Write the evidence artifact
    structure_file = Path("logs/structure.txt")
    structure_file.write_text(structure_output, encoding="utf-8")

if __name__ == "__main__":
    main()

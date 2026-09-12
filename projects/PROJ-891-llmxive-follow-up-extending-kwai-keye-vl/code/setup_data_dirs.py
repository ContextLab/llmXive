import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the llmXive project.
    Directories created:
      - data/raw
      - data/distorted
      - data/outputs
      - data/metadata
    """
    project_root = Path(__file__).resolve().parent.parent
    base_dir = project_root / "data"

    directories = [
        "raw",
        "distorted",
        "outputs",
        "metadata"
    ]

    created = []
    for subdir in directories:
        target = base_dir / subdir
        target.mkdir(parents=True, exist_ok=True)
        created.append(str(target))
        print(f"Created directory: {target}")

    # Create a .gitkeep in each to ensure they are tracked if empty
    for subdir in directories:
        target = base_dir / subdir / ".gitkeep"
        target.write_text("")

    print(f"Data directory structure ready under {base_dir}")
    return created

if __name__ == "__main__":
    main()
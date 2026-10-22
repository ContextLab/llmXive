import os
from pathlib import Path

def main():
    # Required directories per T001 and project plan
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "code/utils",
        "code/tests",
        "results/paper_figures",
    ]

    print("Creating project scaffolding...")
    for dir_path in directories:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked/persist in environments
        (p / ".gitkeep").touch()
        print(f"Created: {dir_path}")

    print("Scaffolding complete.")

if __name__ == "__main__":
    main()

import os
import sys

def main():
    """Create data directories and .gitkeep files."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_root = os.path.join(base_dir, "data")

    dirs = [
        os.path.join(data_root, "raw"),
        os.path.join(data_root, "processed"),
        os.path.join(data_root, "explainability"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
        gitkeep = os.path.join(d, ".gitkeep")
        if not os.path.exists(gitkeep):
            with open(gitkeep, "w") as f:
                f.write("")
            print(f"Created: {gitkeep}")
        else:
            print(f"Exists: {gitkeep}")

    # Verify
    for d in dirs:
        gitkeep = os.path.join(d, ".gitkeep")
        if not os.path.exists(gitkeep):
            print(f"ERROR: Missing {gitkeep}")
            sys.exit(1)

    print("All data directories and .gitkeep files verified.")

if __name__ == "__main__":
    main()
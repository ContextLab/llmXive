import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    
    Directories created:
    - data/raw: For original unmodified source data
    - data/distorted: For generated extreme-aspect ratio videos
    - data/outputs: For analysis results and logs
    - data/metadata: For CSV/JSON metadata linking clips
    - output/control: For square-cropped control group videos
    """
    base_dirs = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata",
        "output/control"
    ]

    created_count = 0
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
"""Create the required project directory structure (Task T001a).

Creates the directories mandated by tasks.md Phase 1:
data/raw, data/processed, data/results, code, tests/unit,
tests/integration, config

After creation it writes a manifest file (data/results/directory_manifest.json)
listing each directory and whether it exists, providing concrete evidence
that the structure was created.
"""
import json
import os
import sys

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "code",
    "tests/unit",
    "tests/integration",
    "config",
]

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    created = []
    for rel in REQUIRED_DIRS:
        path = os.path.join(project_root, rel)
        os.makedirs(path, exist_ok=True)
        created.append(rel)
        print(f"Ensured directory exists: {rel}")

    manifest_path = os.path.join(project_root, "data", "results", "directory_manifest.json")
    manifest = {
        "task_id": "T001a",
        "required_directories": REQUIRED_DIRS,
        "verification": {
            rel: os.path.isdir(os.path.join(project_root, rel)) for rel in REQUIRED_DIRS
        },
        "all_directories_exist": all(
            os.path.isdir(os.path.join(project_root, rel)) for rel in REQUIRED_DIRS
        ),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote directory manifest to {manifest_path}")

    if not manifest["all_directories_exist"]:
        print("ERROR: some required directories are missing", file=sys.stderr)
        sys.exit(1)
    print("All required directories verified.")

if __name__ == "__main__":
    main()
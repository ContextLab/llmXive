"""T004: Create the project data directory structure.

Creates data/raw, data/processed, outputs, and figures under the project
root, then writes a verification record to outputs/directory_structure.json
so the setup is auditable.
"""
import json
from llmxive_toolkit import paths

REQUIRED_DIRS = ["data/raw", "data/processed", "outputs", "figures"]

def ensure_directories() -> dict:
    created = []
    existing = []
    for rel in REQUIRED_DIRS:
        d = paths.path(rel)
        if d.exists():
            existing.append(rel)
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    record = {
        "required_dirs": REQUIRED_DIRS,
        "created": created,
        "already_existing": existing,
        "all_exist": all(paths.path(rel).is_dir() for rel in REQUIRED_DIRS),
    }
    out = paths.path("outputs/directory_structure.json")
    with open(out, "w") as f:
        json.dump(record, f, indent=2)
    return record

def main() -> None:
    record = ensure_directories()
    status = "OK" if record["all_exist"] else "FAILED"
    print(f"Directory setup {status}: {record}")
    if not record["all_exist"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
import json
import os
import sys
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-881-llmxive-follow-up-extending-efficientrol")
    
    required_paths = [
        "code",
        "tests",
        "data",
        "docs",
        "scripts",
        "results",
        "specs/001-entropy-validity-prediction/contracts",
        "code/src",
        "code/data/raw",
        "code/data/processed",
        "code/artifacts",
        "code/state",
        "code/logs",
        "code/contracts",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs/001-entropy-validity-prediction"
    ]

    results = []
    all_exist = True

    for path_str in required_paths:
        full_path = project_root / path_str
        exists = full_path.exists()
        results.append({"path": str(full_path.absolute()), "exists": exists})
        if not exists:
            all_exist = False
            print(f"MISSING: {full_path}")
        else:
            print(f"OK: {full_path}")

    log_path = project_root / "project_structure.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        json.dump({"paths": results}, f, indent=2)

    if not all_exist:
        print(f"Verification failed. Log written to {log_path}")
        sys.exit(1)
    else:
        print(f"Verification successful. Log written to {log_path}")
        sys.exit(0)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Verifies that all required project directories exist.
Generates a JSON log file with existence status.
"""
import json
import os
import sys
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-881-llmxive-follow-up-extending-efficientrol")
    code_dir = project_root / "code"
    
    required_paths = [
        code_dir,
        code_dir / "tests",
        code_dir / "data",
        code_dir / "docs",
        code_dir / "scripts",
        code_dir / "results",
        Path("specs") / "001-entropy-validity-prediction" / "contracts",
        code_dir / "src",
        code_dir / "data" / "raw",
        code_dir / "data" / "processed",
        code_dir / "artifacts",
        code_dir / "state",
        code_dir / "logs",
        code_dir / "src" / "utils",
        code_dir / "src" / "data",
        code_dir / "src" / "generation",
        code_dir / "src" / "analysis",
    ]
    
    results = []
    all_exist = True
    
    for path in required_paths:
        exists = path.exists()
        results.append({
            "path": str(path.absolute()),
            "exists": exists
        })
        if not exists:
            all_exist = False
            print(f"Missing: {path}")
    
    # Write log file
    log_file = code_dir / "project_structure.log"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({"paths": results}, f, indent=2)
    
    print(f"Log written to {log_file}")
    
    if not all_exist:
        print("Error: Some directories are missing.")
        sys.exit(1)
    else:
        print("All directories exist.")
        sys.exit(0)

if __name__ == "__main__":
    main()

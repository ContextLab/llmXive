import os
import json
from datetime import datetime
from pathlib import Path

def ensure_directories():
    """Create the required project directory structure."""
    project_root = Path(__file__).parent.parent
    base_dirs = [
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "final",
        project_root / "data" / "logs",
        project_root / "tests",
        project_root / "docs",
        project_root / "specs" / "001-statistical-analysis-of-recipe-data" / "contracts",
    ]
    created = []
    for d in base_dirs:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d.relative_to(project_root)))
    return created

def verify_directories(paths):
    """Verify that the specified directories exist."""
    project_root = Path(__file__).parent.parent
    verified = []
    for p in paths:
        full_path = project_root / p
        if full_path.exists() and full_path.is_dir():
            verified.append(p)
        else:
            verified.append(None)
    return all(v is not None for v in verified), [v for v in verified if v is not None]

def log_setup_status(output_path, status, paths_verified):
    """Write the setup log to a JSON file."""
    log_entry = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paths_verified": paths_verified
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)

def main():
    """Main entry point for directory setup and verification."""
    project_root = Path(__file__).parent.parent
    output_file = project_root / "data" / "setup_log.json"
    
    try:
        created_dirs = ensure_directories()
        # Verify the core paths required by T001a
        core_paths = [
            "code",
            "data",
            "tests"
        ]
        success, verified = verify_directories(core_paths)
        
        if success:
            log_setup_status(output_file, "SUCCESS", verified)
            print(f"Setup successful. Log written to {output_file}")
        else:
            log_setup_status(output_file, "FAILED", verified)
            print(f"Setup failed. Missing directories.")
            return 1
    except Exception as e:
        log_setup_status(output_file, "FAILED", [])
        print(f"Setup failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

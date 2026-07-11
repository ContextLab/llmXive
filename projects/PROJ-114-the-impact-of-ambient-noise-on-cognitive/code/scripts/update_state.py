"""
Update project state by computing SHA-256 hashes of artifacts.

This script scans the project directories (code/, data/, tests/, docs/, figures/)
for relevant files, computes their SHA-256 hashes, and updates the
state/projects/PROJ-114-.../current_stage.yaml file.
"""
import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_ID = "PROJ-114-the-impact-of-ambient-noise-on-cognitive"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / PROJECT_ID
ARTIFACT_DIRS = ["code", "data", "tests", "docs", "figures", "contracts", "specs"]

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_artifacts(base_dir: Path, artifact_dirs: List[str]) -> List[Dict[str, str]]:
    """Scan directories for artifacts and compute hashes."""
    artifacts = []
    extensions = {".py", ".yaml", ".yml", ".json", ".csv", ".md", ".txt", ".png", ".jpg", ".svg"}

    for dir_name in artifact_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            continue

        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and (file_path.suffix in extensions or file_path.name.endswith(".py")):
                try:
                  rel_path = file_path.relative_to(base_dir)
                  file_hash = compute_file_hash(file_path)
                  artifacts.append({
                      "path": str(rel_path),
                      "hash": file_hash,
                      "size_bytes": file_path.stat().st_size,
                      "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                  })
                except Exception:
                    continue
    
    return sorted(artifacts, key=lambda x: x["path"])

def update_state_file(state_dir: Path, artifacts: List[Dict[str, str]], project_id: str) -> None:
    """Update or create the current_stage.yaml file."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "current_stage.yaml"

    current_stage = {
        "project_id": project_id,
        "last_updated": datetime.now().isoformat(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts
    }

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(current_stage, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for updating project state."""
    print(f"Scanning artifacts for project: {PROJECT_ID}")
    
    artifacts = scan_artifacts(PROJECT_ROOT, ARTIFACT_DIRS)
    
    if not artifacts:
        print("Warning: No artifacts found to hash.")
    
    update_state_file(STATE_DIR, artifacts, PROJECT_ID)
    
    print(f"State updated successfully. Found {len(artifacts)} artifacts.")
    print(f"Output written to: {STATE_DIR / 'current_stage.yaml'}")

if __name__ == "__main__":
    main()
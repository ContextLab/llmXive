import os
from pathlib import Path
import yaml
from datetime import datetime

def create_state_structure(base_path: str):
    """
    Create the state directory structure and the initial project state file.
    """
    state_dir = Path(base_path) / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)

    project_id = "PROJ-122-identifying-structure-property-relations"
    state_file = state_dir / f"{project_id}.yaml"

    if not state_file.exists():
        initial_state = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "artifacts": {},
            "checksums": {},
            "dependencies": {
                "python_version": ">=3.11",
                "packages": [
                    "pandas==2.2.3",
                    "rdkit==2024.3.5",
                    "scikit-learn==1.5.2",
                    "xgboost==2.1.1",
                    "shap==0.46.0",
                    "pyyaml==6.0.2",
                    "requests==2.32.3",
                    "joblib==1.4.2",
                    "psutil==6.0.0"
                ]
            }
        }
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f, default_flow_style=False)

if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    create_state_structure(base)

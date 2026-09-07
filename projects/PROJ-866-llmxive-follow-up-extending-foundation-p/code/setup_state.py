import os
import sys
from pathlib import Path
import yaml
from datetime import datetime


def create_state_directory() -> None:
    """Create the state directory."""
    os.makedirs("state", exist_ok=True)
    os.makedirs("state/projects", exist_ok=True)


def create_initial_project_state(project_id: str) -> None:
    """Create an initial project state file.

    Args:
        project_id: The project identifier.
    """
    state = {
        "project_id": project_id,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "artifact_hashes": {},
        "status": "initialized",
    }

    filepath = f"state/projects/{project_id}.yaml"
    with open(filepath, "w") as f:
        yaml.dump(state, f, default_flow_style=False)
    print(f"Created state file: {filepath}")


def main() -> None:
    """Main entry point for state setup."""
    import argparse

    parser = argparse.ArgumentParser(description="State Setup")
    parser.add_argument("--project", type=str, default="PROJ-866-llmxive-follow-up-extending-foundation-p",
                      help="Project ID")

    args = parser.parse_args()

    create_state_directory()
    create_initial_project_state(args.project)


if __name__ == "__main__":
    main()

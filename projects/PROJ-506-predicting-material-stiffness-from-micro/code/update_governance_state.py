import sys
from pathlib import Path
from code.utils.state_manager import update_project_state

def main():
    """
    Executes the state update for T003: Governance Change Recording.
    
    This script updates the project state YAML to reflect the completion
    of the constitution amendment (T001, T002).
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    state_dir = project_root / "state"
    project_id = "PROJ-506-predicting-material-stiffness-from-micro"
    
    # Artifacts updated in this governance phase
    artifacts = [
        project_root / "docs" / "constitution_amendment_proposal.md",
        project_root / "constitution.md"
    ]
    
    description = "Governance update: Approved FFT-based homogenization (Principle VI). Updated constitution and proposal docs."
    
    try:
        update_project_state(project_id, state_dir, artifacts, description)
        print(f"Successfully updated state for {project_id}")
        return 0
    except Exception as e:
        print(f"Error updating state: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())

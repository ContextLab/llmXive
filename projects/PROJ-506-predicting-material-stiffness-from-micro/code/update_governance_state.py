"""
Updates the project state file to record governance verification completion.
This script updates the artifact_hashes and updated_at fields in the state file.
"""
import sys
from pathlib import Path
from code.utils.state_manager import update_project_state

def main():
    """
    Main entry point for updating governance state.
    Updates the state file for PROJ-506-predicting-material-stiffness-from-micro
    to record that governance verification (T002v, T004v, T005v) is complete.
    """
    project_id = "PROJ-506-predicting-material-stiffness-from-micro"
    task_id = "T002d"
    
    # The state file path relative to project root
    state_file_path = Path("state/projects") / f"{project_id}.yaml"
    
    # Check if state file exists
    if not state_file_path.exists():
        print(f"Error: State file not found at {state_file_path}")
        print("Please ensure the project state file exists before running this update.")
        sys.exit(1)
    
    # Update the state file with governance verification info
    # We update artifact_hashes to include the verified tasks and updated_at to current time
    update_project_state(
        state_file_path=state_file_path,
        project_id=project_id,
        completed_tasks=["T002v", "T004v", "T005v"],
        current_task=task_id,
        status="completed",
        notes="Governance verification complete: Constitution Principle VI, Spec Resolution (128x128), and Spec/Plan Alignment (ANOVA) verified."
    )
    
    print(f"Successfully updated governance state for {project_id}")
    print(f"Verified tasks: T002v, T004v, T005v")
    print(f"Current task {task_id} marked as completed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

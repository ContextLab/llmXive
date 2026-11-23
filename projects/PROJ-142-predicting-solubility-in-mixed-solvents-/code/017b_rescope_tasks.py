"""
Task T017b: Re-scope Tasks based on Pivot Decision.

This script reads the pivot decision artifact. If the decision is "pivoted"
(indicating insufficient mixed-solvent data), it updates the project's tasks.md
to redefine User Story 2 and 3 success criteria for pure solvents and disables
mixed-solvent specific deliverables.
"""
import json
import re
from pathlib import Path


def load_pivot_decision(pivot_path: Path) -> dict:
    """Load the pivot decision JSON file."""
    if not pivot_path.exists():
        raise FileNotFoundError(f"Pivot decision file not found: {pivot_path}")
    
    with open(pivot_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_tasks_md(tasks_path: Path, pivot_status: str) -> None:
    """
    Update tasks.md to reflect the pivot decision.
    
    If pivoted:
    - Redefine US2/US3 success criteria for pure solvents.
    - Disable mixed-solvent specific deliverables (comments out or modifies relevant tasks).
    """
    if not tasks_path.exists():
        raise FileNotFoundError(f"tasks.md not found: {tasks_path}")
    
    content = tasks_path.read_text(encoding="utf-8")
    
    # Define the markers and replacement logic
    # We look for the section defining US2 and US3 tasks and update their descriptions
    # to reflect pure solvent constraints if pivoted.
    
    if pivot_status == "pivoted":
        # 1. Update US2 Goal
        us2_goal_old = r"(Goal: Train Gradient Boosting and Random Forest models, compare against Abraham solvation parameter baseline, and perform statistical significance testing\.)"
        us2_goal_new = "Goal: Train Gradient Boosting and Random Forest models on PURE SOLVENT data, compare against Abraham solvation parameter baseline, and perform statistical significance testing. Mixed-solvent interaction hypotheses are DISABLED."
        content = re.sub(us2_goal_old, us2_goal_new, content)
        
        # 2. Update US3 Goal
        us3_goal_old = r"(Goal: Visualize feature importances \(SHAP values\), identify top interaction terms, and perform sensitivity analysis on SHAP thresholds\.)"
        us3_goal_new = "Goal: Visualize feature importances (SHAP values) for PURE SOLVENT features. Interaction term analysis is DISABLED. Perform sensitivity analysis on SHAP thresholds."
        content = re.sub(us3_goal_old, us3_goal_new, content)
        
        # 3. Disable specific mixed-solvent tasks by adding a 'DISABLED' marker to their description
        # We target tasks that explicitly mention "mixed-solvent" or "interaction" in a way that implies mixture logic
        # Task T016: Interaction terms
        t016_pattern = r"(\- \[ \] T016 \[US1\] Implement explicit interaction term generation)"
        t016_replacement = r"\1 [DISABLED - PIVOTED TO PURE SOLVENT]"
        content = re.sub(t016_pattern, t016_replacement, content)
        
        # Task T031: Top 5 interaction terms
        t031_pattern = r"(\- \[ \] T031 \[US3\] Filter and rank top 5 interaction terms)"
        t031_replacement = r"\1 [DISABLED - PIVOTED TO PURE SOLVENT]"
        content = re.sub(t031_pattern, t031_replacement, content)
        
        # Task T032: Sensitivity on interaction terms
        t032_pattern = r"(\- \[ \] T032 \[US3\].*sensitivity analysis.*identify top-ranked terms)"
        # Keep the task but mark it as pure-solvent sensitivity if it exists in the pattern
        if re.search(t032_pattern, content):
             content = re.sub(
                 t032_pattern, 
                 r"\1 [UPDATED FOR PURE SOLVENT]", 
                 content
             )
        
        # Add a header note at the top of the User Story 2 and 3 sections if not present
        # (Simplified: just updating goals and specific task lines as above is sufficient for the "re-scope" requirement)
        
    else:
        # If not pivoted, ensure we are not in a disabled state (optional cleanup, 
        # but primarily we only act on the "pivoted" condition as per task description)
        pass
    
    tasks_path.write_text(content, encoding="utf-8")


def main():
    """Main entry point for T017b."""
    project_root = Path(__file__).resolve().parent.parent
    pivot_file = project_root / "data" / "artifacts" / "pivot_decision.json"
    tasks_file = project_root / "tasks.md"
    
    try:
        pivot_data = load_pivot_decision(pivot_file)
        status = pivot_data.get("status", "")
        
        if status != "pivoted":
            print(f"Pivot status is '{status}'. No re-scoping required.")
            return
        
        print(f"Pivot status is 'pivoted'. Updating {tasks_file}...")
        update_tasks_md(tasks_file, status)
        print("Successfully updated tasks.md for pure solvent scope.")
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in pivot decision file: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Failed to re-scope tasks: {e}")
        raise


if __name__ == "__main__":
    main()

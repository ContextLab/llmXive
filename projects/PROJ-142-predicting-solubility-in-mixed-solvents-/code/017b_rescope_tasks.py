"""
T017b: Re-scope Tasks based on Pivot Decision.

Reads data/artifacts/pivot_decision.json.
If status is "pivoted":
  1. Updates tasks.md to redefine US2/US3 success criteria for pure solvents.
  2. Disables mixed-solvent specific deliverables in the text.
  3. Writes a confirmation log to data/artifacts/rescope_log.txt.
If status is "normal", does nothing and exits successfully.
"""
import json
import re
from pathlib import Path

# Project paths relative to root
PIVOT_FILE = Path("data/artifacts/pivot_decision.json")
TASKS_FILE = Path("tasks.md")
LOG_FILE = Path("data/artifacts/rescope_log.txt")

def main():
    if not PIVOT_FILE.exists():
        print(f"Warning: {PIVOT_FILE} not found. No rescope needed.")
        return

    with open(PIVOT_FILE, "r", encoding="utf-8") as f:
        pivot_data = json.load(f)

    status = pivot_data.get("status", "normal")
    
    if status != "pivoted":
        print("Pivot status is not 'pivoted'. No rescope required.")
        return

    print("Pivot detected. Updating tasks.md for pure solvent scope...")

    if not TASKS_FILE.exists():
        raise FileNotFoundError(f"Tasks file {TASKS_FILE} not found.")

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    changes_made = []

    # 1. Update Phase 4 (US2) description
    # Look for the specific block in Phase 4
    us2_pattern = r"(## Phase 4: User Story 2 - Model Training and Baseline Comparison \(Priority: P2\)\n\n**Goal**: )([^*]+)(\*\*)"
    
    def replace_us2_goal(match):
        prefix = match.group(1)
        old_goal = match.group(2)
        suffix = match.group(3)
        new_goal = "Train Gradient Boosting and Random Forest models for PURE SOLVENTS (mixed-solvent hypothesis disabled), compare against Abraham solvation parameter baseline, and perform statistical significance testing."
        if old_goal != new_goal:
            changes_made.append("Updated US2 Goal to Pure Solvents")
        return prefix + new_goal + suffix

    content = re.sub(us2_pattern, replace_us2_goal, content)

    # 2. Update Phase 5 (US3) description
    us3_pattern = r"(## Phase 5: User Story 3 - Interpretability and Interaction Term Analysis \(Priority: P3\)\n\n**Goal**: )([^*]+)(\*\*)"
    
    def replace_us3_goal(match):
        prefix = match.group(1)
        old_goal = match.group(2)
        suffix = match.group(3)
        new_goal = "Visualize feature importances (SHAP values) for pure solvent descriptors, identify top molecular descriptors, and perform sensitivity analysis on SHAP thresholds. Mixed-solvent interaction term analysis is DISABLED."
        if old_goal != new_goal:
            changes_made.append("Updated US3 Goal to Pure Solvents")
        return prefix + new_goal + suffix

    content = re.sub(us3_pattern, replace_us3_goal, content)

    # 3. Disable specific mixed-solvent deliverables in US2
    # Target T022: "Implement Abraham solvation parameter model baseline..."
    # We append a note to the task description or modify the fallback logic description
    t022_pattern = r"(- \[ \] T022 \[US2\] Implement Abraham solvation parameter model baseline in `code/03_model_training.py`:)"
    
    def disable_mixed_solvent_notes(match):
        line = match.group(0)
        # Check if we already added the note
        if "DISABLED: Mixed-solvent" in line:
            return line
        
        # Find the end of the line or the next bullet
        # Simple approach: append a comment to the line
        note = "  <!-- DISABLED: Mixed-solvent specific baseline logic removed per Pivot -->"
        changes_made.append("Disabled Mixed-Solvent Baseline Logic in T022")
        return line + "\n" + note

    content = re.sub(t022_pattern, disable_mixed_solvent_notes, content)

    # 4. Disable specific mixed-solvent deliverables in US3 (Interaction Terms)
    # Target T031: "Filter and rank top 5 interaction terms..."
    t031_pattern = r"(- \[ \] T031 \[US3\] Filter and rank top 5 interaction terms contributing to model variance; append to `data/artifacts/shap_ranking.json`)"
    
    def disable_interaction_terms(match):
        line = match.group(0)
        if "DISABLED: Interaction Terms" in line:
            return line
        
        # Modify the task to indicate it's now about main descriptors
        new_line = "- [ ] T031 [US3] **DISABLED**: Filter and rank top 5 interaction terms (Pure Solvent Pivot). Skip this step for pure solvent model."
        changes_made.append("Disabled Interaction Term Ranking in T031")
        return new_line

    content = re.sub(t031_pattern, disable_interaction_terms, content)

    # Write back if changes were made
    if content != original_content:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {TASKS_FILE}")
        
        # Write log
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"Rescope completed at pivot status: {status}\n")
            f.write("Changes made:\n")
            for change in changes_made:
                f.write(f"- {change}\n")
        print(f"Log written to {LOG_FILE}")
    else:
        print("No changes required in tasks.md (already updated or pattern mismatch).")

if __name__ == "__main__":
    main()
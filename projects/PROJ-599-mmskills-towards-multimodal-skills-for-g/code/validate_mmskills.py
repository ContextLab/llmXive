import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import pandas as pd

# Constants
SKILLS_DIR = Path("external/mmskills/skills_library")
OUTPUT_DIR = Path("data")
FIGURES_DIR = Path("figures")

# Ensure output directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# Required files for a valid MMSkill
REQUIRED_FILES = [
    "SKILL.md",
    "plan.json",
    "state_cards.json",
    "runtime_state_cards.json",
    "grounding_audit.json" # Optional but common
]

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Safely load a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        return {"error": str(e)}

def analyze_skill(skill_path: Path) -> Dict[str, Any]:
    """
    Analyze a single skill directory for MMSkills compliance.
    Returns a dictionary of metrics for this skill.
    """
    skill_name = skill_path.name
    results = {
        "skill_name": skill_name,
        "valid_structure": True,
        "missing_files": [],
        "plan_steps": 0,
        "state_cards_count": 0,
        "runtime_state_count": 0,
        "images_missing": [],
        "images_found": 0,
        "total_images": 0,
        "grounding_audit_valid": False,
        "status": "PASS"
    }

    # 1. Check Required Files
    for req_file in REQUIRED_FILES:
        if not (skill_path / req_file).exists():
            results["valid_structure"] = False
            results["missing_files"].append(req_file)
            results["status"] = "FAIL_STRUCTURE"

    # 2. Load and Analyze Plan
    plan_path = skill_path / "plan.json"
    if plan_path.exists():
        plan = load_json_file(plan_path)
        if "error" not in plan and isinstance(plan, list):
            results["plan_steps"] = len(plan)
        elif isinstance(plan, dict) and "steps" in plan:
            results["plan_steps"] = len(plan["steps"])
    else:
        results["plan_steps"] = 0

    # 3. Load and Analyze State Cards
    state_path = skill_path / "state_cards.json"
    if state_path.exists():
        states = load_json_file(state_path)
        if "error" not in states and isinstance(states, list):
            results["state_cards_count"] = len(states)
        elif isinstance(states, dict) and "cards" in states:
            results["state_cards_count"] = len(states["cards"])

    # 4. Load and Analyze Runtime State Cards
    runtime_path = skill_path / "runtime_state_cards.json"
    if runtime_path.exists():
        runtime_states = load_json_file(runtime_path)
        if "error" not in runtime_states and isinstance(runtime_states, list):
            results["runtime_state_count"] = len(runtime_states)
        elif isinstance(runtime_states, dict) and "cards" in runtime_states:
            results["runtime_state_count"] = len(runtime_states["cards"])

    # 5. Check Image References
    img_dir = skill_path / "Images"
    if img_dir.exists():
        image_files = list(img_dir.glob("*.*"))
        results["total_images"] = len(image_files)
        
        # Check if plan references images (heuristic: look for .png/.jpg in plan text)
        # This is a simplified check; real MMSkills might have explicit references.
        # We will just count if the Images folder is populated as expected.
        if results["total_images"] > 0:
            results["images_found"] = results["total_images"]
        else:
            # Check if SKILL.md or plan.json mentions images but none exist
            results["images_missing"] = ["No images found in Images/"]
    else:
        # Some skills might not have images if they are text-only, but MMSkills implies multimodal
        results["images_found"] = 0
        results["total_images"] = 0

    # 6. Grounding Audit Check
    audit_path = skill_path / "grounding_audit.json"
    if audit_path.exists():
        audit = load_json_file(audit_path)
        if "error" not in audit:
            results["grounding_audit_valid"] = True

    # Final Status Logic
    if results["valid_structure"] and results["plan_steps"] > 0:
        results["status"] = "PASS"
    elif not results["valid_structure"]:
        results["status"] = "FAIL_STRUCTURE"
    elif results["plan_steps"] == 0:
        results["status"] = "EMPTY_PLAN"
    else:
        results["status"] = "PARTIAL"

    return results

def main():
    print("MMSkills Structure Validator - CPU Adaptation")
    print(f"Scanning directory: {SKILLS_DIR}")
    
    if not SKILLS_DIR.exists():
        print(f"Error: Skills directory not found at {SKILLS_DIR}")
        # Create dummy data for CI if path is wrong, but ideally fail
        # For this adaptation, we assume the repo structure is correct relative to external/
        # If running locally, adjust path.
        sys.exit(1)

    skills = []
    total_skills = 0
    
    # Traverse skills_library
    for app_dir in SKILLS_DIR.iterdir():
        if app_dir.is_dir():
            for skill_dir in app_dir.iterdir():
                if skill_dir.is_dir():
                    total_skills += 1
                    metrics = analyze_skill(skill_dir)
                    skills.append(metrics)

    if total_skills == 0:
        print("No skills found. Creating empty report.")
        skills = [{"skill_name": "none", "status": "NO_DATA"}]

    # Convert to DataFrame for analysis
    df = pd.DataFrame(skills)

    # 1. Save detailed CSV
    csv_path = OUTPUT_DIR / "skill_validation_report.csv"
    df.to_csv(csv_path, index=False)
    print(f"Wrote detailed report to: {csv_path}")

    # 2. Save Summary JSON
    summary = {
        "total_skills_analyzed": total_skills,
        "skills_passed": int(df[df["status"] == "PASS"].shape[0]),
        "skills_failed_structure": int(df[df["status"] == "FAIL_STRUCTURE"].shape[0]),
        "skills_empty_plan": int(df[df["status"] == "EMPTY_PLAN"].shape[0]),
        "skills_partial": int(df[df["status"] == "PARTIAL"].shape[0]),
        "avg_plan_steps": float(df["plan_steps"].mean()) if not df.empty else 0.0,
        "avg_images_per_skill": float(df["total_images"].mean()) if not df.empty else 0.0
    }
    
    json_path = OUTPUT_DIR / "validation_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to: {json_path}")

    # 3. Generate Visualization
    plt.figure(figsize=(10, 6))
    
    # Status Distribution
    status_counts = df["status"].value_counts()
    # Reorder for clarity
    ordered_statuses = ["PASS", "FAIL_STRUCTURE", "PARTIAL", "EMPTY_PLAN", "NO_DATA"]
    status_counts = status_counts.reindex(ordered_statuses).fillna(0).astype(int)
    
    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#95a5a6', '#bdc3c7']
    plt.bar(status_counts.index, status_counts.values, color=colors)
    plt.title(f"MMSkills Library Integrity Check (N={total_skills})")
    plt.ylabel("Number of Skills")
    plt.xlabel("Validation Status")
    plt.tight_layout()
    
    fig_path = FIGURES_DIR / "skill_integrity_bar.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Wrote chart to: {fig_path}")

    # 4. Correlation: Plan Steps vs Images
    if not df.empty and df["total_images"].sum() > 0:
        plt.figure(figsize=(10, 6))
        plt.scatter(df["plan_steps"], df["total_images"], alpha=0.6)
        plt.title("Correlation: Plan Complexity vs Visual Grounding")
        plt.xlabel("Number of Plan Steps")
        plt.ylabel("Number of Reference Images")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        fig_path2 = FIGURES_DIR / "complexity_vs_images.png"
        plt.savefig(fig_path2)
        plt.close()
        print(f"Wrote chart to: {fig_path2}")

    print("\nValidation Complete.")
    print(f"Total Skills: {summary['total_skills_analyzed']}")
    print(f"Passed: {summary['skills_passed']}")
    print(f"Failed Structure: {summary['skills_failed_structure']}")
    
    return summary

if __name__ == "__main__":
    main()

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def get_project_root() -> Path:
    """Determine the project root directory (parent of the code/ directory)."""
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def get_plan_path(project_root: Path) -> Path:
    """Return the path to the plan.md file."""
    return project_root / "plan.md"

def check_plan_content(plan_path: Path) -> bool:
    """
    Check if plan.md contains 'Amendment 001' or 'Bayesian Hierarchical Model'.
    Returns True if found, False otherwise.
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"plan.md not found at {plan_path}")

    content = plan_path.read_text(encoding="utf-8")
    required_terms = ["Amendment 001", "Bayesian Hierarchical Model"]
    return any(term in content for term in required_terms)

def update_ratification_state(project_root: Path, status: str) -> None:
    """
    Write the ratification status to state/ratification.yaml as a JSON string.
    The task requires the format: {"status": "RATIFIED", "timestamp": "<now>"}
    """
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    ratification_path = state_dir / "ratification.yaml"

    timestamp = datetime.utcnow().isoformat() + "Z"
    data = {
        "status": status,
        "timestamp": timestamp
    }

    # Write as a raw JSON string to satisfy the requirement exactly
    with open(ratification_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data))

def main() -> None:
    """
    Main entry point for plan verification.
    Reads plan.md, checks for required text, and updates state/ratification.yaml.
    """
    project_root = get_project_root()
    plan_path = get_plan_path(project_root)

    try:
        is_ratified = check_plan_content(plan_path)
        if is_ratified:
            update_ratification_state(project_root, "RATIFIED")
            print("Plan successfully ratified. State updated in state/ratification.yaml")
            sys.exit(0)
        else:
            raise ValueError("Plan does not contain required amendment text ('Amendment 001' or 'Bayesian Hierarchical Model').")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
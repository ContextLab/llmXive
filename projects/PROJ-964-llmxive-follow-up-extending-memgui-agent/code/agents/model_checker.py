"""
Model Checker for MemGUI-Agent Project.

Performs static pre-verification of model availability against the Plan.md
"Verified datasets" block. If the primary model is not found, it dynamically
pivots to a hardcoded list of allowed substitutes without failing the build.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Tuple

# Hardcoded list of allowed substitute model IDs as per task specification
ALLOWED_SUBSTITUTES: List[str] = [
    'microsoft/Phi-3-mini-4k-instruct',
    'microsoft/Phi-3.5-mini-instruct'
]

PRIMARY_MODEL_ID: str = "MemGUI-8B-SFT"

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    # Assume code/ is at project root level based on task context
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def read_plan_md() -> Optional[str]:
    """
    Reads the content of Plan.md from the project root.
    Returns None if the file does not exist.
    """
    root = get_project_root()
    plan_path = root / "Plan.md"
    if not plan_path.exists():
        # Fallback to common variations if Plan.md is named differently
        alt_paths = [root / "plan.md", root / "docs" / "Plan.md", root / "docs" / "plan.md"]
        for p in alt_paths:
            if p.exists():
                return p.read_text(encoding='utf-8')
        return None
    return plan_path.read_text(encoding='utf-8')

def extract_verified_datasets_block(plan_content: str) -> str:
    """
    Extracts the 'Verified datasets' block from Plan.md content.
    Heuristic: Looks for a section header containing 'Verified datasets'
    and captures the text until the next major header or end of file.
    """
    # Case-insensitive search for the header
    pattern = r"(?i)Verified datasets.*?(?=\n#{1,3}\s|\Z)"
    match = re.search(pattern, plan_content, re.DOTALL)
    if match:
        return match.group(0)
    return ""

def check_model_in_block(block_content: str, model_id: str) -> bool:
    """
    Checks if a specific model_id exists in the provided text block.
    """
    return model_id in block_content

def verify_model() -> Tuple[bool, str, str]:
    """
    Main verification logic.

    Returns:
        Tuple[success, selected_model_id, message]
        - success: True if a valid model is selected (primary or substitute).
        - selected_model_id: The model ID chosen for use.
        - message: A human-readable explanation of the decision.
    """
    plan_content = read_plan_md()

    if plan_content is None:
        # If Plan.md is missing, we cannot verify the primary, so we pivot to substitute
        # to "do NOT fail the build" as per instructions.
        selected = ALLOWED_SUBSTITUTES[0]
        return (
            True,
            selected,
            "Plan.md not found. Pivoting to default substitute: " + selected
        )

    verified_block = extract_verified_datasets_block(plan_content)

    if not verified_block:
        # "Verified datasets" section not found in Plan.md
        selected = ALLOWED_SUBSTITUTES[0]
        return (
            True,
            selected,
            "'Verified datasets' block not found in Plan.md. Pivoting to default substitute: " + selected
        )

    if check_model_in_block(verified_block, PRIMARY_MODEL_ID):
        return (
            True,
            PRIMARY_MODEL_ID,
            f"Primary model '{PRIMARY_MODEL_ID}' found in 'Verified datasets' block."
        )

    # Primary not found, pivot to the first available substitute
    selected = ALLOWED_SUBSTITUTES[0]
    return (
        True,
        selected,
        f"Primary model '{PRIMARY_MODEL_ID}' NOT found in 'Verified datasets'. Pivoting to substitute: {selected}"
    )

def main():
    """Entry point for the model checker script."""
    print("Running Model Verification Check...")
    success, model_id, message = verify_model()

    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    print(f"Selected Model: {model_id}")
    print(f"Reasoning: {message}")

    # Exit with 0 regardless of pivot, as per "do NOT fail the build"
    # The build fails only if NO valid model could be selected (which shouldn't happen here)
    return 0

if __name__ == "__main__":
    exit(main())

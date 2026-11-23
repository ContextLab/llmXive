"""
Module to verify and update the status of plan.md regarding Constitution Amendment compliance.
Specifically checks for the BHM (Bayesian Hierarchical Model) methodology and updates status to 'RATIFIED'.
"""
import os
import re
from pathlib import Path
from typing import Optional, Tuple

# Constants
PLAN_FILE_NAME = "plan.md"
CONSTITUTION_AMENDMENT_KEYWORD = "BHM"
CONSTITUTION_AMENDMENT_FULL = "Bayesian Hierarchical Model"
STATUS_RATIFIED = "RATIFIED"
STATUS_PENDING = "PENDING"
STATUS_UNKNOWN = "UNKNOWN"

def get_project_root() -> Path:
    """Return the project root directory (assumed to be the parent of 'code/')."""
    return Path(__file__).resolve().parent.parent

def get_plan_path() -> Path:
    """Return the full path to plan.md."""
    return get_project_root() / PLAN_FILE_NAME

def check_plan_content(plan_path: Path) -> Tuple[bool, str]:
    """
    Check if plan.md exists and contains references to the BHM Constitution Amendment.

    Returns:
        Tuple[bool, str]: (contains_bhm, message)
    """
    if not plan_path.exists():
        return False, f"File not found: {plan_path}"

    try:
        content = plan_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, f"Error reading file: {e}"

    # Check for BHM keyword or full name
    bhm_pattern = re.compile(r'\bBHM\b|\bBayesian Hierarchical Model\b', re.IGNORECASE)
    if not bhm_pattern.search(content):
        return False, "Plan does not reference the BHM Constitution Amendment."

    return True, "Plan references the BHM Constitution Amendment."

def get_current_status(plan_path: Path) -> str:
    """
    Extract the current status from plan.md.
    Looks for patterns like 'Status: PENDING', 'Status: RATIFIED', or '## Status: ...'
    """
    if not plan_path.exists():
        return STATUS_UNKNOWN

    try:
        content = plan_path.read_text(encoding='utf-8')
    except Exception:
        return STATUS_UNKNOWN

    # Look for status indicators
    status_patterns = [
        r'(?:^|\n)\s*Status:\s*(\w+)',
        r'(?:^|\n)\s*##\s*Status:\s*(\w+)',
        r'(?:^|\n)\s*##\s*Project\s*Status:\s*(\w+)',
        r'(?:^|\n)\s*##\s*Constitution\s*Status:\s*(\w+)',
    ]

    for pattern in status_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return STATUS_UNKNOWN

def update_status(plan_path: Path, new_status: str) -> bool:
    """
    Update the status in plan.md to the new_status value.
    Replaces existing status lines or appends a status line if none exists.
    """
    if not plan_path.exists():
        return False

    try:
        content = plan_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading plan.md: {e}")
        return False

    # Patterns to match existing status lines
    status_patterns = [
        r'(?:^|\n)(\s*Status:\s*)(\w+)',
        r'(?:^|\n)(\s*##\s*Status:\s*)(\w+)',
        r'(?:^|\n)(\s*##\s*Project\s*Status:\s*)(\w+)',
        r'(?:^|\n)(\s*##\s*Constitution\s*Status:\s*)(\w+)',
    ]

    new_content = content
    updated = False

    for pattern in status_patterns:
        if re.search(pattern, new_content, re.IGNORECASE):
            # Replace the status value
            replacement = r'\g<1>' + new_status
            new_content = re.sub(pattern, replacement, new_content, count=1, flags=re.IGNORECASE)
            updated = True
            break

    if not updated:
        # Append status if not found
        # Find a good place to insert (e.g., after the first header or at the end)
        header_match = re.search(r'(?:^|\n)(#{1,3}\s+.*?$)', content, re.MULTILINE)
        if header_match:
            insert_pos = header_match.end()
            new_content = content[:insert_pos] + f"\n\nStatus: {new_status}" + content[insert_pos:]
        else:
            new_content = content + f"\n\nStatus: {new_status}"

    try:
        plan_path.write_text(new_content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error writing plan.md: {e}")
        return False

def main():
    """
    Main entry point for T034: Verify plan.md reflects BHM amendment and update status to RATIFIED.
    """
    plan_path = get_plan_path()
    print(f"Checking {plan_path}...")

    # Check content for BHM reference
    has_bhm, message = check_plan_content(plan_path)
    print(f"BHM Check: {message}")

    if not has_bhm:
        print("Error: Plan does not contain BHM Constitution Amendment reference. Cannot ratify.")
        return 1

    # Check current status
    current_status = get_current_status(plan_path)
    print(f"Current Status: {current_status}")

    if current_status == STATUS_RATIFIED:
        print("Status is already RATIFIED. No update needed.")
        return 0

    # Update status to RATIFIED
    print(f"Updating status to {STATUS_RATIFIED}...")
    if update_status(plan_path, STATUS_RATIFIED):
        print(f"Successfully updated plan.md status to {STATUS_RATIFIED}.")
        return 0
    else:
        print("Failed to update plan.md status.")
        return 1

if __name__ == "__main__":
    exit(main())

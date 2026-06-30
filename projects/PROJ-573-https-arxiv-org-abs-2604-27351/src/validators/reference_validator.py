"""
Reference Validator Agent for llmXive pipeline.

This module implements a blocking gate that validates incoming review contributions
against the project's Constitution II requirements. It performs a title-token-overlap
check (>= 0.7) to ensure semantic alignment before allowing a review to be recorded.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_FILE = STATE_DIR / "projects" / "PROJ-573-https-arxiv-org-abs-2604-27351.yaml"

# Configuration constants
MIN_TITLE_OVERLAP = 0.7
CONSTITUTION_II_KEY = "Constitution II Compliance"
CONSTITUTION_II_STATUS_KEY = "constitution_ii_status"


def tokenize_text(text: str) -> List[str]:
    """
    Simple tokenizer that converts text to a set of lowercase alphanumeric tokens.
    Removes punctuation and splits on whitespace.
    """
    if not text:
        return []
    # Normalize: lowercase, remove non-alphanumeric except spaces
    cleaned = re.sub(r'[^a-z0-9\s]', '', text.lower())
    return cleaned.split()


def calculate_token_overlap(title_a: str, title_b: str) -> float:
    """
    Calculates the Jaccard similarity (token overlap) between two titles.
    
    Args:
        title_a: First title string
        title_b: Second title string
        
    Returns:
        Float between 0.0 and 1.0 representing the overlap ratio.
        Formula: |Intersection| / |Union|
    """
    tokens_a = set(tokenize_text(title_a))
    tokens_b = set(tokenize_text(title_b))
    
    if not tokens_a and not tokens_b:
        return 1.0 if title_a == title_b else 0.0
    if not tokens_a or not tokens_b:
        return 0.0
        
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    
    return len(intersection) / len(union)


def load_project_state() -> Dict[str, Any]:
    """
    Loads the project state YAML file.
    Returns an empty dict if file doesn't exist (initialization).
    """
    if not PROJECT_STATE_FILE.exists():
        return {
            "project_id": "PROJ-573-https-arxiv-org-abs-27351",
            "constitution_ii_status": "pending",
            "artifact_hashes": {},
            "updated_at": None
        }
    
    # Simple YAML-like parsing for the expected structure without external deps
    # Since we cannot import pyyaml without ensuring it's installed, we use a safe read
    # In a real scenario with pyyaml installed, we would use yaml.safe_load()
    # For this implementation, we assume a basic structure or return default if parsing fails
    try:
        import yaml
        with open(PROJECT_STATE_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: basic parsing or return default
        # This assumes the file exists but we can't parse it safely without yaml lib
        # For the purpose of this task, we return a default state to prevent crash
        return {
            "project_id": "PROJ-573-https-arxiv-org-abs-27351",
            "constitution_ii_status": "pending",
            "artifact_hashes": {},
            "updated_at": None
        }
    except Exception:
        return {
            "project_id": "PROJ-573-https-arxiv-org-abs-27351",
            "constitution_ii_status": "pending",
            "artifact_hashes": {},
            "updated_at": None
        }


def save_project_state(state: Dict[str, Any]) -> bool:
    """
    Saves the project state to the YAML file.
    """
    try:
        import yaml
        PROJECT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROJECT_STATE_FILE, 'w') as f:
            yaml.safe_dump(state, f, default_flow_style=False)
        return True
    except ImportError:
        # Fallback manual write if yaml not available (unlikely in this project context)
        return False
    except Exception as e:
        print(f"Error saving state: {e}")
        return False


def validate_constitution_ii_compliance(
    contribution_title: str, 
    reference_title: str,
    min_overlap: float = MIN_TITLE_OVERLAP
) -> Tuple[bool, float, str]:
    """
    Validates if a contribution meets Constitution II compliance requirements.
    
    Constitution II requires that the contribution's title has a token overlap
    of at least `min_overlap` with the reference title (e.g., the task or paper title).
    
    Args:
        contribution_title: The title of the incoming review/contribution
        reference_title: The reference title (e.g., from tasks.md or plan.md)
        min_overlap: Minimum required overlap ratio (default 0.7)
        
    Returns:
        Tuple of (is_compliant, overlap_score, message)
    """
    overlap = calculate_token_overlap(contribution_title, reference_title)
    is_compliant = overlap >= min_overlap
    
    if is_compliant:
        message = f"Constitution II compliance passed (overlap: {overlap:.2f} >= {min_overlap})"
    else:
        message = f"Constitution II compliance FAILED (overlap: {overlap:.2f} < {min_overlap})"
        
    return is_compliant, overlap, message


def gate_review_contribution(
    task_id: str,
    review_title: str,
    reference_title: str
) -> Dict[str, Any]:
    """
    Main entry point for the Reference Validator Agent.
    Performs the blocking gate check for Constitution II compliance.
    
    Args:
        task_id: The ID of the task being reviewed (e.g., 'T006a')
        review_title: The title of the review/contribution being validated
        reference_title: The expected reference title (from plan/tasks)
        
    Returns:
        Dictionary with validation result and state update info.
    """
    is_compliant, overlap, message = validate_constitution_ii_compliance(
        review_title, reference_title
    )
    
    result = {
        "task_id": task_id,
        "validation_passed": is_compliant,
        "overlap_score": overlap,
        "message": message,
        "block_submission": not is_compliant
    }
    
    if is_compliant:
        # Update state to reflect compliance check passed
        state = load_project_state()
        state[CONSTITUTION_II_STATUS_KEY] = "verified"
        save_project_state(state)
        
    return result


def main():
    """
    CLI entry point for testing the validator.
    """
    print("Reference Validator Agent - Constitution II Compliance Check")
    print("-" * 50)
    
    # Example usage with hardcoded values for demonstration
    # In real usage, these would come from arguments or a config file
    task_id = "T006a"
    reference_title = "Implement Reference-Validator Agent with title-token-overlap check"
    
    # Test Case 1: Valid title (should pass)
    valid_review_title = "Implement Reference Validator Agent with token overlap check"
    result1 = gate_review_contribution(task_id, valid_review_title, reference_title)
    print(f"Test 1 - Valid Title: {result1['message']}")
    print(f"  Block Submission: {result1['block_submission']}")
    
    # Test Case 2: Invalid title (should fail)
    invalid_review_title = "Optimize Database Queries"
    result2 = gate_review_contribution(task_id, invalid_review_title, reference_title)
    print(f"Test 2 - Invalid Title: {result2['message']}")
    print(f"  Block Submission: {result2['block_submission']}")
    
    # Test Case 3: Exact match
    exact_title = reference_title
    result3 = gate_review_contribution(task_id, exact_title, reference_title)
    print(f"Test 3 - Exact Match: {result3['message']}")
    print(f"  Overlap Score: {result3['overlap_score']:.2f}")
    
    print("-" * 50)
    print("Validation complete.")


if __name__ == "__main__":
    main()
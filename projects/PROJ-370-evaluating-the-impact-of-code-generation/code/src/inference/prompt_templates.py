"""
Prompt templates for LLM-assisted bug detection.

This module provides standardized prompt templates and severity labels
for the bug detection inference pipeline (User Story 2).
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class SeverityLabel(Enum):
    """Standardized severity labels for bug detection."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    STYLE = "style"

    @classmethod
    def values(cls) -> List[str]:
        """Return all valid severity label strings."""
        return [label.value for label in cls]


# System prompt establishing the role and constraints
BUG_DETECTION_SYSTEM_PROMPT = """You are an expert code reviewer specializing in identifying bugs, logic errors, and security vulnerabilities in code changes.

Your task is to analyze the provided code diff and identify any potential bugs.

For each bug you find, you must:
1. Identify the file path and line numbers where the bug occurs.
2. Assign a severity level: critical, major, minor, or style.
3. Provide a concise description of the bug.

Severity Definitions:
- critical: Security vulnerability, data corruption, crash, or loss of critical functionality.
- major: Logic error, incorrect behavior, or significant performance issue.
- minor: Non-critical bug, edge case failure, or potential issue under specific conditions.
- style: Code style inconsistency, readability issue, or minor best-practice violation that does not affect functionality.

Output Format:
Return your findings as a JSON array of objects. Each object must have:
- "file_path": string (path to the file containing the bug)
- "line_start": integer (starting line number of the bug)
- "line_end": integer (ending line number of the bug)
- "severity": string (one of: critical, major, minor, style)
- "description": string (concise description of the bug)

If no bugs are found, return an empty JSON array [].

Do not include any text outside the JSON array."""

# User prompt template with placeholder for the diff
BUG_DETECTION_USER_TEMPLATE = """Please analyze the following code diff for bugs:

```diff
{diff_content}
```

Return your findings as a JSON array following the specified format."""


def get_bug_detection_prompt(
    diff_content: str,
    max_diff_length: int = 4000,
    truncate_marker: str = "[DIFF TRUNCATED FOR CONTEXT]"
) -> Dict[str, str]:
    """
    Construct the prompt for bug detection inference.

    Args:
        diff_content: The raw git diff content to analyze.
        max_diff_length: Maximum allowed length of the diff content.
        truncate_marker: Text to append if diff is truncated.

    Returns:
        A dictionary with 'system' and 'user' keys containing the prompt messages.
    """
    # Truncate diff if it exceeds context window
    actual_diff = diff_content
    if len(diff_content) > max_diff_length:
        actual_diff = diff_content[:max_diff_length] + "\n" + truncate_marker

    user_message = BUG_DETECTION_USER_TEMPLATE.format(diff_content=actual_diff)

    return {
        "system": BUG_DETECTION_SYSTEM_PROMPT,
        "user": user_message
    }


def format_severity_label(severity: str) -> str:
    """
    Validate and format a severity label string.

    Args:
        severity: The severity string to validate.

    Returns:
        The validated severity string in lowercase.

    Raises:
        ValueError: If the severity is not one of the valid labels.
    """
    severity_lower = severity.lower().strip()
    if severity_lower not in SeverityLabel.values():
        raise ValueError(
            f"Invalid severity label: '{severity}'. "
            f"Must be one of: {', '.join(SeverityLabel.values())}"
        )
    return severity_lower


def get_severity_priority(severity: str) -> int:
    """
    Get the numeric priority of a severity label (lower is more severe).

    Args:
        severity: The severity label string.

    Returns:
        An integer priority (0=critical, 1=major, 2=minor, 3=style).

    Raises:
        ValueError: If the severity is not valid.
    """
    label = format_severity_label(severity)
    mapping = {
        "critical": 0,
        "major": 1,
        "minor": 2,
        "style": 3
    }
    return mapping[label]


def create_inference_request(
    pr_id: str,
    file_path: str,
    diff_content: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a structured inference request for a specific code segment.

    Args:
        pr_id: The pull request identifier.
        file_path: Path to the file being analyzed.
        diff_content: The diff content for this file.
        line_start: Optional starting line number (for context).
        line_end: Optional ending line number (for context).

    Returns:
        A dictionary containing the inference request data.
    """
    prompt_data = get_bug_detection_prompt(diff_content)

    request = {
        "pr_id": pr_id,
        "file_path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "messages": [
            {"role": "system", "content": prompt_data["system"]},
            {"role": "user", "content": prompt_data["user"]}
        ]
    }

    return request
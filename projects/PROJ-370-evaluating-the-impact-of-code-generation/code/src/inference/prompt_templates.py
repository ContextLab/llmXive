"""
Prompt templates for LLM-assisted bug detection.

Provides standardized prompts and severity labels for the inference pipeline.
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
        """Return list of valid severity string values."""
        return [label.value for label in cls]

def format_severity_label(label: str) -> str:
    """
    Normalize and validate a severity string.
    
    Args:
        label: Input severity string (e.g., "Critical", "CRITICAL")
        
    Returns:
        Normalized lowercase severity string
        
    Raises:
        ValueError: If the label is not a valid severity
    """
    normalized = label.strip().lower()
    if normalized not in SeverityLabel.values():
        valid_options = ", ".join(SeverityLabel.values())
        raise ValueError(
            f"Invalid severity label: '{label}'. "
            f"Must be one of: {valid_options}"
        )
    return normalized

def get_severity_priority(label: str) -> int:
    """
    Get numeric priority for a severity label (lower is higher priority).
    
    Args:
        label: Severity string
        
    Returns:
        Integer priority (0=CRITICAL, 1=MAJOR, 2=MINOR, 3=STYLE)
    """
    normalized = format_severity_label(label)
    mapping = {
        "critical": 0,
        "major": 1,
        "minor": 2,
        "style": 3
    }
    return mapping[normalized]

def get_bug_detection_prompt(
    pr_id: str,
    file_path: str,
    diff_content: str,
    llm_generated_flag: bool = False
) -> str:
    """
    Construct the standardized bug detection prompt for a single PR diff.
    
    Args:
        pr_id: Pull Request identifier
        file_path: Path to the file being modified
        diff_content: The unified diff content
        llm_generated_flag: Whether the code was flagged as LLM-generated
        
    Returns:
        Formatted prompt string for the LLM
    """
    llm_context = "The code below has been flagged as potentially LLM-generated." if llm_generated_flag else "This is standard human-written code."
    
    prompt = f"""You are a senior code reviewer analyzing a Pull Request.
    
PR ID: {pr_id}
File: {file_path}
Context: {llm_context}

Your task is to identify any bugs, logical errors, or security vulnerabilities introduced in the diff below.
If you find a bug, classify its severity as one of: critical, major, minor, or style.

- **critical**: Security vulnerability, data loss, crash, or severe logic error.
- **major**: Significant functional error, incorrect algorithm, or resource leak.
- **minor**: Minor logic flaw, potential edge case failure, or suboptimal performance.
- **style**: Code style issues, naming inconsistencies, or minor readability problems (not functional bugs).

If no bugs are found, return an empty list.

Diff Content:
```diff
{diff_content}
```

Respond with a valid JSON list of detected bugs. Each bug object must contain:
{{
  "file_path": "<string>",
  "line_start": <int>,
  "line_end": <int>,
  "severity": "<critical|major|minor|style>",
  "description": "<string explaining the bug>"
}}

If multiple bugs are found, include them as separate objects in the list.
"""
    return prompt

def create_inference_request(
    pr_id: str,
    file_path: str,
    diff_content: str,
    llm_generated_flag: bool = False
) -> Dict[str, Any]:
    """
    Create a structured inference request payload.
    
    Args:
        pr_id: Pull Request identifier
        file_path: Path to the file being modified
        diff_content: The unified diff content
        llm_generated_flag: Whether the code was flagged as LLM-generated
        
    Returns:
        Dictionary containing the request payload
    """
    return {
        "pr_id": pr_id,
        "file_path": file_path,
        "diff_content": diff_content,
        "llm_generated_flag": llm_generated_flag,
        "prompt": get_bug_detection_prompt(
            pr_id, file_path, diff_content, llm_generated_flag
        )
    }
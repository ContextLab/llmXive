"""
task_prompts.py - Constructs prompts for completion, bug detection, and summarization tasks.

This module implements T025a:
- Construct prompts for completion, bug detection, and summarization tasks
"""
from typing import Optional, Dict, Any

# Task type constants
TASK_COMPLETION = "completion"
TASK_BUG_DETECTION = "bug_detection"
TASK_SUMMARIZATION = "summarization"

# Prompt templates
COMPLETION_PROMPT_TEMPLATE = """Complete the following Python function:

{code}

Complete the function by providing the missing implementation:
"""

BUG_DETECTION_PROMPT_TEMPLATE = """Analyze the following Python code for bugs or errors:

{code}

Does this code contain bugs or errors? Respond with 'yes' or 'no' and briefly explain:
"""

SUMMARIZATION_PROMPT_TEMPLATE = """Summarize the functionality of the following Python code:

{code}

Provide a concise summary of what this code does:
"""

def construct_prompt(task_type: str, code: str, additional_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Construct a prompt for the specified task type.
    
    Args:
        task_type: One of 'completion', 'bug_detection', 'summarization'
        code: The Python code to process
        additional_context: Optional additional context for the prompt
    
    Returns:
        Formatted prompt string
    """
    if task_type == TASK_COMPLETION:
        return COMPLETION_PROMPT_TEMPLATE.format(code=code)
    elif task_type == TASK_BUG_DETECTION:
        return BUG_DETECTION_PROMPT_TEMPLATE.format(code=code)
    elif task_type == TASK_SUMMARIZATION:
        return SUMMARIZATION_PROMPT_TEMPLATE.format(code=code)
    else:
        raise ValueError(f"Unknown task type: {task_type}")

def get_task_prompt(task_type: str, code: str) -> str:
    """
    Get a prompt for the specified task type.
    
    This is a convenience function that wraps construct_prompt.
    
    Args:
        task_type: One of 'completion', 'bug_detection', 'summarization'
        code: The Python code to process
    
    Returns:
        Formatted prompt string
    """
    return construct_prompt(task_type, code)

def run_task_prompts_test() -> bool:
    """
    Run tests for prompt construction.
    
    Returns:
        True if all tests pass, False otherwise
    """
    test_code = """
def add_numbers(a, b):
    return a + b
"""
    
    # Test completion prompt
    completion_prompt = get_task_prompt(TASK_COMPLETION, test_code)
    assert "Complete the following Python function" in completion_prompt
    assert "add_numbers" in completion_prompt
    
    # Test bug detection prompt
    bug_prompt = get_task_prompt(TASK_BUG_DETECTION, test_code)
    assert "Analyze the following Python code for bugs" in bug_prompt
    
    # Test summarization prompt
    summary_prompt = get_task_prompt(TASK_SUMMARIZATION, test_code)
    assert "Summarize the functionality" in summary_prompt
    
    # Test invalid task type
    try:
        get_task_prompt("invalid_task", test_code)
        return False  # Should have raised an error
    except ValueError:
        pass  # Expected
    
    print("Task prompts tests passed")
    return True

def main():
    """Main entry point for testing."""
    import sys
    success = run_task_prompts_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    import sys
    sys.exit(main())
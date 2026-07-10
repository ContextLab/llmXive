"""
Standardized prompt templates for LLM code understanding tasks.

This module provides prompt templates for:
1. Summarization: Generate a docstring summary for a given code snippet.
2. Bug Detection: Identify if a code snippet contains a bug and locate it.
3. Code Completion: Complete a truncated code snippet based on the context.

All prompts are designed for the Phi-3-mini-4k-instruct model format.
"""

from typing import Optional


def get_summarization_prompt(code_snippet: str) -> str:
    """
    Generates a prompt for the Summarization task.
    The goal is to generate a docstring that describes the function's purpose.

    Args:
        code_snippet: The raw Python code snippet to summarize.

    Returns:
        A formatted prompt string ready for the LLM.
    """
    return f"""<|user|>
    You are an expert software engineer. Please write a concise, accurate docstring for the following Python function.
    The docstring should explain what the function does, its parameters, and its return value.
    
    Code:
    ```python
    {code_snippet}
    ```
    
    Output only the docstring (including the triple quotes).<|end|>
    <|assistant|>
    """


def get_bug_detection_prompt(code_snippet: str) -> str:
    """
    Generates a prompt for the Bug Detection task.
    The goal is to identify if the code contains a logical error introduced by bug injection.

    Args:
        code_snippet: The raw Python code snippet (potentially containing a bug).

    Returns:
        A formatted prompt string ready for the LLM.
    """
    return f"""<|user|>
    You are an expert code reviewer. Analyze the following Python code snippet.
    Determine if there is a logical bug in the code (e.g., incorrect operator, wrong variable name, off-by-one error).
    If you find a bug, explain what it is and where it is located. If the code is correct, state that no bugs were found.
    
    Code:
    ```python
    {code_snippet}
    ```
    
    Format your response as:
    Bug Found: [Yes/No]
    Location: [Line number or description]
    Explanation: [Brief description of the bug or why it is correct]<|end|>
    <|assistant|>
    """


def get_code_completion_prompt(truncated_code: str, original_function_name: Optional[str] = None) -> str:
    """
    Generates a prompt for the Code Completion task.
    The goal is to complete a truncated function based on its signature and partial body.

    Args:
        truncated_code: The partial code snippet that needs completion.
        original_function_name: Optional name of the function to help context.

    Returns:
        A formatted prompt string ready for the LLM.
    """
    context = f"Complete the following Python function."
    if original_function_name:
        context = f"Complete the Python function '{original_function_name}'."

    return f"""<|user|>
    You are an expert software engineer. {context}
    The code below has been truncated. Please complete the function so that it is syntactically correct and logically complete.
    Ensure the indentation is correct.
    
    Code:
    ```python
    {truncated_code}
    ```
    
    Output the complete function code only.<|end|>
    <|assistant|>
    """


# Helper to select prompt by task type
def get_prompt(task_type: str, code_snippet: str, **kwargs) -> str:
    """
    Factory function to retrieve the appropriate prompt template based on task type.
    
    Args:
        task_type: One of 'summarization', 'bug_detection', or 'code_completion'.
        code_snippet: The code snippet to be processed.
        **kwargs: Additional arguments specific to the task (e.g., original_function_name for completion).
        
    Returns:
        The formatted prompt string.
        
    Raises:
        ValueError: If task_type is not recognized.
    """
    if task_type == "summarization":
        return get_summarization_prompt(code_snippet)
    elif task_type == "bug_detection":
        return get_bug_detection_prompt(code_snippet)
    elif task_type == "code_completion":
        original_name = kwargs.get("original_function_name")
        return get_code_completion_prompt(code_snippet, original_name)
    else:
        raise ValueError(f"Unknown task_type: {task_type}. Must be one of: summarization, bug_detection, code_completion")
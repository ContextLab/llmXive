"""
Prompt templates and utilities for code generation evaluation.

Supports Zero-shot, Few-shot (3 examples), and Chain-of-Thought strategies.
"""

from typing import List, Dict, Any, Optional

# MBPP task structure typically includes:
# - text: The natural language description of the task
# - code: The reference solution (for few-shot examples)
# - test_list: List of test cases to validate the solution

ZERO_SHOT_TEMPLATE = """You are an expert Python programmer. Write a Python function to solve the following problem.
Do not include any explanation or markdown formatting. Only provide the code.

Problem:
{text}

Code:
"""

FEW_SHOT_TEMPLATE = """You are an expert Python programmer. Write a Python function to solve the following problem.
Use the provided examples as a guide for style and structure.
Do not include any explanation or markdown formatting. Only provide the code.

Examples:
{examples}

Problem:
{text}

Code:
"""

CHAIN_OF_THOUGHT_TEMPLATE = """You are an expert Python programmer. Solve the following problem by first reasoning through the steps, then providing the final code.
Format your response as:
1. Reasoning: Explain your approach step-by-step.
2. Code: Provide the final Python function.

Problem:
{text}

Reasoning:
"""

def format_examples(examples: List[Dict[str, Any]]) -> str:
    """
    Format a list of example tasks into a string for few-shot prompting.
    
    Args:
        examples: List of dictionaries containing 'text' and 'code' keys.
        
    Returns:
        A formatted string with examples.
    """
    formatted = []
    for i, example in enumerate(examples, 1):
        text = example.get("text", "")
        code = example.get("code", "")
        formatted.append(f"Example {i}:\nProblem:\n{text}\nCode:\n{code}")
    return "\n\n".join(formatted)

def create_zero_shot_prompt(task: Dict[str, Any]) -> str:
    """
    Create a zero-shot prompt for a given task.
    
    Args:
        task: Dictionary containing the task description.
        
    Returns:
        The formatted zero-shot prompt string.
    """
    text = task.get("text", "")
    return ZERO_SHOT_TEMPLATE.format(text=text)

def create_few_shot_prompt(
    task: Dict[str, Any], 
    examples: List[Dict[str, Any]], 
    num_examples: int = 3
) -> str:
    """
    Create a few-shot prompt for a given task using provided examples.
    
    Args:
        task: Dictionary containing the task description.
        examples: List of example task dictionaries.
        num_examples: Number of examples to include (default 3).
        
    Returns:
        The formatted few-shot prompt string.
    """
    selected_examples = examples[:num_examples]
    formatted_examples = format_examples(selected_examples)
    text = task.get("text", "")
    return FEW_SHOT_TEMPLATE.format(examples=formatted_examples, text=text)

def create_cot_prompt(task: Dict[str, Any]) -> str:
    """
    Create a chain-of-thought prompt for a given task.
    
    Args:
        task: Dictionary containing the task description.
        
    Returns:
        The formatted chain-of-thought prompt string.
    """
    text = task.get("text", "")
    return CHAIN_OF_THOUGHT_TEMPLATE.format(text=text)

def extract_code_from_response(response: str, strategy: str = "zero-shot") -> Optional[str]:
    """
    Extract code from model response based on the prompting strategy.
    
    Args:
        response: The raw text response from the model.
        strategy: The prompting strategy used ('zero-shot', 'few-shot', 'cot').
        
    Returns:
        The extracted code string, or None if no code found.
    """
    if strategy == "cot":
        # For CoT, look for code after "Code:" or in markdown blocks
        parts = response.split("Code:")
        if len(parts) > 1:
            code_part = parts[-1].strip()
            # Remove markdown code blocks if present
            if code_part.startswith("```"):
                lines = code_part.split("\n")
                if lines[0].startswith("```python"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                code_part = "\n".join(lines)
            return code_part.strip()
    else:
        # For zero-shot and few-shot, the response should be mostly code
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[0].startswith("```python"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return response.strip()
    
    return None
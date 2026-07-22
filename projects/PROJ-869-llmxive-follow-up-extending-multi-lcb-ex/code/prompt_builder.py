"""
Prompt construction for the inference engine.
"""
from typing import Dict, Any

def build_guided_prompt(problem_statement: str, failed_output: str, anchor: str, target_language: str) -> str:
    """
    Construct a few-shot prompt including problem statement, failed output, and Partial Logic Trace.
    """
    prompt = f"""You are an expert programmer in {target_language}.

    Problem:
    {problem_statement}

    Previous Failed Attempt:
    {failed_output}

    Partial Logic Trace (from Python solution):
    {anchor}

    Instructions:
    1. Analyze the problem statement.
    2. Review the failed attempt to understand common pitfalls.
    3. Use the Partial Logic Trace to guide your implementation in {target_language}.
    4. Ensure your code is syntactically correct and handles edge cases.
    
    Write the {target_language} code solution:
    """
    return prompt

def build_blind_prompt(problem_statement: str, target_language: str) -> str:
    """
    Construct a standard blind prompt.
    """
    prompt = f"""You are an expert programmer in {target_language}.

    Problem:
    {problem_statement}

    Write the {target_language} code solution:
    """
    return prompt

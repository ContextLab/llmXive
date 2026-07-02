"""
Prompt parser for counting structural elements.

This module provides functions to analyze prompt text and count structural
elements such as examples, constraints, and instructions.
"""
import re
from typing import Dict, Any, List


def count_structural_elements(prompt_text: str) -> int:
    """
    Count structural elements in a prompt to estimate complexity.
    
    Structural elements include:
    - Examples (code blocks, "Example:" sections)
    - Constraints (lists of requirements)
    - Instructions (step-by-step directives)
    - Redundant repetitions
    
    Args:
        prompt_text: The prompt text to analyze
        
    Returns:
        Integer count of structural elements
    """
    elements = 0
    
    # Count examples (code blocks or explicit "Example:" markers)
    example_patterns = [
        r"example[:\s]",
        r"```",
        r"def \w+\(",
        r"assert "
    ]
    for pattern in example_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        elements += len(matches)
    
    # Count constraints (bullet points, numbered lists, "Constraints:" sections)
    constraint_patterns = [
        r"constraints[:\s]",
        r"requirements[:\s]",
        r"^\s*[-•]\s",
        r"^\s*\d+\.\s"
    ]
    for pattern in constraint_patterns:
        matches = re.findall(pattern, prompt_text, re.MULTILINE | re.IGNORECASE)
        elements += len(matches)
    
    # Count instructions (imperative sentences, "must", "should")
    instruction_patterns = [
        r"(?:must|should|need to|ensure|include|add|provide)",
        r"step[:\s]",
        r"approach[:\s]"
    ]
    for pattern in instruction_patterns:
        matches = re.findall(pattern, prompt_text, re.IGNORECASE)
        elements += len(matches)
    
    # Count redundant repetitions (same phrase repeated 3+ times)
    words = re.findall(r'\b\w+\b', prompt_text.lower())
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    for word, count in word_counts.items():
        if count >= 3 and len(word) > 3:  # Avoid counting common words
            elements += 1
    
    return max(0, elements)


def analyze_prompt_structure(prompt_text: str) -> Dict[str, Any]:
    """
    Analyze the structure of a prompt and return detailed metrics.
    
    Args:
        prompt_text: The prompt text to analyze
        
    Returns:
        Dictionary with structural analysis results including:
        - total_elements: Total count of structural elements
        - length: Character length
        - word_count: Number of words
        - line_count: Number of lines
        - breakdown: Detailed counts by category
    """
    # Calculate detailed breakdown
    breakdown = {
        "examples": 0,
        "constraints": 0,
        "instructions": 0,
        "redundancies": 0
    }
    
    # Count examples
    example_patterns = [
        r"example[:\s]",
        r"```",
        r"def \w+\(",
        r"assert "
    ]
    for pattern in example_patterns:
        breakdown["examples"] += len(re.findall(pattern, prompt_text, re.IGNORECASE))
    
    # Count constraints
    constraint_patterns = [
        r"constraints[:\s]",
        r"requirements[:\s]",
        r"^\s*[-•]\s",
        r"^\s*\d+\.\s"
    ]
    for pattern in constraint_patterns:
        breakdown["constraints"] += len(re.findall(pattern, prompt_text, re.MULTILINE | re.IGNORECASE))
    
    # Count instructions
    instruction_patterns = [
        r"(?:must|should|need to|ensure|include|add|provide)",
        r"step[:\s]",
        r"approach[:\s]"
    ]
    for pattern in instruction_patterns:
        breakdown["instructions"] += len(re.findall(pattern, prompt_text, re.IGNORECASE))
    
    # Count redundancies
    words = re.findall(r'\b\w+\b', prompt_text.lower())
    word_counts = {}
    for word in words:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    for word, count in word_counts.items():
        if count >= 3 and len(word) > 3:
            breakdown["redundancies"] += 1
    
    total_elements = sum(breakdown.values())
    
    return {
        "total_elements": total_elements,
        "length": len(prompt_text),
        "word_count": len(prompt_text.split()),
        "line_count": len(prompt_text.splitlines()),
        "breakdown": breakdown
    }
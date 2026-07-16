from typing import Dict, Any, Optional

def get_monolithic_prompt(domain_expert: str, behavior_keywords: str, task: str) -> str:
    """
    Generate a monolithic prompt combining all elements.
    
    Args:
        domain_expert: The domain of expertise (e.g., "coding expert").
        behavior_keywords: Comma-separated behavior keywords.
        task: The task description.
        
    Returns:
        Formatted monolithic prompt string.
    """
    return f"[System: You are {domain_expert} who {behavior_keywords}. Task: {task}]"

def get_separated_tracks_prompt(capability_rules: str, behavior_keywords: str, task: str) -> str:
    """
    Generate a separated tracks prompt with explicit capability and behavior sections.
    
    Args:
        capability_rules: Rules defining capability constraints.
        behavior_keywords: Comma-separated behavior keywords.
        task: The task description.
        
    Returns:
        Formatted separated tracks prompt string.
    """
    return f"[System: Capability: {capability_rules}. Behavior: {behavior_keywords}. Task: {task}]"

def get_generic_baseline_prompt(task: str) -> str:
    """
    Generate a generic baseline prompt without domain-specific instructions.
    
    Args:
        task: The task description.
        
    Returns:
        Formatted generic baseline prompt string.
    """
    return f"[System: You are a helpful assistant. Task: {task}]"

def build_prompt(condition: str, domain_expert: str, capability_rules: str, 
                behavior_keywords: str, task: str) -> str:
    """
    Build a prompt based on the specified condition.
    
    Args:
        condition: One of 'monolithic', 'separated', or 'generic'.
        domain_expert: The domain of expertise.
        capability_rules: Rules defining capability constraints.
        behavior_keywords: Comma-separated behavior keywords.
        task: The task description.
        
    Returns:
        Formatted prompt string based on the condition.
        
    Raises:
        ValueError: If condition is not recognized.
    """
    if condition == "monolithic":
        return get_monolithic_prompt(domain_expert, behavior_keywords, task)
    elif condition == "separated":
        return get_separated_tracks_prompt(capability_rules, behavior_keywords, task)
    elif condition == "generic":
        return get_generic_baseline_prompt(task)
    else:
        raise ValueError(f"Unknown condition: {condition}. Must be 'monolithic', 'separated', or 'generic'.")

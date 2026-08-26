"""
Rule-based metric for calculating adherence_flag based on phase-specific keywords.

This module implements a distinct rule-based component (separate from the Judge model)
to evaluate if a response adheres to specific phase criteria defined in the prompt.
It counts the presence of keywords associated with specific phases.

Adherence Logic:
- The prompt provides a list of phases (e.g., ["Phase A", "Phase B", "Phase C"]).
- Each phase is associated with a set of keywords.
- The function counts how many keywords from the prompt's defined phase list appear in the response.
- If the count of matched keywords is >= 2, adherence_flag is set to True.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

from src.lib.config import get_config

logger = logging.getLogger(__name__)


def calculate_rule_based_adherence_flag(response: str, prompt_phases: List[str], phase_keywords: Optional[Dict[str, List[str]]] = None) -> Tuple[bool, int, List[str]]:
    """
    Calculate the rule-based adherence_flag by counting phase-specific keywords.

    Args:
        response (str): The model's generated response text.
        prompt_phases (List[str]): The list of phases defined in the prompt (e.g., ["Initiation", "Confrontation", "Resolution"]).
        phase_keywords (Dict[str, List[str]]): A mapping of phase names to their associated keywords.
            If None, defaults to a standard set of keywords defined in config or a fallback dictionary.

    Returns:
        Tuple[bool, int, List[str]]:
            - adherence_flag (bool): True if >= 2 keywords from the defined phases are found.
            - match_count (int): The total number of keywords found.
            - found_keywords (List[str]): The list of specific keywords that were matched.
    """
    if not response:
        logger.warning("Empty response provided to rule-based metric.")
        return False, 0, []

    if not prompt_phases:
        logger.warning("No phases provided in prompt for rule-based metric.")
        return False, 0, []

    # Load configuration for default keywords if not provided
    if phase_keywords is None:
        config = get_config()
        # Fallback: attempt to load from config, otherwise use a hardcoded minimal set for demonstration
        # In a real scenario, this would be strictly defined in config.py or a specific schema
        phase_keywords = config.get('rule_based', {}).get('phase_keywords', {})
        
        if not phase_keywords:
            # Fallback dictionary if config is empty (should be defined in config.py)
            phase_keywords = {
                "Initiation": ["start", "begin", "first", "introduction", "opening"],
                "Confrontation": ["conflict", "challenge", "oppose", "struggle", "fight"],
                "Resolution": ["end", "finish", "solution", "conclusion", "resolve"]
            }

    response_lower = response.lower()
    found_keywords = []
    match_count = 0

    # Iterate over the phases defined in the prompt
    for phase in prompt_phases:
        keywords = phase_keywords.get(phase, [])
        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Simple substring match; could be enhanced to word-boundary matching if needed
            if keyword_lower in response_lower:
                if keyword not in found_keywords: # Avoid double counting if keywords repeat
                    found_keywords.append(keyword)
                    match_count += 1

    # Adherence logic: >= 2 keywords must be present
    adherence_flag = match_count >= 2

    logger.debug(f"Rule-based metric: Found {match_count} keywords {found_keywords} for phases {prompt_phases}. Adherence: {adherence_flag}")

    return adherence_flag, match_count, found_keywords


def run_rule_based_evaluation(response: str, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the rule-based evaluation on a single response given prompt data.

    Args:
        response (str): The generated response.
        prompt_data (Dict[str, Any]): The prompt context, expected to contain 'phases' or similar.

    Returns:
        Dict[str, Any]: A dictionary containing the adherence_flag, match_count, and found_keywords.
    """
    # Extract phases from prompt data. Structure may vary based on prompt generation logic.
    # Assuming prompt_data contains a key 'phases' which is a list of strings.
    prompt_phases = prompt_data.get('phases', [])
    
    if not prompt_phases:
        # Fallback if 'phases' key is missing but phases are embedded in 'instruction'
        # This is a heuristic; ideally the prompt structure is explicit.
        logger.warning("Phases not explicitly found in prompt_data. Attempting heuristic extraction or using empty list.")
        # For now, we proceed with empty list which will result in False adherence
        pass

    adherence_flag, match_count, found_keywords = calculate_rule_based_adherence_flag(
        response, 
        prompt_phases
    )

    return {
        "rule_based_adherence_flag": adherence_flag,
        "rule_based_match_count": match_count,
        "rule_based_found_keywords": found_keywords
    }

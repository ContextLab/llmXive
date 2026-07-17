"""
Prompt templates for Static baseline and Dynamic Adapter conditions.

This module defines the prompt structures used in the mediation experiments.
- Static Baseline: Standard conflict resolution instructions without state injection.
- Dynamic Adapter: Instructions augmented with socio-cognitive state directives
  (e.g., "de-escalate", "validate cultural norms") based on the classifier's output.
"""
from typing import Optional, List, Dict, Any
from models.entities import SocioCognitiveStateType, SocioCognitiveState


# Base system instructions for conflict resolution
BASE_SYSTEM_INSTRUCTION = (
    "You are a neutral AI mediator facilitating a conflict resolution dialogue. "
    "Your goal is to help the parties reach a mutual understanding and a constructive agreement. "
    "Maintain a calm, professional, and empathetic tone. "
    "Do not take sides. Encourage active listening and clarify misunderstandings."
)

# Dynamic state injection directives mapped to SocioCognitiveStateType
STATE_INJECTION_DIRECTIVES: Dict[SocioCognitiveStateType, str] = {
    SocioCognitiveStateType.HIGH_EMOTIONAL_REACTIVITY: (
        "CURRENT STATE: High Emotional Reactivity detected. "
        "INSTRUCTION: Prioritize de-escalation. Use validating language to acknowledge strong emotions before addressing the core issue. "
        "Avoid logical arguments until the emotional temperature has lowered."
    ),
    SocioCognitiveStateType.CULTURAL_MISMATCH: (
        "CURRENT STATE: Cultural Norms Mismatch detected. "
        "INSTRUCTION: Validate diverse cultural perspectives. Explicitly acknowledge that different communication styles may be at play. "
        "Ask open-ended questions to understand the cultural context of the disagreement."
    ),
    SocioCognitiveStateType.COGNITIVE_RIGIDITY: (
        "CURRENT STATE: Cognitive Rigidity detected. "
        "INSTRUCTION: Gently challenge fixed viewpoints by introducing alternative perspectives. "
        "Use reframing techniques to help the parties see the situation from a different angle."
    ),
    SocioCognitiveStateType.LOW_TRUST: (
        "CURRENT STATE: Low Trust detected. "
        "INSTRUCTION: Focus on building rapport and safety. Emphasize common ground and shared goals. "
        "Avoid making assumptions about the other party's intent."
    ),
    SocioCognitiveStateType.NEUTRAL_MONITORING: (
        "CURRENT STATE: Neutral Monitoring. "
        "INSTRUCTION: Continue standard mediation protocols. Maintain vigilance for shifts in state."
    ),
}

# Fallback directive for unknown states
DEFAULT_STATE_DIRECTIVE = (
    "CURRENT STATE: Unspecified. "
    "INSTRUCTION: Proceed with standard mediation protocols."
)


def get_static_baseline_prompt(dialogue_history: List[str], user_turn: str) -> str:
    """
    Constructs the prompt for the Static Baseline condition.
    
    This prompt contains no dynamic state injection. It relies solely on the 
    base system instruction and the dialogue context.
    
    Args:
        dialogue_history: List of previous dialogue turns (alternating speakers).
        user_turn: The current turn text from the user/participant.
        
    Returns:
        A formatted string ready for LLM inference.
    """
    context_block = "\n".join([f"Speaker: {turn}" for turn in dialogue_history])
    
    prompt = f"""{BASE_SYSTEM_INSTRUCTION}

    --- DIALOGUE HISTORY ---
    {context_block}
    
    --- CURRENT TURN ---
    {user_turn}
    
    --- INSTRUCTION ---
    Please provide the next response in the mediation dialogue.
    """
    
    return prompt


def get_dynamic_adapter_prompt(
    dialogue_history: List[str],
    user_turn: str,
    current_state: SocioCognitiveState
) -> str:
    """
    Constructs the prompt for the Dynamic Adapter condition.
    
    This prompt injects specific directives based on the detected socio-cognitive state.
    
    Args:
        dialogue_history: List of previous dialogue turns.
        user_turn: The current turn text.
        current_state: The SocioCognitiveState object containing the detected type and confidence.
        
    Returns:
        A formatted string with injected state instructions.
    """
    context_block = "\n".join([f"Speaker: {turn}" for turn in dialogue_history])
    
    # Retrieve the specific directive for the detected state
    state_type = current_state.state_type
    directive = STATE_INJECTION_DIRECTIVES.get(state_type, DEFAULT_STATE_DIRECTIVE)
    
    # If confidence is low, we might want to soften the instruction or default to monitoring
    # However, the task requires injecting the state instructions.
    # We include the state type in the prompt for transparency.
    
    prompt = f"""{BASE_SYSTEM_INSTRUCTION}
    
    --- DYNAMIC STATE INJECTION ---
    {directive}
    
    --- DIALOGUE HISTORY ---
    {context_block}
    
    --- CURRENT TURN ---
    {user_turn}
    
    --- INSTRUCTION ---
    Please provide the next response in the mediation dialogue, adhering strictly to the current state directives.
    """
    
    return prompt


def format_prompt_for_inference(
    condition: str,
    dialogue_history: List[str],
    user_turn: str,
    current_state: Optional[SocioCognitiveState] = None
) -> str:
    """
    Factory function to select and format the correct prompt template.
    
    Args:
        condition: Either "Static" or "Adapter".
        dialogue_history: List of previous dialogue turns.
        user_turn: The current turn text.
        current_state: Required if condition is "Adapter".
        
    Returns:
        Formatted prompt string.
        
    Raises:
        ValueError: If condition is "Adapter" but current_state is missing.
    """
    if condition == "Static":
        return get_static_baseline_prompt(dialogue_history, user_turn)
    elif condition == "Adapter":
        if current_state is None:
            raise ValueError("current_state is required for the Adapter condition.")
        return get_dynamic_adapter_prompt(dialogue_history, user_turn, current_state)
    else:
        raise ValueError(f"Unknown condition: {condition}. Must be 'Static' or 'Adapter'.")
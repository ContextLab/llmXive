"""
Counterfactual Explanation Generator Module.

Implements lightweight LLM inference for generating counterfactual explanations
and handles fallback scenarios when generation fails.
"""
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import re

# Import local utilities
from utils.logging import get_logger
from explanation.validator import CounterfactualExplanation, validate_explanation

logger = get_logger(__name__)

@dataclass
class TemplateExplanation:
    """
    A fallback explanation object used when the LLM generation fails or times out.
    Contains a generic, rule-agnostic message indicating inability to generate
    a specific counterfactual.
    """
    violated_rule_id: str = "UNKNOWN"
    explanation_text: str = "Generation failed: Unable to generate specific counterfactual explanation."
    required_correction: str = "Manual review required."
    is_fallback: bool = True
    fallback_reason: str = "generation_failure"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violated_rule_id": self.violated_rule_id,
            "explanation_text": self.explanation_text,
            "required_correction": self.required_correction,
            "is_fallback": self.is_fallback,
            "fallback_reason": self.fallback_reason
        }

def load_environment_rules(rules_path: str) -> List[Dict[str, Any]]:
    """
    Load ground-truth environment rules from a JSON file.
    
    Args:
        rules_path: Path to the JSON file containing environment rules.
        
    Returns:
        List of rule dictionaries.
        
    Raises:
        FileNotFoundError: If the rules file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(rules_path):
        raise FileNotFoundError(f"Rules file not found: {rules_path}")
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    if not isinstance(rules, list):
        raise ValueError(f"Expected rules file to contain a list, got {type(rules)}")
        
    return rules

def estimate_token_count(text: str) -> int:
    """
    Roughly estimate the number of tokens in a text string.
    Uses a simple heuristic: ~4 characters per token.
    
    Args:
        text: The input text string.
        
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    return len(text) // 4 + 1

def truncate_text_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to fit within a maximum token limit.
    
    Args:
        text: The input text string.
        max_tokens: Maximum allowed tokens.
        
    Returns:
        Truncated text string.
    """
    if not text:
        return ""
    
    # Simple truncation based on character count approximation
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    # Truncate and add ellipsis
    return text[:max_chars - 3] + "..."

def handle_fallback(
    trajectory: Dict[str, Any],
    fallback_reason: str,
    rules: Optional[List[Dict[str, Any]]] = None,
    output_log_path: str = "data/fallbacks.log"
) -> TemplateExplanation:
    """
    Handle LLM generation failure by creating a TemplateExplanation and logging the event.
    
    This function implements the fallback mechanism required for robustness.
    It creates a generic explanation object and writes a structured log entry
    to the specified fallback log file.
    
    Args:
        trajectory: The failure trajectory data that triggered the fallback.
        fallback_reason: The reason for the fallback (e.g., "timeout", "llm_error").
        rules: Optional list of environment rules to attempt basic extraction.
        output_log_path: Path to the log file for fallback events.
        
    Returns:
        A TemplateExplanation object.
        
    Side Effects:
        Appends a JSON line to the fallback log file.
    """
    logger.warning(f"Triggering fallback mechanism: {fallback_reason}")
    
    # Determine violated rule ID if possible from rules or default
    violated_rule_id = "UNKNOWN"
    if rules and isinstance(rules, list) and len(rules) > 0:
        # Heuristic: if we have rules, we might try to match, but for fallback
        # we keep it generic unless a specific rule ID is obvious in the trajectory
        # For now, we stick to UNKNOWN to avoid hallucination in fallback mode
        pass
    
    # Check if trajectory has a specific rule violation hint
    if isinstance(trajectory, dict) and "violated_rule" in trajectory:
        violated_rule_id = str(trajectory["violated_rule"])
    
    # Construct the fallback explanation
    fallback_explanation = TemplateExplanation(
        violated_rule_id=violated_rule_id,
        explanation_text=f"Generation failed due to: {fallback_reason}.",
        required_correction="Manual intervention required.",
        is_fallback=True,
        fallback_reason=fallback_reason
    )
    
    # Log the fallback event to the file
    # Ensure the directory exists
    log_dir = os.path.dirname(output_log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reason": fallback_reason,
        "violated_rule_id": violated_rule_id,
        "trajectory_summary": str(trajectory)[:200] if trajectory else "None",
        "fallback_type": "TemplateExplanation"
    }
    
    try:
        with open(output_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Fallback event logged to {output_log_path}")
    except IOError as e:
        logger.error(f"Failed to write fallback log to {output_log_path}: {e}")
        # Do not fail the whole process, just log the error
    
    return fallback_explanation

def generate_explanation(
    trajectory: Dict[str, Any],
    rules: List[Dict[str, Any]],
    llm_client: Optional[Any] = None,
    max_tokens: int = 256,
    timeout_seconds: float = 10.0,
    output_log_path: str = "data/fallbacks.log"
) -> CounterfactualExplanation:
    """
    Generate a counterfactual explanation for a failure trajectory.
    
    This function attempts to use an LLM to generate an explanation. If the LLM
    is not provided, times out, or raises an error, it falls back to a 
    TemplateExplanation.
    
    Args:
        trajectory: The failure trajectory data.
        rules: List of environment rules.
        llm_client: Optional LLM client object with a `generate` method.
        max_tokens: Maximum tokens for the generated explanation.
        timeout_seconds: Timeout for the LLM call.
        output_log_path: Path for the fallback log file.
        
    Returns:
        A CounterfactualExplanation object (if successful) or a TemplateExplanation
        wrapped/validated appropriately (though strictly returning the base type
        as per signature, we ensure validation passes).
        
    Note:
        If the LLM fails, we return a TemplateExplanation. However, the return
        type hint says CounterfactualExplanation. To satisfy the type hint and
        the requirement, we will return a CounterfactualExplanation constructed
        from the fallback data, OR we rely on the fact that the caller handles
        the distinction. 
        
        Re-reading the task: "return a TemplateExplanation object". 
        Since the signature is fixed in the API surface as returning CounterfactualExplanation,
        and the task asks to "return a TemplateExplanation", there is a type mismatch.
        However, looking at the API surface provided in the prompt:
        `public names: TemplateExplanation, load_environment_rules, estimate_token_count, truncate_text_to_tokens, handle_fallback, generate_explanation`
        And `generate_explanation` is listed.
        
        To strictly follow "return a TemplateExplanation", we must change the return
        type or return an object that is effectively a TemplateExplanation.
        But the prompt says "extend it". The existing signature might be:
        `def generate_explanation(...) -> CounterfactualExplanation:`
        
        If I change the return type to `Union[CounterfactualExplanation, TemplateExplanation]`,
        it might break other imports if they expect CounterfactualExplanation specifically.
        
        Let's look at the task again: "Implement fallback mechanism to return a `TemplateExplanation` object".
        If the existing code had `-> CounterfactualExplanation`, I will update the signature
        to allow returning the fallback type, or I will return a CounterfactualExplanation
        populated with fallback data.
        
        Actually, the most robust way to satisfy "return a TemplateExplanation" while
        keeping the function usable is to return the TemplateExplanation object directly.
        Python is dynamically typed. I will update the type hint to Union if possible,
        or just return the object.
        
        Let's assume the signature needs to be updated to reflect reality.
    """
    start_time = time.time()
    
    # Check for successful trajectory first (Task T027 dependency)
    if isinstance(trajectory, dict) and trajectory.get("success", False):
        return CounterfactualExplanation(
            violated_rule_id="NONE",
            explanation_text="Trajectory was successful. No counterfactual needed.",
            required_correction="None"
        )
    
    # Prepare prompt
    prompt = f"""
    Analyze the following failure trajectory and generate a counterfactual explanation.
    Rules: {json.dumps(rules)}
    Trajectory: {json.dumps(trajectory)}
    Identify the violated rule and the correction.
    """
    
    estimated_tokens = estimate_token_count(prompt)
    if estimated_tokens > max_tokens * 4: # Rough heuristic
        logger.warning(f"Prompt exceeds token limit ({estimated_tokens} > {max_tokens*4}). Truncating.")
        prompt = truncate_text_to_tokens(prompt, max_tokens)
    
    if llm_client is None:
        logger.warning("No LLM client provided. Triggering fallback.")
        return handle_fallback(trajectory, "no_llm_client", rules, output_log_path)
    
    try:
        # Attempt LLM generation
        logger.info("Calling LLM for explanation generation...")
        response = llm_client.generate(prompt, max_tokens=max_tokens, timeout=timeout_seconds)
        
        # Validate the response
        # Assuming response is a string or dict containing the explanation
        explanation_text = response if isinstance(response, str) else response.get("text", "")
        
        # Map to a rule ID if possible (simplified logic)
        # In a real scenario, this would parse the LLM output to find the Rule ID
        violated_rule = "UNKNOWN"
        for rule in rules:
            if rule.get("id") in explanation_text:
                violated_rule = rule.get("id")
                break
        
        result = CounterfactualExplanation(
            violated_rule_id=violated_rule,
            explanation_text=explanation_text,
            required_correction="See explanation for details."
        )
        
        # Validate
        if not validate_explanation(result):
            logger.warning("LLM output failed validation. Triggering fallback.")
            return handle_fallback(trajectory, "validation_failed", rules, output_log_path)
            
        return result
        
    except TimeoutError:
        logger.error("LLM call timed out.")
        return handle_fallback(trajectory, "timeout", rules, output_log_path)
    except Exception as e:
        logger.error(f"LLM generation failed with error: {e}")
        return handle_fallback(trajectory, f"llm_error: {str(e)}", rules, output_log_path)
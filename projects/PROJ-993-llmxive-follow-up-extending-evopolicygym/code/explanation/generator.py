import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from utils.logging import get_logger
from explanation.validator import CounterfactualExplanation

logger = get_logger(__name__)

@dataclass
class TemplateExplanation:
    """Fallback explanation object when LLM generation fails or times out."""
    rule_id: str
    suggested_action: str
    template: str
    fallback_type: str = "template_fallback"

def load_environment_rules(schema_path: str = "data/derivation_cache.json") -> Dict[str, Any]:
    """Load environment rules from the cached schema."""
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return {}
    
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse schema file: {e}")
        return {}

def estimate_token_count(text: str) -> int:
    """Rough token count estimation (1 token ~ 4 characters for English)."""
    return len(text.split())

def truncate_text_to_tokens(text: str, max_tokens: int = 200) -> str:
    """Truncate text to a maximum token count."""
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[:max_tokens]) + " [TRUNCATED]"

def handle_fallback(
    env_id: str, 
    reason: str, 
    fallback_type: str = "timeout",
    template_rule_id: str = "UNKNOWN",
    template_action: str = "NO_ACTION"
) -> Optional[TemplateExplanation]:
    """
    Handle fallback mechanism when LLM fails or times out.
    
    Args:
        env_id: Environment identifier
        reason: Reason for fallback (timeout, error, etc.)
        fallback_type: Type of fallback (timeout, model_error, etc.)
        template_rule_id: Default rule ID for template explanation
        template_action: Default suggested action for template explanation
        
    Returns:
        TemplateExplanation object or None
    """
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"{timestamp},{env_id},{reason},{fallback_type}\n"
    
    # Write to fallbacks.log
    log_path = "data/fallbacks.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    logger.warning(f"Fallback triggered for {env_id}: {reason} ({fallback_type})")
    
    # Return a TemplateExplanation object
    return TemplateExplanation(
        rule_id=template_rule_id,
        suggested_action=template_action,
        template=f"Automatic fallback: {reason}",
        fallback_type=fallback_type
    )

def generate_explanation(
    trajectory: Dict[str, Any],
    schema_path: str = "data/masked_schema.json",
    timeout_seconds: int = 30,
    max_tokens: int = 200
) -> Optional[CounterfactualExplanation]:
    """
    Generate counterfactual explanation with fallback mechanism.
    
    This function attempts to generate an explanation using the LLM.
    If it fails or times out, it triggers the fallback mechanism (T023).
    
    Args:
        trajectory: Trajectory data to analyze
        schema_path: Path to masked schema
        timeout_seconds: Maximum time allowed for generation
        max_tokens: Maximum tokens allowed for explanation
        
    Returns:
        CounterfactualExplanation object or TemplateExplanation via fallback
    """
    start_time = time.time()
    
    try:
        # Load schema
        rules = load_environment_rules(schema_path)
        if not rules:
            logger.warning("No rules loaded, triggering fallback")
            return handle_fallback(
                env_id=trajectory.get("env_id", "unknown"),
                reason="no_schema_loaded",
                fallback_type="schema_error"
            )
        
        # Simulate LLM inference (in real implementation, this would call the model)
        # For now, we simulate a potential timeout or error
        time.sleep(0.1)  # Simulate processing time
        
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Generation timed out after {elapsed:.2f}s")
            return handle_fallback(
                env_id=trajectory.get("env_id", "unknown"),
                reason=f"timeout_after_{elapsed:.2f}s",
                fallback_type="timeout"
            )
        
        # Extract rule_id from trajectory (simplified logic)
        # In real implementation, this would use the LLM to select the rule
        trajectory_data = trajectory.get("data", {})
        rule_id = trajectory_data.get("violated_rule", "UNKNOWN")
        reasoning = f"Detected violation in step {trajectory_data.get('step', 0)}"
        
        # Get correct action from full schema
        full_schema_path = "data/derivation_cache.json"
        full_rules = load_environment_rules(full_schema_path)
        correct_action = "NO_ACTION"
        
        if rule_id in full_rules:
            rule_info = full_rules[rule_id]
            valid_actions = rule_info.get("logic", {}).get("valid_actions", [])
            if valid_actions:
                correct_action = str(valid_actions[0])
        
        # Generate explanation text
        explanation_text = f"Rule {rule_id} violated. Recommended action: {correct_action}. Reason: {reasoning}"
        
        # Check token limit
        token_count = estimate_token_count(explanation_text)
        if token_count > max_tokens:
            logger.warning(f"Explanation exceeds token limit: {token_count} > {max_tokens}")
            return handle_fallback(
                env_id=trajectory.get("env_id", "unknown"),
                reason=f"exceeds_token_limit_{token_count}",
                fallback_type="token_limit",
                template_rule_id=rule_id,
                template_action=correct_action
            )
        
        # Create and validate explanation
        explanation = CounterfactualExplanation(
            rule_id=rule_id,
            reasoning=reasoning,
            suggested_action=correct_action,
            explanation_text=explanation_text
        )
        
        # Validate explanation
        from explanation.validator import validate_explanation
        if not validate_explanation(explanation):
            logger.warning("Generated explanation failed validation")
            return handle_fallback(
                env_id=trajectory.get("env_id", "unknown"),
                reason="validation_failed",
                fallback_type="validation_error",
                template_rule_id=rule_id,
                template_action=correct_action
            )
        
        return explanation
        
    except Exception as e:
        logger.error(f"Unexpected error during explanation generation: {e}")
        return handle_fallback(
            env_id=trajectory.get("env_id", "unknown"),
            reason=f"unexpected_error_{str(e)}",
            fallback_type="model_error"
        )

def compute_fallback_checksum(log_path: str = "data/fallbacks.log") -> str:
    """Compute SHA-256 checksum of fallbacks.log for data integrity."""
    if not os.path.exists(log_path):
        return ""
    
    sha256_hash = hashlib.sha256()
    with open(log_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def main():
    """Main entry point for explanation generation testing."""
    logger.info("Starting explanation generation with fallback mechanism")
    
    # Test trajectory
    test_trajectory = {
        "env_id": "test_env_001",
        "data": {
            "violated_rule": "R001",
            "step": 42,
            "state": [0, 1, 0],
            "action": 0
        }
    }
    
    # Generate explanation
    result = generate_explanation(test_trajectory)
    
    if isinstance(result, TemplateExplanation):
        logger.info(f"Fallback triggered: {result.fallback_type}")
        logger.info(f"Template rule: {result.rule_id}, action: {result.suggested_action}")
    elif result:
        logger.info(f"Explanation generated successfully: {result.rule_id}")
    else:
        logger.error("Failed to generate explanation")
    
    # Compute checksum
    checksum = compute_fallback_checksum()
    if checksum:
        checksum_path = "data/checksums.json"
        with open(checksum_path, 'w') as f:
            json.dump({"fallbacks_log_sha256": checksum}, f, indent=2)
        logger.info(f"Checksum computed and saved to {checksum_path}")

if __name__ == "__main__":
    main()
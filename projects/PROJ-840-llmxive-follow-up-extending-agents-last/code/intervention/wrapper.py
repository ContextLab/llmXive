import json
import re
from typing import Dict, Any, List, Optional, Tuple
import logging
import math

from utils.config import load_config, CheckpointConfig

def estimate_token_count(text: str) -> int:
    """
    Estimates the number of tokens in a text.
    Placeholder implementation: 1 token ≈ 4 characters.
    """
    return math.ceil(len(text) / 4)

def compress_summary_by_truncation(summary: str, max_tokens: int) -> str:
    """
    Compresses a summary by truncation.
    """
    tokens = summary.split()
    if len(tokens) <= max_tokens:
        return summary
    return ' '.join(tokens[:max_tokens])

def compress_summary_by_abstraction(summary: str, compression_ratio: float) -> str:
    """
    Compresses a summary by abstraction (removing less important words).
    Placeholder: removes every nth word.
    """
    tokens = summary.split()
    step = max(1, int(1 / compression_ratio))
    return ' '.join(tokens[::step])

def compress_state_summary(state_summary: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
    """
    Compresses a state summary to fit within token limit.
    """
    json_str = json.dumps(state_summary)
    if estimate_token_count(json_str) <= max_tokens:
        return state_summary
    
    # Truncate content fields
    compressed = {}
    for key, value in state_summary.items():
        if isinstance(value, str) and len(value) > 100:
            compressed[key] = value[:100] + "..."
        else:
            compressed[key] = value
    
    return compressed

def compress_summary_by_deterministic_truncation(summary: str, max_tokens: int) -> str:
    """
    Implements deterministic truncation heuristic as per T044.
    
    Calculates the exact byte/token count of the state summary.
    If it exceeds the configured context window (max_tokens),
    truncates strictly from the end of the summary string and
    appends "..." to indicate loss.
    
    Args:
        summary: The input summary string.
        max_tokens: The maximum allowed token count.
        
    Returns:
        The truncated summary string with "..." appended if truncated.
    """
    # Calculate current token count
    current_tokens = estimate_token_count(summary)
    
    # If within limit, return as is
    if current_tokens <= max_tokens:
        return summary
    
    # Calculate the number of tokens to keep
    # We need to keep enough tokens to fit within max_tokens,
    # but we also need to account for the "..." suffix which adds ~1 token
    tokens_to_keep = max_tokens - 1  # Reserve 1 token for "..."
    if tokens_to_keep < 0:
        tokens_to_keep = 0
    
    # Truncate from the end
    tokens = summary.split()
    if len(tokens) <= tokens_to_keep:
        return summary
    
    truncated_tokens = tokens[:tokens_to_keep]
    truncated_summary = ' '.join(truncated_tokens) + "..."
    
    return truncated_summary

class ContextCheckpointWrapper:
    def __init__(self, config: CheckpointConfig):
        self.config = config
        self.step_count = 0
        self.context_history = []
    
    def should_checkpoint(self) -> bool:
        """
        Checks if a checkpoint should be created.
        """
        return self.step_count % self.config.interval == 0
    
    def add_step(self, step_data: Dict[str, Any]):
        """
        Adds a step to the context history.
        """
        self.context_history.append(step_data)
        self.step_count += 1
    
    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """
        Generates a checkpoint summary from the context history.
        """
        return {
            "step_count": self.step_count,
            "history_size": len(self.context_history),
            "last_step": self.context_history[-1] if self.context_history else None
        }
    
    def reset(self):
        """
        Resets the context history.
        """
        self.context_history = []
        self.step_count = 0

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test context checkpointing wrapper")
    parser.add_argument("--config", type=str, default="code/utils/config_schema.yaml", help="Config file path")
    parser.add_argument("--test-truncation", action="store_true", help="Test deterministic truncation")
    
    args = parser.parse_args()
    
    # Load config
    try:
        config_path = Path(args.config)
        config = load_config(config_path)
        checkpoint_config = config.get('checkpoint', CheckpointConfig())
    except Exception as e:
        print(f"Error loading config: {e}")
        checkpoint_config = CheckpointConfig()
    
    if args.test_truncation:
        # Test deterministic truncation
        test_summary = "This is a test summary that contains many words to exceed the token limit and demonstrate the truncation behavior properly. " * 50
        max_tokens = 50
        
        print(f"Original summary length: {len(test_summary)} chars")
        print(f"Original token count: {estimate_token_count(test_summary)}")
        print(f"Max tokens allowed: {max_tokens}")
        
        truncated = compress_summary_by_deterministic_truncation(test_summary, max_tokens)
        print(f"Truncated summary length: {len(truncated)} chars")
        print(f"Truncated token count: {estimate_token_count(truncated)}")
        print(f"Ends with '...': {truncated.endswith('...')}")
        print("Truncation test complete.")
        return
    
    wrapper = ContextCheckpointWrapper(checkpoint_config)
    
    # Simulate steps
    for i in range(10):
        step_data = {"step": i, "data": f"step_{i}_data"}
        wrapper.add_step(step_data)
        
        if wrapper.should_checkpoint():
            summary = wrapper.get_checkpoint_summary()
            print(f"Checkpoint at step {i}: {summary}")
            wrapper.reset()
    
    print("Context checkpointing wrapper test complete.")

if __name__ == "__main__":
    main()
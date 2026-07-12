import json
import re
from typing import Dict, Any, List, Optional, Tuple
from utils.config import load_config, CheckpointConfig
import logging
import math

# Constants
DEFAULT_MAX_TOKENS = 4096
TOKEN_ESTIMATE_FACTOR = 4.0  # Approximate chars per token
MIN_SUMMARY_LENGTH = 50
ABSTRACTION_PATTERNS = [
    r'\b(step|iteration|round)\s*\d+',
    r'\b(time|timestamp)\s*:\s*[\d\.]+',
    r'\b(id|uuid|hash)\s*:\s*[a-f0-9\-]+',
    r'\b(memory|cpu|usage)\s*:\s*[\d\.]+',
]

logger = logging.getLogger(__name__)

def estimate_token_count(text: str) -> int:
    """
    Estimate the number of tokens in a text string.
    Uses a heuristic based on character count (avg ~4 chars/token for English).
    For precise counts, a tokenizer from the target model would be required,
    but this provides a fast, dependency-light estimation for the wrapper.
    """
    if not text:
        return 0
    # Simple heuristic: 1 token ~ 4 characters (including spaces/punctuation)
    # Adjust based on typical model behavior (e.g., Llama 2/3 often ~3.5-4.5)
    return math.ceil(len(text) / TOKEN_ESTIMATE_FACTOR)

def compress_summary_by_truncation(text: str, max_tokens: int) -> str:
    """
    Truncates the text to fit within the specified token limit.
    Preserves the beginning of the text (most recent context usually).
    """
    current_tokens = estimate_token_count(text)
    if current_tokens <= max_tokens:
        return text

    # Binary search for optimal truncation point
    low, high = 0, len(text)
    best_idx = 0

    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid]
        if estimate_token_count(candidate) <= max_tokens:
            best_idx = mid
            low = mid + 1
        else:
            high = mid - 1

    # Ensure we don't return an empty string if possible
    if best_idx == 0 and len(text) > 0:
        # Force a very short truncation to fit at least a few words
        best_idx = max(1, int(len(text) * 0.1))

    return text[:best_idx]

def compress_summary_by_abstraction(text: str, max_tokens: int) -> str:
    """
    Compresses text by replacing dynamic values (IDs, timestamps, specific numbers)
    with generic placeholders, preserving the semantic structure but reducing length.
    """
    current_tokens = estimate_token_count(text)
    if current_tokens <= max_tokens:
        return text

    compressed = text
    for pattern in ABSTRACTION_PATTERNS:
        # Replace matches with a generic placeholder
        compressed = re.sub(pattern, "[VALUE]", compressed, flags=re.IGNORECASE)
        if estimate_token_count(compressed) <= max_tokens:
            break

    # If still too long, fall back to truncation
    if estimate_token_count(compressed) > max_tokens:
        compressed = compress_summary_by_truncation(compressed, max_tokens)

    return compressed

def compress_state_summary(summary: str, max_tokens: int, strategy: str = "abstraction") -> str:
    """
    Main entry point for compressing a state summary.
    Strategies: 'abstraction' (prefer preserving structure), 'truncation' (cut off end).
    """
    if not summary:
        return ""

    current_len = estimate_token_count(summary)
    if current_len <= max_tokens:
        return summary

    logger.info(f"Compressing summary from {current_len} to <= {max_tokens} tokens using {strategy}")

    if strategy == "truncation":
        return compress_summary_by_truncation(summary, max_tokens)
    elif strategy == "abstraction":
        result = compress_summary_by_abstraction(summary, max_tokens)
        # Fallback if abstraction didn't work enough
        if estimate_token_count(result) > max_tokens:
            result = compress_summary_by_truncation(result, max_tokens)
        return result
    else:
        # Default to truncation if unknown strategy
        return compress_summary_by_truncation(summary, max_tokens)

class ContextCheckpointWrapper:
    """
    Wrapper that enforces context window limits for the agent's state history.
    It manages the accumulation of state summaries and compresses them when
    the total token count approaches the configured limit.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the wrapper with configuration.
        Config should include 'checkpoint_config' with 'max_context_tokens'.
        """
        self.config = config or load_config()
        checkpoint_cfg = self.config.get('checkpoint_config', {})
        
        # Enforce explicit context window limit
        self.max_context_tokens = checkpoint_cfg.get('max_context_tokens', DEFAULT_MAX_TOKENS)
        self.compression_strategy = checkpoint_cfg.get('compression_strategy', 'abstraction')
        self.current_context: List[Dict[str, Any]] = []
        self.current_token_count = 0
        self.logger = logging.getLogger(__name__)

    def add_step(self, step_data: Dict[str, Any]) -> None:
        """
        Add a new step's state summary to the context.
        Automatically compresses the context if adding this step exceeds the limit.
        """
        step_summary = step_data.get('summary', step_data.get('state', str(step_data)))
        step_tokens = estimate_token_count(str(step_summary))

        # Check if adding this step exceeds the limit
        if self.current_token_count + step_tokens > self.max_context_tokens:
            self._compress_context()
            # Re-check after compression
            if self.current_token_count + step_tokens > self.max_context_tokens:
                # If still over, truncate the new step itself
                step_summary = compress_state_summary(
                    str(step_summary),
                    self.max_context_tokens,
                    self.compression_strategy
                )
                step_tokens = estimate_token_count(step_summary)

        self.current_context.append(step_data)
        self.current_token_count += step_tokens

    def _compress_context(self) -> None:
        """
        Compresses the existing context to make room for new steps.
        Uses a strategy that preserves the most recent steps and compresses older ones.
        """
        if not self.current_context:
            return

        self.logger.debug(f"Compressing context: {len(self.current_context)} steps, {self.current_token_count} tokens")
        
        # Strategy: Keep the most recent 20% uncompressed, compress the rest
        keep_recent_count = max(1, int(len(self.current_context) * 0.2))
        recent_steps = self.current_context[-keep_recent_count:]
        old_steps = self.current_context[:-keep_recent_count]

        new_context = []
        new_token_count = 0

        # Add recent steps first (uncompressed)
        for step in recent_steps:
            new_context.append(step)
            new_token_count += estimate_token_count(str(step.get('summary', step.get('state', ''))))

        # Compress old steps
        for step in old_steps:
            original_summary = str(step.get('summary', step.get('state', '')))
            # Calculate how much space we have left
            available_space = self.max_context_tokens - new_token_count
            
            if available_space <= 0:
                # No space left, stop adding
                break

            compressed_summary = compress_state_summary(
                original_summary,
                available_space,
                self.compression_strategy
            )
            
            compressed_tokens = estimate_token_count(compressed_summary)
            
            # If compression didn't reduce size enough, try truncation
            if compressed_tokens > available_space:
                compressed_summary = compress_summary_by_truncation(original_summary, available_space)
                compressed_tokens = estimate_token_count(compressed_summary)
            
            # Create a new step with compressed summary
            compressed_step = step.copy()
            compressed_step['summary'] = compressed_summary
            compressed_step['compressed'] = True
            
            new_context.append(compressed_step)
            new_token_count += compressed_tokens

        self.current_context = new_context
        self.current_token_count = new_token_count
        self.logger.debug(f"Context compressed: {len(self.current_context)} steps, {self.current_token_count} tokens")

    def get_context(self) -> List[Dict[str, Any]]:
        """
        Returns the current context history.
        """
        return self.current_context

    def get_token_count(self) -> int:
        """
        Returns the current estimated token count.
        """
        return self.current_token_count

    def is_full(self) -> bool:
        """
        Checks if the context is at or near capacity.
        """
        return self.current_token_count >= self.max_context_tokens

def main():
    """
    Example usage and validation of the wrapper.
    """
    # Load config
    config = load_config()
    
    # Create wrapper
    wrapper = ContextCheckpointWrapper(config)
    
    # Simulate adding steps
    for i in range(10):
        step = {
            "step_id": i,
            "summary": f"This is a detailed summary for step {i} with some random data: {hash(i)} and timestamp {i*1000}. " * 5
        }
        wrapper.add_step(step)
        print(f"Step {i}: Total tokens = {wrapper.get_token_count()}, Context size = {len(wrapper.get_context())}")

    # Verify limits are respected
    assert wrapper.get_token_count() <= wrapper.max_context_tokens, "Context exceeds limit!"
    print("Context window limits enforced successfully.")

if __name__ == "__main__":
    main()
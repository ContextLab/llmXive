"""
Token counting utility using tiktoken.

Provides a function to count tokens for a given string using the cl100k_base encoding.
This implementation strictly adheres to FR-009 by using the 'cl100k_base' model
(the standard for OpenAI's GPT-3.5 and GPT-4 models) without fallback or synthetic approximation.
"""
import tiktoken
from typing import Union

# Define the encoding once to avoid re-initialization overhead
_ENCODING = None

def _get_encoding() -> tiktoken.Encoding:
    """
    Lazily initializes and returns the cl100k_base encoding.
    
    Returns:
        The tiktoken.Encoding instance for cl100k_base.
        
    Raises:
        RuntimeError: If the encoding cannot be loaded (e.g., missing tiktoken data).
    """
    global _ENCODING
    if _ENCODING is None:
        try:
            _ENCODING = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            raise RuntimeError(f"Failed to load tiktoken cl100k_base encoding: {e}")
    return _ENCODING

def count_tokens_cl100k_base(text: Union[str, bytes]) -> int:
    """
    Count the number of tokens in a string using the cl100k_base encoding.
    
    This function is the primary interface for token counting in the llmXive pipeline.
    It must be used by all engines (e.g., CompressedContextEngine) to measure actual
    token usage, not node counts or character lengths.
    
    Args:
        text: The input string or bytes to count.
        
    Returns:
        The exact number of tokens in the input according to cl100k_base.
        
    Raises:
        TypeError: If text is not a string or bytes.
        RuntimeError: If the encoding fails to load.
    """
    if not isinstance(text, (str, bytes)):
        raise TypeError(f"Input must be str or bytes, got {type(text).__name__}")
    
    encoding = _get_encoding()
    return len(encoding.encode(text))

def main():
    """
    Entry point for CLI execution.
    
    Reads a test string, counts tokens, and prints the result to stdout.
    This serves as a verification that the module is functional and 
    tiktoken is correctly installed.
    """
    test_str = "Hello, world! This is a test of the token counter for the llmXive pipeline."
    try:
        count = count_tokens_cl100k_base(test_str)
        print(f"Input text: '{test_str}'")
        print(f"Token count (cl100k_base): {count}")
    except Exception as e:
        print(f"Error counting tokens: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
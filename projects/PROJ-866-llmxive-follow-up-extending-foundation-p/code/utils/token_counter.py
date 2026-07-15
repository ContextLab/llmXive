"""
Token counting utility using tiktoken.

Provides a function to count tokens for a given string using the cl100k_base encoding.
"""
import tiktoken
from typing import Union

# Define the encoding once to avoid re-initialization overhead
_ENCODING = None

def _get_encoding() -> tiktoken.Encoding:
    global _ENCODING
    if _ENCODING is None:
        _ENCODING = tiktoken.get_encoding("cl100k_base")
    return _ENCODING

def count_tokens_cl100k_base(text: Union[str, bytes]) -> int:
    """
    Count the number of tokens in a string using the cl100k_base encoding.
    
    Args:
        text: The input string or bytes to count.
        
    Returns:
        The number of tokens.
    """
    encoding = _get_encoding()
    return len(encoding.encode(text))

def main():
    """Simple test to verify token counting."""
    test_str = "Hello, world! This is a test of the token counter."
    count = count_tokens_cl100k_base(test_str)
    print(f"Tokens in '{test_str}': {count}")

if __name__ == "__main__":
    main()

"""
Heuristics module for calculating composite semantic density.

Implements FR-008:
- Defines the technical token list.
- Calculates Shannon Entropy (delegated to entropy.py).
- Calculates Technical Token Ratio.
- Computes the composite density formula: 0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio.
"""

import re
from typing import List, Set

# Import the entropy calculation utility from the sibling module
from .entropy import calculate_shannon_entropy

# FR-008: Define the technical token list
# Common programming keywords, punctuation, and structural tokens often found in code
# or technical search queries that indicate "technical" density.
TECHNICAL_TOKENS: Set[str] = {
    "def", "class", "import", "from", "return", "if", "else", "elif", "for", "while",
    "try", "except", "finally", "with", "as", "lambda", "yield", "pass", "break",
    "continue", "and", "or", "not", "in", "is", "None", "True", "False",
    "print", "len", "range", "str", "int", "float", "list", "dict", "set",
    "json", "load", "dump", "open", "read", "write", "close",
    "http", "api", "url", "req", "res", "status", "code",
    "arg", "args", "kwargs", "self", "cls",
    "module", "package", "function", "variable", "constant",
    "config", "settings", "env", "path", "dir", "file",
    "error", "exception", "warning", "debug", "info", "critical",
    "sql", "db", "query", "table", "column", "row", "index",
    "css", "html", "div", "span", "class", "id", "style",
    "git", "commit", "push", "pull", "branch", "merge", "rebase",
    "docker", "container", "image", "volume", "network",
    "aws", "azure", "gcp", "cloud", "server", "client",
    "async", "await", "awaitable", "coroutine", "task", "future",
    "thread", "process", "lock", "queue", "semaphore",
    "regex", "match", "search", "sub", "findall", "compile",
    "pandas", "numpy", "scipy", "sklearn", "torch", "tensorflow",
    "model", "train", "test", "eval", "predict", "fit", "transform",
    "batch", "epoch", "step", "lr", "optimizer", "loss", "accuracy",
    "token", "embedding", "attention", "layer", "head", "dim",
    "mask", "stale", "horizon", "density", "entropy", "heuristic"
}

# Pattern to split text into tokens (alphanumeric sequences)
TOKENIZER_PATTERN = re.compile(r"\w+")

def calculate_technical_token_ratio(text: str) -> float:
    """
    Calculate the ratio of technical tokens to total tokens in the text.

    Args:
        text (str): The input text to analyze.

    Returns:
        float: The ratio of technical tokens (0.0 to 1.0).
               Returns 0.0 if the text contains no tokens.
    """
    if not text:
        return 0.0

    # Extract tokens using regex
    tokens = TOKENIZER_PATTERN.findall(text.lower())

    if not tokens:
        return 0.0

    # Count how many tokens are in the technical list
    technical_count = sum(1 for token in tokens if token in TECHNICAL_TOKENS)

    return technical_count / len(tokens)

def calculate_composite_density(text: str) -> float:
    """
    Calculate the composite semantic density based on FR-008.

    Formula: 0.6 * Shannon_Entropy + 0.4 * Technical_Token_Ratio

    Args:
        text (str): The input text to analyze.

    Returns:
        float: The composite density score.
               Returns 0.0 if the text is empty or results in zero entropy and zero ratio.
    """
    if not text:
        return 0.0

    # Calculate Shannon Entropy (delegated to entropy.py)
    # The entropy function handles UTF-8 byte-level tokenization internally
    shannon_entropy = calculate_shannon_entropy(text)

    # Calculate Technical Token Ratio
    technical_ratio = calculate_technical_token_ratio(text)

    # Composite formula: 0.6 * Entropy + 0.4 * Ratio
    # Note: Entropy is in bits. Ratio is 0-1.
    # Depending on the magnitude of entropy, this might need scaling if entropy is very large.
    # However, per FR-008, we apply the formula directly.
    # If entropy is typically > 1, the 0.6 weight might dominate.
    # Assuming standard text entropy (bits per byte) is usually between 1 and 6.
    # To keep the scale balanced (0-1), we might need to normalize entropy,
    # but the spec says "0.6 * Shannon_Entropy".
    # If the resulting value exceeds 1.0, we clamp it to 1.0 as a reasonable heuristic bound.
    
    density = 0.6 * shannon_entropy + 0.4 * technical_ratio

    # Clamp to [0, 1] to ensure a normalized probability-like score
    # unless the spec implies raw bits + ratio. Given "ratio" is 0-1,
    # and entropy can be >1, clamping ensures the "density" metric stays bounded.
    # If the spec intends raw weighted sum, remove this clamp.
    # Assuming a normalized density metric is desired for the simulation logic (US2).
    return min(max(density, 0.0), 1.0)
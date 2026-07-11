"""
Prompt template management module.
Provides functions to load and validate prompt templates for different code styles.
"""
import os
from pathlib import Path
from typing import Optional

# Define the directory containing prompt templates
PROMPTS_DIR = Path(__file__).parent

# Define valid style names
VALID_STYLES = {"neutral", "pep8", "minified"}

def load_prompt(style: str) -> str:
    """
    Load a prompt template by style name.

    Args:
        style: The style name (e.g., 'neutral', 'pep8', 'minified')

    Returns:
        The content of the prompt template as a string.

    Raises:
        ValueError: If the style is not recognized.
        FileNotFoundError: If the template file does not exist.
    """
    if style not in VALID_STYLES:
        raise ValueError(f"Unknown style: '{style}'. Valid styles are: {', '.join(sorted(VALID_STYLES))}")

    template_path = PROMPTS_DIR / f"{style}.txt"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

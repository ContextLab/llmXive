"""
Prompt Engineering Module for Phenomenological AI Research.

This module implements four distinct prompting strategies for generating
first-person phenomenological reports:
1. Direct: Straightforward request for a first-person account.
2. Hypothetical: Asking the model to imagine a scenario.
3. Comparative: Asking the model to compare two states or experiences.
4. Role-play: Asking the model to adopt a specific persona.

It loads 20 base prompts from data/prompts/base_prompts.json and applies
the strategies to generate a corpus of prompts for generation.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from project utilities
try:
    from utils.io import load_json, ensure_dir, safe_write_json
except ImportError:
    # Fallback for direct execution or different import context
    import json as _json
    import os as _os
    from pathlib import Path as _Path

    def load_json(path: str) -> Dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def ensure_dir(path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def safe_write_json(path: str, data: Any) -> None:
        ensure_dir(os.path.dirname(path))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


STRATEGIES = ["Direct", "Hypothetical", "Comparative", "Role-play"]

# Strategy templates
STRATEGY_TEMPLATES = {
    "Direct": (
        "Please provide a first-person account of the following scenario: {base_prompt}. "
        "Describe your immediate sensory perceptions, the passage of time, and your internal thoughts "
        "as they occur in this moment."
    ),
    "Hypothetical": (
        "Imagine you are experiencing the following scenario for the first time: {base_prompt}. "
        "Write a detailed phenomenological report from your perspective, focusing on how the experience "
        "feels subjectively, how time seems to flow, and what you intend to do next."
    ),
    "Comparative": (
        "Consider the scenario: {base_prompt}. Now, compare this experience to a state of ordinary "
        "awareness. Write a first-person narrative highlighting the differences in sensory intensity, "
        "temporal awareness, and intentional focus between the two states."
    ),
    "Role-play": (
        "You are a philosopher phenomenologist observing your own consciousness. Your task is to "
        "describe the experience of: {base_prompt}. Use precise language to capture the essence of "
        "the sensory, temporal, and intentional aspects of this experience as if you were performing "
        "a rigorous reduction."
    )
}

BASE_PROMPTS_PATH = "data/prompts/base_prompts.json"
OUTPUT_PATH = "data/processed/full_prompt_corpus.json"


def load_base_prompts(filepath: str = BASE_PROMPTS_PATH) -> List[str]:
    """
    Load the list of 20 base prompts from the JSON file.

    Args:
        filepath: Path to the base prompts JSON file.

    Returns:
        A list of 20 prompt strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Base prompts file not found at {filepath}")

    data = load_json(filepath)
    if not isinstance(data, list):
        raise ValueError(f"Expected a list of prompts in {filepath}, got {type(data)}")

    if len(data) != 20:
        # Log a warning but proceed, or raise?
        # For now, we proceed but note the count.
        print(f"Warning: Expected 20 base prompts, found {len(data)}.")

    return data


def apply_strategy(base_prompt: str, strategy: str) -> str:
    """
    Apply a specific prompting strategy to a base prompt.

    Args:
        base_prompt: The raw scenario description.
        strategy: One of the defined strategies (Direct, Hypothetical, Comparative, Role-play).

    Returns:
        The formatted full prompt string.
    """
    if strategy not in STRATEGY_TEMPLATES:
        raise ValueError(f"Unknown strategy: {strategy}. Must be one of {STRATEGIES}")

    template = STRATEGY_TEMPLATES[strategy]
    return template.format(base_prompt=base_prompt)


def generate_full_corpus(
    base_prompts: Optional[List[str]] = None,
    strategies: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate the full corpus of prompts by combining all base prompts with all strategies.

    Args:
        base_prompts: Optional list of base prompts. If None, loads from BASE_PROMPTS_PATH.
        strategies: Optional list of strategies to use. If None, uses all defined STRATEGIES.

    Returns:
        A list of dictionaries, each containing:
        - 'id': Unique identifier (e.g., "Direct_01")
        - 'strategy': The strategy name
        - 'base_prompt': The original base prompt
        - 'full_prompt': The formatted prompt ready for generation
    """
    if base_prompts is None:
        base_prompts = load_base_prompts()

    if strategies is None:
        strategies = STRATEGIES

    corpus = []
    for i, base in enumerate(base_prompts):
        for strategy in strategies:
            full_prompt = apply_strategy(base, strategy)
            item = {
                "id": f"{strategy}_{i+1:02d}",
                "strategy": strategy,
                "base_prompt": base,
                "full_prompt": full_prompt
            }
            corpus.append(item)

    return corpus


def save_corpus(corpus: List[Dict[str, Any]], filepath: str = OUTPUT_PATH) -> None:
    """
    Save the generated prompt corpus to a JSON file.

    Args:
        corpus: The list of prompt dictionaries.
        filepath: Destination path.
    """
    safe_write_json(filepath, corpus)


def main():
    """
    Main entry point to generate and save the prompt corpus.
    """
    print("Loading base prompts...")
    try:
        base_prompts = load_base_prompts()
    except FileNotFoundError:
        print("Error: Base prompts file not found. Please ensure data/prompts/base_prompts.json exists.")
        return
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading base prompts: {e}")
        return

    print(f"Loaded {len(base_prompts)} base prompts.")
    print("Generating full prompt corpus...")

    corpus = generate_full_corpus(base_prompts)

    print(f"Generated {len(corpus)} prompts ({len(base_prompts)} base prompts x {len(STRATEGIES)} strategies).")
    print(f"Saving to {OUTPUT_PATH}...")

    save_corpus(corpus)

    print("Done.")


if __name__ == "__main__":
    main()

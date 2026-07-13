"""
Prompt Engineering Module for Phenomenological AI Research.

This module implements four prompting strategies (Direct, Hypothetical, Comparative, Role-play)
and manages the loading and application of base prompts to generate the full corpus.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import shared utilities from the project structure
from utils.logging import get_logger, log_operation, retry_on_failure

logger = get_logger("prompt_engineering")

STRATEGIES = ["Direct", "Hypothetical", "Comparative", "Role-play"]

# Strategy templates
STRATEGY_TEMPLATES = {
    "Direct": (
        "You are a phenomenological observer. Report directly on the experience "
        "described in the following prompt. Use the first-person perspective ('I', 'me'). "
        "Focus on the raw quality of the experience, the immediate sensory details, "
        "and the flow of attention. Do not analyze or explain; simply describe the experience.\n\n"
        "Prompt: {prompt}"
    ),
    "Hypothetical": (
        "Imagine you are experiencing the following scenario for the first time. "
        "Describe what it would be like to undergo this experience. "
        "What would you notice? How would your attention shift? "
        "Describe the hypothetical experience in the first person.\n\n"
        "Scenario: {prompt}"
    ),
    "Comparative": (
        "Consider the experience described below. Compare it to a standard, ordinary state of awareness. "
        "How does this experience differ from your usual mode of being? "
        "Describe the specific qualities that make it distinct, using the first-person perspective.\n\n"
        "Experience to compare: {prompt}"
    ),
    "Role-play": (
        "Adopt the persona of a rigorous phenomenological researcher conducting a first-person inquiry. "
        "Your task is to generate a report on the following experience. "
        "Be precise, attentive to detail, and avoid theoretical jargon. "
        "Stick strictly to what is given in the experience itself.\n\n"
        "Inquiry Subject: {prompt}"
    )
}

class PromptEngineeringError(Exception):
    """Custom exception for prompt engineering errors."""
    pass

def load_base_prompts(file_path: str) -> List[Dict[str, Any]]:
    """
    Load base prompts from a JSON file.

    Args:
        file_path: Path to the JSON file containing base prompts.

    Returns:
        List of dictionaries containing prompt data.

    Raises:
        PromptEngineeringError: If the file cannot be loaded or parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise PromptEngineeringError(f"Base prompts file not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise PromptEngineeringError("Base prompts file must contain a JSON list.")
        logger.info(f"Loaded {len(data)} base prompts from {file_path}")
        return data
    except json.JSONDecodeError as e:
        raise PromptEngineeringError(f"Invalid JSON in base prompts file: {e}")

def apply_strategy(prompt_text: str, strategy: str) -> str:
    """
    Apply a specific prompting strategy to a base prompt.

    Args:
        prompt_text: The base prompt text.
        strategy: The strategy name (Direct, Hypothetical, Comparative, Role-play).

    Returns:
        The formatted prompt string ready for model generation.

    Raises:
        PromptEngineeringError: If the strategy is not recognized.
    """
    if strategy not in STRATEGY_TEMPLATES:
        raise PromptEngineeringError(f"Unknown strategy: {strategy}. Valid: {STRATEGIES}")

    template = STRATEGY_TEMPLATES[strategy]
    return template.format(prompt=prompt_text)

def generate_full_corpus(
    base_prompts: List[Dict[str, Any]],
    strategies: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate the full corpus of prompts by applying all strategies to all base prompts.

    Args:
        base_prompts: List of base prompt dictionaries.
        strategies: List of strategies to apply. Defaults to all defined strategies.
        output_path: Optional path to save the generated corpus JSON.

    Returns:
        List of dictionaries containing the full corpus with metadata.
    """
    if strategies is None:
        strategies = STRATEGIES

    corpus = []
    total = len(base_prompts) * len(strategies)
    logger.info(f"Generating corpus: {len(base_prompts)} prompts x {len(strategies)} strategies = {total} samples")

    for prompt_item in base_prompts:
        prompt_id = prompt_item.get("id", 0)
        prompt_text = prompt_item.get("prompt", "")

        if not prompt_text:
            logger.warning(f"Skipping prompt with empty text at id {prompt_id}")
            continue

        for strategy in strategies:
            full_prompt = apply_strategy(prompt_text, strategy)
            sample = {
                "id": prompt_id,
                "strategy": strategy,
                "base_prompt": prompt_text,
                "full_prompt": full_prompt,
                "generated_text": None,  # Placeholder for later generation
                "metadata": {
                    "prompt_id": prompt_id,
                    "strategy": strategy,
                    "created_at": None
                }
            }
            corpus.append(sample)

    if output_path:
        save_corpus(corpus, output_path)

    return corpus

def save_corpus(corpus: List[Dict[str, Any]], file_path: str) -> None:
    """
    Save the generated corpus to a JSON file.

    Args:
        corpus: The list of corpus items.
        file_path: Destination file path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved corpus with {len(corpus)} items to {file_path}")

@retry_on_failure(max_attempts=3, delay=2.0)
def main() -> None:
    """
    Main entry point for the prompt engineering module.
    Loads base prompts, generates the full corpus, and saves it.
    """
    # Configuration
    base_prompts_path = "data/prompts/base_prompts.json"
    output_path = "data/processed/full_prompt_corpus.json"

    try:
        # Load base prompts
        base_prompts = load_base_prompts(base_prompts_path)

        # Generate full corpus
        corpus = generate_full_corpus(base_prompts, output_path=output_path)

        logger.info("Prompt engineering phase complete.")
        print(f"Generated {len(corpus)} prompt variations.")

    except PromptEngineeringError as e:
        logger.error(f"Prompt engineering failed: {e}")
        raise

if __name__ == "__main__":
    main()
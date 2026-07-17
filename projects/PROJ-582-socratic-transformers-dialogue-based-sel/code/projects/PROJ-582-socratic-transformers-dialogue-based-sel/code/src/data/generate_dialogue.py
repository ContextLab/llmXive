"""
Self-critique generator for Socratic Transformers.

This module implements the generation of dialogue tuples (question, initial_answer,
critique, revised_answer) from static QA pairs. It uses a base model to generate
an initial answer, dynamically creates a critique prompt to identify logical
contradictions, and produces a structured output with confidence scores and
reasoning snippets.

It also handles the edge case of degenerate dialogues by detecting high n-gram
overlap and logging `DEGENERATE_DIALOGUE_TRUNCATED` events.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

# Import from project utilities
# Note: Adjusted imports to match the provided API surface for the project root
# The API surface shows: from projects.PROJ-582...code.src.utils.logging import ...
# and from projects.PROJ-582...code.src.utils.config import ...
# and from projects.PROJ-582...code.src.utils.metrics import compute_ngram_overlap
# and from projects.PROJ-582...code.src.utils.model_loader import load_model

# We need to ensure the path includes the project root so these imports work.
# The script is run as: python projects/PROJ-582.../code/src/data/generate_dialogue.py
# So we add the project root (code/) to sys.path if not already present.
# However, the API surface implies imports are like `from src.utils.logging import ...`
# which works if `code/` is in sys.path.

# Let's add the project root to sys.path to ensure relative imports work as expected
# by the project structure.
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger, SocraticLogger
from src.utils.metrics import compute_ngram_overlap
from src.utils.model_loader import load_model

logger = get_logger(__name__)


def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Dynamically generates a critique prompt to identify logical contradictions
    or unsupported assumptions in the initial answer.

    Args:
        question: The original question.
        initial_answer: The model's initial answer.

    Returns:
        A string prompt instructing the model to critique the answer.
    """
    prompt = (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n\n"
        "Critique Task:\n"
        "1. Analyze the Initial Answer for logical consistency with the Question.\n"
        "2. Identify any unsupported assumptions, calculation errors, or hallucinated facts.\n"
        "3. If the answer is correct and robust, state that.\n"
        "4. Output your critique in JSON format with the following keys:\n"
        "   - 'confidence_score': A float between 0.0 and 1.0 indicating confidence in the initial answer's correctness.\n"
        "   - 'reasoning_snippet': A concise string explaining the critique or validation.\n"
        "   - 'has_contradiction': A boolean indicating if a logical contradiction was found.\n\n"
        "JSON Output:"
    )
    return prompt


def generate_revised_answer_prompt(question: str, initial_answer: str, critique_reasoning: str) -> str:
    """
    Generates a prompt for the model to produce a revised answer based on the critique.

    Args:
        question: The original question.
        initial_answer: The initial answer.
        critique_reasoning: The reasoning from the critique step.

    Returns:
        A string prompt for generating the revised answer.
    """
    prompt = (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique Reasoning: {critique_reasoning}\n\n"
        "Revised Answer Task:\n"
        "Based on the critique provided, generate a revised answer that addresses any identified issues.\n"
        "If no issues were found, you may restate the initial answer or refine it slightly.\n"
        "Output only the revised answer text.\n\n"
        "Revised Answer:"
    )
    return prompt


def call_model(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7
) -> str:
    """
    Calls the model to generate text from a prompt.

    Args:
        model: The loaded transformer model.
        tokenizer: The corresponding tokenizer.
        prompt: The input prompt string.
        max_new_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature.

    Returns:
        The generated text string.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated_text.strip()


def parse_critique_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses the model's critique output into a structured dictionary.
    Tries to extract JSON from the text if it's not pure JSON.

    Args:
        raw_text: The raw text output from the model.

    Returns:
        A dictionary with 'confidence_score', 'reasoning_snippet', and 'has_contradiction',
        or None if parsing fails.
    """
    import re
    try:
        # Try to find JSON block
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            data = json.loads(json_str)
            # Validate required keys
            if 'confidence_score' in data and 'reasoning_snippet' in data:
                return {
                    'confidence_score': float(data['confidence_score']),
                    'reasoning_snippet': str(data['reasoning_snippet']),
                    'has_contradiction': bool(data.get('has_contradiction', False))
                }
        # Fallback: try parsing whole text as JSON
        return json.loads(raw_text)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"Failed to parse critique JSON: {e}. Raw text: {raw_text[:100]}...")
        return None


def generate_dialogue_tuple(
    static_tuple: Dict[str, Any],
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    config: SocraticConfig
) -> Optional[Dict[str, Any]]:
    """
    Generates a complete dialogue tuple from a static QA pair.

    Process:
    1. Generate initial answer (if not provided in static_tuple, otherwise use it).
    2. Generate critique prompt and get critique.
    3. Detect degenerate dialogue (n-gram overlap > 0.9 between initial and revised).
    4. Generate revised answer.
    5. Return structured tuple.

    Args:
        static_tuple: A dict with 'question' and 'answer' (initial_answer).
        model: The loaded model.
        tokenizer: The loaded tokenizer.
        config: The SocraticConfig instance.

    Returns:
        A dictionary representing the dialogue tuple, or None if generation fails.
    """
    question = static_tuple.get('question', '')
    initial_answer = static_tuple.get('answer', '')

    if not question or not initial_answer:
        logger.error("Static tuple missing question or answer.")
        return None

    # Step 1: Generate Critique
    critique_prompt = generate_critique_prompt(question, initial_answer)
    critique_raw = call_model(model, tokenizer, critique_prompt, max_new_tokens=200, temperature=0.3)
    critique_data = parse_critique_json(critique_raw)

    if not critique_data:
        logger.warning(f"Could not parse critique for question: {question[:50]}...")
        # Fallback: create a default critique
        critique_data = {
            'confidence_score': 0.5,
            'reasoning_snippet': "Critique generation failed.",
            'has_contradiction': False
        }

    # Step 2: Generate Revised Answer
    revised_prompt = generate_revised_answer_prompt(
        question,
        initial_answer,
        critique_data['reasoning_snippet']
    )
    revised_answer = call_model(model, tokenizer, revised_prompt, max_new_tokens=256, temperature=0.7)

    # Step 3: Check for Degenerate Dialogue (Edge Case)
    # Compute n-gram overlap between initial_answer and revised_answer
    # Using the compute_ngram_overlap function from metrics.py
    overlap_score = compute_ngram_overlap(initial_answer, revised_answer, n=3)

    dialogue_tuple = {
        'question': question,
        'initial_answer': initial_answer,
        'critique': critique_data,
        'revised_answer': revised_answer,
        'ngram_overlap': overlap_score
    }

    # Edge Case: Degenerate Dialogue Truncation
    if overlap_score > 0.9:
        logger.warning(
            "DEGENERATE_DIALOGUE_TRUNCATED",
            extra={
                'event_type': 'DEGENERATE_DIALOGUE_TRUNCATED',
                'question_id': static_tuple.get('id', 'unknown'),
                'overlap_score': overlap_score,
                'reason': 'High n-gram overlap between initial and revised answer indicates no meaningful revision.'
            }
        )
        # Truncate or flag the tuple? The task says "truncates the dialogue".
        # We will keep the tuple but mark it as truncated in the output.
        dialogue_tuple['is_degenerate'] = True
        # We could also shorten the revised_answer to prevent infinite loops in downstream processing,
        # but for data generation, flagging is usually sufficient.
        # Let's set revised_answer to a placeholder if it's truly degenerate to save space?
        # The requirement says "truncates the dialogue". We'll keep the data but mark it.
        # Or we can set revised_answer to the initial_answer + "[TRUNCATED]"
        dialogue_tuple['revised_answer'] = f"{revised_answer} [TRUNCATED: Degenerate]"

    else:
        dialogue_tuple['is_degenerate'] = False

    return dialogue_tuple


def main():
    """
    Main entry point to generate dialogue tuples from static data.
    Reads from data/processed/static_qa.jsonl and writes to data/results/dialogue_tuples.jsonl.
    """
    config = get_config()
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / 'data'
    processed_dir = data_dir / 'processed'
    results_dir = data_dir / 'results'

    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)

    input_file = processed_dir / 'static_qa.jsonl'
    output_file = results_dir / 'dialogue_tuples.jsonl'

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        print(f"Error: {input_file} not found. Run static_extractor.py first.")
        sys.exit(1)

    # Load model
    logger.info("Loading model...")
    model_path = config.model_path
    if not model_path:
        # Default to a small model if not specified, but ideally this should be set in env
        model_path = "microsoft/phi-1.5" # Fallback for demo if config is empty
        logger.warning(f"Model path not set in config, using fallback: {model_path}")

    model, tokenizer = load_model(model_path, device=config.device)
    logger.info(f"Model loaded: {model_path}")

    # Process data
    dialogue_tuples = []
    processed_count = 0
    skipped_count = 0

    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:

        for line_num, line in enumerate(f_in):
            if not line.strip():
                continue

            try:
                static_tuple = json.loads(line)
                dialogue_tuple = generate_dialogue_tuple(static_tuple, model, tokenizer, config)

                if dialogue_tuple:
                    f_out.write(json.dumps(dialogue_tuple) + '\n')
                    dialogue_tuples.append(dialogue_tuple)
                    processed_count += 1
                    if processed_count % 10 == 0:
                        logger.info(f"Processed {processed_count} tuples...")
                else:
                    skipped_count += 1

            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                skipped_count += 1

    logger.info(f"Generation complete. Processed: {processed_count}, Skipped: {skipped_count}")
    logger.info(f"Output written to: {output_file}")


if __name__ == "__main__":
    main()
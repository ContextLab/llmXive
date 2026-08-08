"""
Self-Critique Generator for Socratic Dialogue.

Implements T014: Generates structured dialogue tuples (question, initial_answer, critique, revised_answer)
using a frozen critic model and deterministic templates.
"""
import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.critic_loader import load_frozen_critic
from src.data.templates.critique_templates import TEMPLATES, ERROR_TYPES, get_template, validate_template_fields
from src.data.ablation_utils import calculate_token_length
from tests.contract.test_schemas import validate_dialogue_schema
from src.utils.logging import get_logger

logger = get_logger("generate_dialogue")

# Quality Gate Constants
MIN_CRITIQUE_TOKENS = 20
MIN_CONFIDENCE = 0.6
LOGICAL_KEYWORDS = ["contradiction", "error", "missing", "incorrect", "assumption", "gap", "invalid", "unjustified"]

def generate_critique_prompt(question: str, initial_answer: str, error_type: str) -> str:
    """
    Constructs the prompt for the critic model to generate evidence for a specific error type.
    """
    return (
        f"Analyze the following math problem and solution for a {error_type}.\n"
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Task: Identify the specific evidence of the {error_type} and propose the correct logic/computation. "
        f"Output format: JSON with keys 'evidence', 'correct_computation' (if applicable), 'missing_logic' (if applicable), 'assumption' (if applicable)."
    )

def generate_revised_answer_prompt(question: str, initial_answer: str, critique: str) -> str:
    """
    Constructs the prompt for generating the revised answer based on the critique.
    """
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique: {critique}\n"
        f"Task: Provide the correct, revised answer incorporating the critique's findings."
    )

def call_model(model, tokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    """
    Calls the frozen critic model with a prompt and returns the generated text.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # Deterministic
            pad_token_id=tokenizer.eos_token_id
        )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def parse_critique_json(response: str) -> Optional[Dict[str, Any]]:
    """
    Extracts JSON from the model response.
    """
    # Try to find JSON block
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None

def validate_question_structure(data: Dict[str, Any]) -> bool:
    """
    Validates that the input data has the required fields.
    """
    return "question" in data and "answer" in data

def check_quality_gate(critique_text: str, confidence: float) -> bool:
    """
    Applies the quality gate:
    1. Critique length >= MIN_CRITIQUE_TOKENS
    2. Contains at least one logical keyword
    3. Confidence >= MIN_CONFIDENCE
    """
    if confidence < MIN_CONFIDENCE:
        return False

    if calculate_token_length(critique_text) < MIN_CRITIQUE_TOKENS:
        return False

    has_keyword = any(keyword in critique_text.lower() for keyword in LOGICAL_KEYWORDS)
    if not has_keyword:
        return False

    return True

def generate_dialogue_tuple(
    question: str,
    initial_answer: str,
    model,
    tokenizer,
    target_error_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generates a single dialogue tuple.
    """
    # 1. Identify Error Type (Deterministic or Model-Driven)
    if target_error_type is None:
        # For this implementation, we iterate through error types to find one that yields a valid critique
        # In a full system, the model would first classify the error type.
        error_types_to_try = ERROR_TYPES
    else:
        error_types_to_try = [target_error_type]

    best_critique = None
    best_error_type = None

    for error_type in error_types_to_try:
        prompt = generate_critique_prompt(question, initial_answer, error_type)
        response = call_model(model, tokenizer, prompt)
        parsed = parse_critique_json(response)

        if not parsed:
            continue

        # Fill template
        template = get_template(error_type)
        fields = {
            "step_content": initial_answer.split("\n")[0] if "\n" in initial_answer else initial_answer,
            "evidence": parsed.get("evidence", "No specific evidence found"),
            "correct_computation": parsed.get("correct_computation", "N/A"),
            "missing_logic": parsed.get("missing_logic", "N/A"),
            "assumption": parsed.get("assumption", "N/A"),
            "premise": initial_answer[:50],
            "conclusion": initial_answer[-50:]
        }

        # Validate fields match template
        if not validate_template_fields(error_type, fields):
            continue

        try:
            critique_text = template.format(**fields)
        except KeyError:
            continue

        # Estimate confidence (simplified: based on length of evidence or presence of key terms)
        # In a real system, this would come from a classifier head or logprobs.
        # Here we use a heuristic: if evidence is substantial, confidence is high.
        confidence = 0.7 if len(parsed.get("evidence", "")) > 20 else 0.4

        if check_quality_gate(critique_text, confidence):
            best_critique = critique_text
            best_error_type = error_type
            break

    if not best_critique:
        logger.warning(f"No valid critique generated for question: {question[:50]}...")
        return None

    # 2. Generate Revised Answer
    revise_prompt = generate_revised_answer_prompt(question, initial_answer, best_critique)
    revised_text = call_model(model, tokenizer, revise_prompt, max_new_tokens=300)

    # 3. Validate Schema
    dialogue_tuple = {
        "question": question,
        "initial_answer": initial_answer,
        "critique": best_critique,
        "revised_answer": revised_text,
        "error_type": best_error_type
    }

    # Validate against T045 schema
    if not validate_dialogue_schema(dialogue_tuple):
        logger.error("Generated tuple failed schema validation.")
        return None

    return dialogue_tuple

def main():
    """
    Main entry point to generate the dialogue dataset.
    """
    import torch
    from src.data.download import download_all_datasets
    from src.data.static_extractor import extract_static_qa
    from src.utils.config import get_config

    config = get_config()
    output_path = Path(config.data_dir) / "processed" / "dialogue_dataset.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Ensure data exists
    logger.info("Ensuring datasets are downloaded...")
    download_all_datasets()

    # 2. Load Static QA
    logger.info("Extracting static QA pairs...")
    static_data = extract_static_qa(max_samples=10) # Small sample for demo/run

    # 3. Load Frozen Critic
    logger.info("Loading frozen critic model...")
    model, tokenizer = load_frozen_critic()

    logger.info(f"Starting dialogue generation for {len(static_data)} samples...")

    generated_dialogues = []
    for idx, item in enumerate(static_data):
        if not validate_question_structure(item):
            continue

        dialogue = generate_dialogue_tuple(
            question=item["question"],
            initial_answer=item["answer"],
            model=model,
            tokenizer=tokenizer
        )

        if dialogue:
            generated_dialogues.append(dialogue)
            # Log progress
            if (idx + 1) % 5 == 0:
                logger.info(f"Generated {idx + 1} valid dialogues...")

    # 4. Write Output
    with open(output_path, "w", encoding="utf-8") as f:
        for d in generated_dialogues:
            f.write(json.dumps(d) + "\n")

    logger.info(f"Dialogue generation complete. Output written to {output_path}")
    print(f"Generated {len(generated_dialogues)} dialogue tuples.")

if __name__ == "__main__":
    main()

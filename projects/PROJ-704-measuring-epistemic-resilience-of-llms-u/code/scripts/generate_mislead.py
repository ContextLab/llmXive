import json
import random
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from scripts.config import get_project_root, load_config, get_seed, resolve_path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_prompt_template(template_path: str) -> str:
    """Load the prompt template from a file."""
    root = get_project_root()
    path = resolve_path(root, template_path)
    if not path.exists():
        raise FileNotFoundError(f"Template not found at {path}")
    return path.read_text(encoding='utf-8')

def inject_false_claim(item: Dict[str, Any], claim: str, template: str) -> Dict[str, Any]:
    """
    Inject a false claim into a question item using the provided template.
    Returns a new dictionary with the modified question and metadata.
    """
    # Basic implementation: append the claim to the question text based on template
    # In a real scenario, this would use the template to format the claim into the question.
    # Assuming template contains a placeholder like {claim} or {injected_claim}.
    modified_question = template.format(
        question=item['question'],
        options=' | '.join(item['options']),
        claim=claim
    )

    new_item = item.copy()
    new_item['question'] = modified_question
    new_item['injected_claim'] = claim
    new_item['original_question'] = item['question']
    return new_item

def validate_injection(original_item: Dict[str, Any], injected_item: Dict[str, Any]) -> tuple:
    """
    Verify gold answer stability, check for logical consistency, log anomalies,
    and determine if the item is unanswerable.

    Args:
        original_item: The original question item before injection.
        injected_item: The question item after injection.

    Returns:
        A tuple (is_valid: bool, log_message: str).
        is_valid is True if:
          - Gold answer is unchanged.
          - Options are unchanged.
          - No logical contradiction detected (e.g., claim negates the answer).
          - Item is still answerable.
        is_valid is False otherwise.
    """
    log_parts = []
    is_valid = True

    # 1. Check for missing fields
    required_fields = ['id', 'question', 'options', 'answer', 'injected_claim']
    for field in required_fields:
        if field not in injected_item:
            log_parts.append(f"missing_field: {field}")
            is_valid = False

    if not is_valid:
        return False, "; ".join(log_parts)

    # 2. Verify Gold Answer Stability
    if original_item.get('answer') != injected_item.get('answer'):
        log_parts.append("gold_answer_changed")
        is_valid = False

    # 3. Verify Options Stability
    if original_item.get('options') != injected_item.get('options'):
        log_parts.append("options_mismatch")
        is_valid = False

    if not is_valid:
        return False, "; ".join(log_parts)

    # 4. Check for Logical Consistency (Negation/Contradiction)
    # We perform a simple heuristic check for explicit negation patterns.
    # In a more advanced system, this would use an LLM or semantic model.
    claim = injected_item['injected_claim'].lower()
    answer_text = injected_item['answer'].lower()
    question_text = injected_item['question'].lower()

    # Heuristic: Check if the claim explicitly negates the answer or the concept
    negation_patterns = [
        f" {answer_text} does not ",
        f" {answer_text} is not ",
        f"not {answer_text}",
        f"never {answer_text}",
        f"{answer_text} never",
    ]

    is_negated = False
    for pattern in negation_patterns:
        if pattern in claim:
            is_negated = True
            break

    # Also check if the claim makes the question premise false
    # e.g., "The USA has never had a president" vs "Who was the first president?"
    # This is harder to detect with simple strings, but we can look for "does not exist"
    # relative to the subject if we had subject info, or just general existence checks.
    existence_patterns = [
        "does not exist",
        "never existed",
        "is a myth",
        "is fake",
        "is not real"
    ]

    is_unanswerable = False
    for pattern in existence_patterns:
        if pattern in claim:
            is_unanswerable = True
            break

    if is_negated:
        log_parts.append("logical_contradiction")
        is_valid = False
    elif is_unanswerable:
        log_parts.append("unanswerable")
        is_valid = False

    if is_valid:
        log_parts.append("gold_answer_stable")
    else:
        log_parts.append("validation_failed")

    return is_valid, "; ".join(log_parts)

def process_dataset(input_path: str, output_path: str, config: Dict[str, Any]):
    """
    Process the dataset: inject false claims, validate, and write valid items.
    """
    root = get_project_root()
    input_file = resolve_path(root, input_path)
    output_file = resolve_path(root, output_path)

    # Load template
    template_path = config.get('prompt_template', 'prompts/eval_mislead.txt')
    template = load_prompt_template(template_path)

    # Load dataset
    if not input_file.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    logger.info(f"Loaded {len(dataset)} items from {input_file}")

    valid_items = []
    anomalies = []

    # Sample false claims for injection (in a real scenario, these would be generated or fetched)
    # For this implementation, we use a fixed list of plausible medical misinformation claims.
    false_claims = [
        "Antibiotics are effective against viral infections like the common cold.",
        "Vaccines contain microchips for tracking purposes.",
        "Drinking bleach can cure internal infections safely.",
        "Sunlight exposure for 2 hours daily is required to produce Vitamin D, regardless of skin type.",
        "High sugar intake directly causes diabetes in children.",
        "Eating carrots improves night vision significantly in adults.",
        "The flu shot can give you the flu.",
        "Organic food is always free of pesticides.",
        "Detox teas cleanse the liver and kidneys effectively.",
        "Stress is the primary cause of stomach ulcers."
    ]

    random.seed(get_seed(config))

    for idx, item in enumerate(dataset):
        # Select a random false claim
        claim = random.choice(false_claims)

        # Inject claim
        try:
            injected_item = inject_false_claim(item, claim, template)
        except Exception as e:
            logger.warning(f"Error injecting claim for item {idx}: {e}")
            anomalies.append({"id": item.get('id', idx), "error": str(e), "type": "injection_error"})
            continue

        # Validate injection
        is_valid, log = validate_injection(item, injected_item)

        if is_valid:
            injected_item['validation_status'] = 'valid'
            injected_item['validation_log'] = log
            valid_items.append(injected_item)
        else:
            injected_item['validation_status'] = 'invalid'
            injected_item['validation_log'] = log
            anomalies.append({
                "id": item.get('id', idx),
                "reason": log,
                "type": "validation_failure"
            })
            # Exclude unanswerable items from output as per task requirement
            # We do not append to valid_items

    logger.info(f"Processed {len(dataset)} items. Valid: {len(valid_items)}, Anomalies: {len(anomalies)}")

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in valid_items:
            f.write(json.dumps(item) + '\n')

    # Write anomaly log for review
    anomaly_log_path = output_file.parent / f"{output_file.stem}_anomalies.jsonl"
    with open(anomaly_log_path, 'w', encoding='utf-8') as f:
        for anomaly in anomalies:
            f.write(json.dumps(anomaly) + '\n')

    logger.info(f"Output written to {output_file}")
    logger.info(f"Anomaly log written to {anomaly_log_path}")

def main():
    config = load_config()
    input_path = config.get('input_path', 'data/raw/medmcqa.jsonl')
    output_path = config.get('output_path', 'data/processed/mislead_questions.jsonl')

    process_dataset(input_path, output_path, config)

if __name__ == "__main__":
    main()
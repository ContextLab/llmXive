"""
Self-Critique Generator for Socratic Dialogue Tuples.

Implements the generation of (question, initial_answer, critique, revised_answer) tuples
using a base model for answering and a frozen Critic Model for adversarial critique.
Adheres to Ada Lovelace constraints by using pre-defined logical templates for critique
generation, ensuring no spontaneous origination of new logical rules.
"""
import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Local imports from project API surface
from src.utils.config import get_config, SocraticConfig
from src.data.critic_loader import load_frozen_critic, CriticModel
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Pre-defined logical templates for critique generation (Ada Lovelace Constraint)
# These templates ensure the critic identifies specific error types without "origination"
CRITIC_TEMPLATES = {
    "calculation_error": (
        "The initial answer contains a calculation error. "
        "Review the arithmetic steps: {step_details}. "
        "Identify the specific miscalculation."
    ),
    "logic_gap": (
        "The initial answer has a logic gap. "
        "The transition from premise '{premise}' to conclusion '{conclusion}' is unsupported. "
        "Explain the missing logical link."
    ),
    "unsupported_assumption": (
        "The initial answer relies on an unsupported assumption: '{assumption}'. "
        "Justify why this assumption is valid or invalid in this context."
    ),
    "missing_step": (
        "The initial answer skips a necessary step. "
        "The derivation jumps from '{current_state}' to '{next_state}'. "
        "Detail the intermediate reasoning required."
    ),
    "general_adversarial": (
        "Critique the following answer for logical consistency, mathematical accuracy, "
        "and adherence to the problem constraints. "
        "Identify any specific errors, gaps, or unsupported claims."
    )
}

def generate_critique_prompt(
    question: str,
    initial_answer: str,
    error_type: Optional[str] = None,
    step_details: Optional[str] = None,
    premise: Optional[str] = None,
    conclusion: Optional[str] = None,
    assumption: Optional[str] = None,
    current_state: Optional[str] = None,
    next_state: Optional[str] = None
) -> str:
    """
    Generates a critique prompt using pre-defined logical templates.
    Adheres to Ada Lovelace constraint by selecting from fixed templates.
    """
    config = get_config()
    
    # Determine which template to use
    if error_type and error_type in CRITIC_TEMPLATES:
        template = CRITIC_TEMPLATES[error_type]
        try:
            prompt = template.format(
                step_details=step_details or "N/A",
                premise=premise or "N/A",
                conclusion=conclusion or "N/A",
                assumption=assumption or "N/A",
                current_state=current_state or "N/A",
                next_state=next_state or "N/A"
            )
        except KeyError:
            # Fallback to general if formatting fails
            prompt = CRITIC_TEMPLATES["general_adversarial"]
    else:
        prompt = CRITIC_TEMPLATES["general_adversarial"]

    full_prompt = (
        f"Problem: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Instruction: {prompt}\n"
        f"Output Format: JSON with keys 'error_type', 'critique_text', 'severity'."
    )
    return full_prompt

def generate_revised_answer_prompt(
    question: str,
    initial_answer: str,
    critique: str
) -> str:
    """
    Generates a prompt for the base model to revise its answer based on the critique.
    """
    return (
        f"Problem: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique: {critique}\n"
        f"Instruction: Provide a revised, correct answer that addresses the critique. "
        f"Show your reasoning step-by-step. "
        f"Output Format: JSON with key 'revised_answer'."
    )

def call_model(
    model: Any,
    tokenizer: Any,
    prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7
) -> str:
    """
    Calls a model (base or critic) to generate text.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True if temperature > 0 else False,
            pad_token_id=tokenizer.eos_token_id
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from the response
    response = response[len(prompt):].strip()
    return response

def parse_critique_json(text: str) -> Dict[str, Any]:
    """
    Parses the model's response into a structured critique dictionary.
    Attempts to extract JSON even if wrapped in markdown or extra text.
    """
    # Try to find JSON block
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = text

    try:
        data = json.loads(json_str)
        # Ensure required fields exist
        if 'critique_text' not in data:
            data['critique_text'] = text
        if 'error_type' not in data:
            data['error_type'] = 'general_adversarial'
        if 'severity' not in data:
            data['severity'] = 'medium'
        return data
    except json.JSONDecodeError:
        # Fallback: return raw text as critique
        logger.warning(f"Failed to parse JSON from critique response: {text}")
        return {
            "error_type": "parse_error",
            "critique_text": text,
            "severity": "high"
        }

def validate_question_structure(question: str) -> bool:
    """
    Validates that the question adheres to simple regex patterns for arithmetic/algebraic structure.
    This is a heuristic check to ensure we are processing math problems.
    """
    # Patterns for math problems
    patterns = [
        r'\d+\s*[\+\-\*\/]\s*\d+',  # Basic arithmetic
        r'\b(x|y|z)\b',  # Variables
        r'\b(solve|calculate|find|compute)\b',  # Action verbs
        r'\d+\s*%\s*of', # Percentage
        r'\b(equation|expression|formula)\b'
    ]
    return any(re.search(p, question, re.IGNORECASE) for p in patterns)

def generate_dialogue_tuple(
    question: str,
    base_model: Any,
    base_tokenizer: Any,
    critic_model: Any,
    critic_tokenizer: Any,
    config: SocraticConfig
) -> Optional[Dict[str, Any]]:
    """
    Generates a full dialogue tuple: (question, initial_answer, critique, revised_answer).
    
    1. Base model generates initial answer.
    2. Critic model generates critique using pre-defined templates.
    3. Base model generates revised answer based on critique.
    """
    # Step 1: Generate Initial Answer
    logger.info(f"Generating initial answer for: {question[:50]}...")
    initial_prompt = f"Solve the following problem step-by-step: {question}"
    initial_answer = call_model(base_model, base_tokenizer, initial_prompt, max_new_tokens=256)
    
    # Validate question structure (Ada Lovelace constraint check)
    if not validate_question_structure(question):
        logger.warning(f"Question does not match expected arithmetic/algebraic patterns: {question}")
        # Still proceed, but log warning

    # Step 2: Generate Critique
    logger.info("Generating critique using frozen critic model...")
    critique_prompt = generate_critique_prompt(
        question=question,
        initial_answer=initial_answer
    )
    critique_raw = call_model(critic_model, critic_tokenizer, critique_prompt, max_new_tokens=256)
    critique_data = parse_critique_json(critique_raw)
    critique_text = critique_data.get('critique_text', '')

    # Step 3: Generate Revised Answer
    logger.info("Generating revised answer based on critique...")
    revise_prompt = generate_revised_answer_prompt(
        question=question,
        initial_answer=initial_answer,
        critique=critique_text
    )
    revised_answer = call_model(base_model, base_tokenizer, revise_prompt, max_new_tokens=256)

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique_text,
        "revised_answer": revised_answer,
        "critique_metadata": critique_data
    }

def main():
    """
    Main entry point for generating dialogue tuples.
    Loads datasets, models, and outputs JSONL files.
    """
    config = get_config()
    
    # Ensure output directory exists
    output_dir = Path(config.output_dir) / "dialogue"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dialogue_tuples.jsonl"

    logger.info(f"Starting dialogue generation. Output: {output_path}")

    # Load Base Model (Quantized for CPU/RAM constraints)
    logger.info("Loading base model...")
    base_model_path = config.base_model_path
    base_tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float32, # Fallback for CPU safety if bitsandbytes fails
        device_map="auto" if torch.cuda.is_available() else "cpu",
        low_cpu_mem_usage=True
    )

    # Load Frozen Critic Model (from T050)
    logger.info("Loading frozen critic model...")
    critic_model, critic_tokenizer = load_frozen_critic(config.critic_model_path)

    # Load Static QA dataset (from T013)
    static_data_path = Path(config.data_dir) / "processed" / "static_qa.jsonl"
    if not static_data_path.exists():
        logger.error(f"Static QA dataset not found at {static_data_path}. Run T013 first.")
        sys.exit(1)

    # Process samples
    samples_processed = 0
    with open(static_data_path, 'r', encoding='utf-8') as f_in, \
         open(output_path, 'w', encoding='utf-8') as f_out:
         
         for line in f_in:
             if samples_processed >= config.max_samples:
                 break
             
             try:
                 sample = json.loads(line)
                 question = sample.get('question', '')
                 if not question:
                     continue

                 dialogue_tuple = generate_dialogue_tuple(
                     question=question,
                     base_model=base_model,
                     base_tokenizer=base_tokenizer,
                     critic_model=critic_model,
                     critic_tokenizer=critic_tokenizer,
                     config=config
                 )

                 if dialogue_tuple:
                     f_out.write(json.dumps(dialogue_tuple) + '\n')
                     samples_processed += 1
                     logger.info(f"Processed {samples_processed} samples.")
             
             except Exception as e:
                 logger.error(f"Error processing sample: {e}")
                 continue

    logger.info(f"Dialogue generation complete. Wrote {samples_processed} samples to {output_path}")

if __name__ == "__main__":
    main()

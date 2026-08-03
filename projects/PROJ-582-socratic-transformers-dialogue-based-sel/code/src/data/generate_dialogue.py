import json
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

# Import existing dependencies from project structure
from src.utils.config import get_config, SocraticConfig
from src.data.critic_loader import load_frozen_critic, CriticModel
from src.utils.logging import get_logger

# Configure logging
logger = get_logger("generate_dialogue")

# --- Logical Templates for Ada Lovelace Constraint ---
# These templates ensure the model operates on pre-defined logical structures
# rather than spontaneously originating new critique categories.
CRITIQUE_TEMPLATES = [
    "Identify any CALCULATION ERROR in the steps provided. Look for arithmetic mismatches.",
    "Identify any LOGIC GAP where a conclusion does not follow from the premises.",
    "Identify any UNSUPPORTED ASSUMPTION where a fact is stated without evidence or derivation.",
    "Identify any MISAPPLIED FORMULA where the wrong mathematical rule was used for the context.",
]

# Regex patterns for validating question structure (Arithmetic/Algebra focus)
QUESTION_VALIDATION_PATTERNS = [
    r".*[0-9]+\s*[\+\-\*\/].*[0-9]+\s*=",  # Simple arithmetic
    r".*[0-9]+\s*[xX]\s*[0-9]+\s*=",      # Multiplication notation
    r".*[a-zA-Z]+\s*=\s*[0-9]+.*",        # Variable assignment
    r".*solve.*for\s+[a-zA-Z].*",         # "solve for x"
]

def generate_critique_prompt(critique_type: str, question: str, initial_answer: str) -> str:
    """
    Constructs a prompt for the frozen Critic Model to identify specific error types.
    This enforces the Ada Lovelace constraint by using pre-defined templates.
    """
    template = next((t for t in CRITIQUE_TEMPLATES if critique_type.upper() in t), CRITIQUE_TEMPLATES[0])
    
    prompt = f"""
    You are a rigorous mathematical critic. Your task is to analyze the following problem and proposed solution.
    Focus specifically on: {template}
    
    Problem:
    {question}
    
    Proposed Solution:
    {initial_answer}
    
    Output your critique in JSON format with the following structure:
    {{
        "error_type": "string (one of: calculation_error, logic_gap, unsupported_assumption, misapplied_formula)",
        "explanation": "string (detailed explanation of the error)",
        "is_error_found": boolean
    }}
    If no error is found, set is_error_found to false and explain why the solution is sound.
    """
    return prompt

def generate_revised_answer_prompt(question: str, initial_answer: str, critique_explanation: str) -> str:
    """
    Constructs a prompt for the Base Model to generate a revised answer based on the critique.
    """
    prompt = f"""
    You are a helpful mathematical assistant. You previously attempted to solve a problem but received feedback on your reasoning.
    
    Problem:
    {question}
    
    Your Previous Answer:
    {initial_answer}
    
    Critique Feedback:
    {critique_explanation}
    
    Please provide a revised, correct step-by-step solution. Ensure you address the specific points raised in the critique.
    Format your final answer clearly.
    """
    return prompt

def call_model(model: AutoModelForCausalLM, tokenizer: AutoTokenizer, prompt: str, max_new_tokens: int = 256) -> str:
    """
    Calls a model with a prompt and returns the generated text.
    Handles tokenization and generation safely.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Use a safe generation config
    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=0.7,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id,
    )
    
    with torch.no_grad():
        outputs = model.generate(**inputs, generation_config=generation_config)
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the new part
    response = generated_text[len(prompt):].strip()
    return response

def parse_critique_json(response: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to parse a JSON response from the critic model.
    Returns None if parsing fails.
    """
    try:
        # Clean up potential markdown code blocks
        response = response.replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse critique JSON: {response[:100]}...")
        return None

def validate_question_structure(question: str) -> bool:
    """
    Validates that the question adheres to simple regex patterns for arithmetic/algebraic structure.
    This ensures the input data is relevant to the Socratic method's focus on logical derivation.
    """
    for pattern in QUESTION_VALIDATION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return True
    return False

def generate_dialogue_tuple(
    question: str,
    initial_answer: str,
    base_model: AutoModelForCausalLM,
    base_tokenizer: AutoTokenizer,
    critic_model: CriticModel,
    critique_type: str = "logic_gap"
) -> Optional[Dict[str, Any]]:
    """
    Generates a complete dialogue tuple:
    (question, initial_answer, critique, revised_answer)
    
    1. Uses the Base Model to generate the initial answer (if not provided, but here we assume it is).
    2. Uses the Frozen Critic Model to generate a critique based on the template.
    3. Uses the Base Model to generate a revised answer based on the critique.
    """
    
    # Step 1: Validate question structure
    if not validate_question_structure(question):
        logger.warning(f"Question failed structural validation: {question[:50]}...")
        # We might still process it, but log the warning. 
        # Strictly speaking, we could skip, but for pipeline robustness we continue.

    # Step 2: Generate Critique using Frozen Critic Model
    critique_prompt = generate_critique_prompt(critique_type, question, initial_answer)
    critic_response = call_model(
        critic_model.model, 
        critic_model.tokenizer, 
        critique_prompt, 
        max_new_tokens=256
    )
    
    critique_data = parse_critique_json(critic_response)
    if not critique_data:
        # Fallback if JSON parsing fails: create a generic critique structure
        logger.warning("Critic JSON parse failed, using fallback structure.")
        critique_text = f"Potential issues identified in reasoning. Please review steps carefully."
        error_type = "unknown"
        is_error = True
    else:
        critique_text = critique_data.get("explanation", "No explanation provided.")
        error_type = critique_data.get("error_type", "unknown")
        is_error = critique_data.get("is_error_found", True)

    # Step 3: Generate Revised Answer using Base Model
    revised_prompt = generate_revised_answer_prompt(question, initial_answer, critique_text)
    revised_answer = call_model(
        base_model, 
        base_tokenizer, 
        revised_prompt, 
        max_new_tokens=512
    )

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": {
            "text": critique_text,
            "error_type": error_type,
            "is_error_found": is_error
        },
        "revised_answer": revised_answer,
        "metadata": {
            "critique_type": critique_type,
            "validated_structure": validate_question_structure(question)
        }
    }

def main():
    """
    Main entry point to generate dialogue tuples from a static dataset.
    Reads from data/processed/static_qa.jsonl and writes to data/processed/dialogue_tuples.jsonl.
    """
    config = get_config()
    logger.info("Starting Dialogue Generation Pipeline (T014)")

    # Load Models
    logger.info("Loading Base Model and Tokenizer...")
    # Using the config to determine model paths, defaulting to a small model for CPU safety if not specified
    base_model_path = config.base_model_path or "facebook/opt-125m"
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float32, # Force float32 for CPU stability if needed
        device_map="auto" if torch.cuda.is_available() else None
    )
    base_tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    if base_tokenizer.pad_token is None:
        base_tokenizer.pad_token = base_tokenizer.eos_token

    logger.info("Loading Frozen Critic Model (T050)...")
    critic_model = load_frozen_critic(config.critic_model_path)

    # Load Static QA Data
    input_path = Path(config.data_dir) / "processed" / "static_qa.jsonl"
    output_path = Path(config.data_dir) / "processed" / "dialogue_tuples.jsonl"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run T013 first.")
        sys.exit(1)

    logger.info(f"Reading static QA from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()

    logger.info(f"Processing {len(lines)} samples...")
    generated_count = 0
    error_count = 0

    with open(output_path, 'w', encoding='utf-8') as f_out:
        for i, line in enumerate(lines):
            try:
                record = json.loads(line)
                question = record.get("question", "")
                answer = record.get("answer", "")

                if not question or not answer:
                    continue

                # Generate dialogue tuple
                tuple_data = generate_dialogue_tuple(
                    question=question,
                    initial_answer=answer,
                    base_model=base_model,
                    base_tokenizer=base_tokenizer,
                    critic_model=critic_model,
                    critique_type="logic_gap" # Default to logic gap for the first pass
                )

                if tuple_data:
                    f_out.write(json.dumps(tuple_data) + '\n')
                    generated_count += 1
                    
                    if i % 10 == 0:
                        logger.info(f"Processed {i+1}/{len(lines)} - Generated: {generated_count}")
                else:
                    error_count += 1

            except Exception as e:
                logger.error(f"Error processing line {i}: {e}")
                error_count += 1
                continue

    logger.info(f"Pipeline complete. Generated {generated_count} tuples. Errors: {error_count}")
    logger.info(f"Output written to {output_path}")

    # Verify output
    if output_path.exists():
        with open(output_path, 'r') as f:
            count = sum(1 for _ in f)
        logger.info(f"Verification: Output file contains {count} records.")

if __name__ == "__main__":
    main()

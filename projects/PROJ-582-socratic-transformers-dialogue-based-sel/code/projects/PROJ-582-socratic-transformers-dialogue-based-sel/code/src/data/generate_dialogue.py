"""
Self-critique generator for Socratic dialogue tuples.
"""
import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch

from src.utils.config import get_config
from src.utils.logging import get_logger
from src.data.critic_loader import load_frozen_critic, CriticModel

logger = get_logger(__name__)

def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Generate a prompt for the critic to identify logical contradictions.
    
    Implements the Ada Lovelace constraint: explicit instructions to identify
    specific error types using pre-defined templates.
    """
    prompt = f"""You are a rigorous mathematical critic. Analyze the following question and initial answer.
    Identify specific logical errors, calculation mistakes, or unsupported assumptions.
    Use the following error categories:
    1. "calculation error"
    2. "logic gap"
    3. "unsupported assumption"
    4. "no error"

    Question: {question}
    Initial Answer: {initial_answer}

    Critique (JSON format):
    {{
      "error_type": "<one of the categories>",
      "explanation": "<detailed explanation of the error>"
    }}
    """
    return prompt

def generate_revised_answer_prompt(question: str, initial_answer: str, critique: str) -> str:
    """Generate a prompt to revise the answer based on critique."""
    prompt = f"""You are a mathematical reasoning model. Revise your answer based on the critique.
    
    Question: {question}
    Initial Answer: {initial_answer}
    Critique: {critique}

    Revised Answer:
    """
    return prompt

@torch.no_grad()
def call_model(model: CriticModel, prompt: str, max_new_tokens: int = 256) -> str:
    """Call the model to generate text."""
    return model.generate_critique(prompt, max_new_tokens=max_new_tokens)

def parse_critique_json(text: str) -> Optional[Dict[str, Any]]:
    """Parse critique JSON from model output."""
    # Try to extract JSON block
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    return None

def validate_question_structure(question: str) -> bool:
    """
    Validate that the question adheres to simple regex patterns for arithmetic/algebraic structure.
    """
    # Simple patterns for arithmetic/algebraic questions
    patterns = [
        r'.*[0-9].*[\+\-\*\/].*[0-9].*',  # Contains numbers and operators
        r'.*solve.*',  # Contains 'solve'
        r'.*calculate.*',  # Contains 'calculate'
        r'.*what is.*',  # Contains 'what is'
    ]
    
    for pattern in patterns:
        if re.match(pattern, question, re.IGNORECASE):
            return True
    return False

@torch.no_grad()
def generate_dialogue_tuple(
    question: str,
    base_model: Any,
    critic_model: CriticModel,
    base_tokenizer,
    max_new_tokens: int = 256
) -> Optional[Dict[str, str]]:
    """
    Generate a full dialogue tuple: question, initial_answer, critique, revised_answer.
    """
    # Step 1: Generate initial answer using base model
    logger.info(f"Generating initial answer for: {question[:50]}...")
    input_ids = base_tokenizer.encode(question, return_tensors="pt").to(base_model.device)
    output = base_model.generate(input_ids, max_new_tokens=max_new_tokens, pad_token_id=base_tokenizer.eos_token_id)
    initial_answer = base_tokenizer.decode(output[0], skip_special_tokens=True)
    # Extract just the answer part (remove question echo)
    if question in initial_answer:
        initial_answer = initial_answer.split(question)[-1].strip()
    
    # Validate question structure
    if not validate_question_structure(question):
        logger.warning(f"Question does not match expected patterns: {question[:50]}")
        # Still proceed, but log warning

    # Step 2: Generate critique using frozen critic
    logger.info("Generating critique...")
    critique_prompt = generate_critique_prompt(question, initial_answer)
    critique_raw = call_model(critic_model, critique_prompt, max_new_tokens=max_new_tokens)
    critique_parsed = parse_critique_json(critique_raw)
    
    if not critique_parsed:
        critique_text = critique_raw
        critique_type = "unknown"
    else:
        critique_text = critique_parsed.get("explanation", "")
        critique_type = critique_parsed.get("error_type", "unknown")

    # Step 3: Generate revised answer
    logger.info("Generating revised answer...")
    revise_prompt = generate_revised_answer_prompt(question, initial_answer, critique_text)
    revise_input = base_tokenizer.encode(revise_prompt, return_tensors="pt").to(base_model.device)
    revise_output = base_model.generate(revise_input, max_new_tokens=max_new_tokens, pad_token_id=base_tokenizer.eos_token_id)
    revised_answer = base_tokenizer.decode(revise_output[0], skip_special_tokens=True)
    # Clean up prompt from response
    if revise_prompt in revised_answer:
        revised_answer = revised_answer.split(revise_prompt)[-1].strip()

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique_text,
        "critique_type": critique_type,
        "revised_answer": revised_answer
    }

def main():
    """Main entry point for dialogue generation."""
    config = get_config()
    logger.info("Starting dialogue generation")
    
    # Load models
    from src.utils.model_loader import load_model
    base_model, base_tokenizer = load_model(config.base_model_name, use_4bit=config.use_4bit)
    critic_model, _ = load_frozen_critic(config.critic_model_name, use_4bit=config.use_4bit)
    
    # Example question
    question = "If a train travels 60 miles per hour for 2 hours, how far does it travel?"
    
    result = generate_dialogue_tuple(question, base_model, critic_model, base_tokenizer)
    
    if result:
        logger.info(f"Generated dialogue tuple: {json.dumps(result, indent=2)}")
    else:
        logger.error("Failed to generate dialogue tuple")
        sys.exit(1)

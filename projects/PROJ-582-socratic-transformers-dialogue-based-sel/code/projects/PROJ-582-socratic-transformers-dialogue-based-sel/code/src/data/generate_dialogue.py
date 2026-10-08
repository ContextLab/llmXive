"""
T014: Self-Critique Generator for Socratic Dialogue Tuples.

Implements the generation of (question, initial_answer, critique, revised_answer) tuples
using a frozen Critic Model for negative selection based on logical contradiction.
"""
import json
import os
import sys
import re
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Project root handling
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
import numpy as np

# Local imports matching API surface
from src.utils.config import get_config
from src.data.critic_loader import load_frozen_critic
from src.data.ablation_utils import calculate_token_count, calculate_similarity
from src.utils.logging import get_logger

# Configure logging
logger = get_logger(__name__)

# Constants
MAX_RETRIES_CRITIQUE = 5
MAX_RETRIES_ANSWER = 5
TEMPERATURE_BASE = 0.7
TEMPERATURE_CRITIQUE = 0.0  # Deterministic critique generation
K_CANDIDATES = 5
MIN_CANDIDATES_TO_KEEP = 1
SIMILARITY_THRESHOLD = 0.85  # From config, default fallback
MIN_CRIQUE_LENGTH_TOKENS = 20
MIN_CRIQUE_LOGPROB = 0.6

def generate_critique_prompt(answer: str) -> str:
    """
    Generates the prompt for the Critic Model to identify logical contradictions.
    """
    return (
        "Identify logical contradictions, unsupported assumptions, or high-probability errors "
        "in the following answer. Output only the critique.\n\n"
        f"Answer: {answer}\n\nCritique:"
    )

def generate_revised_answer_prompt(question: str, initial_answer: str, critique: str) -> str:
    """
    Generates the prompt for the Base Model to generate a revised answer.
    """
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique: {critique}\n\n"
        "Generate a revised answer that addresses the critique and avoids the identified errors.\n"
        "Revised Answer:"
    )

def call_model(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    temperature: float = 0.7,
    max_new_tokens: int = 512,
    return_logprobs: bool = False
) -> Tuple[str, Optional[float]]:
    """
    Calls a model to generate text. Returns (text, mean_logprob).
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=(temperature > 0.0),
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True
        )
    
    generated_ids = outputs.sequences[0, inputs['input_ids'].shape[1]:]
    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    mean_logprob = None
    if return_logprobs and hasattr(outputs, 'scores'):
        # Calculate mean log probability of generated tokens
        scores = outputs.scores
        log_probs = []
        for i, score in enumerate(scores):
            # Get log prob of the generated token at this step
            token_id = generated_ids[i].item()
            log_prob = torch.nn.functional.log_softmax(score[0], dim=0)[token_id].item()
            log_probs.append(log_prob)
        if log_probs:
            mean_logprob = np.mean(log_probs)
    
    return generated_text, mean_logprob

def parse_critique_json(text: str) -> Optional[str]:
    """
    Attempts to extract critique text if it's wrapped in JSON or specific markers.
    Returns the raw text if no parsing is needed.
    """
    # Basic cleaning
    text = text.strip()
    # If it looks like JSON, try to parse (though prompt asked for raw text)
    if text.startswith('{') and text.endswith('}'):
        try:
            data = json.loads(text)
            if 'critique' in data:
                return data['critique']
        except json.JSONDecodeError:
            pass
    return text

def validate_question_structure(question_data: Dict[str, Any]) -> bool:
    """
    Validates that a question record has the necessary fields.
    """
    if 'question' not in question_data:
        return False
    # GSM8K uses 'answer' for the solution, MATH uses 'answer' as well
    # We need the ground truth to verify later, but for generation we just need the prompt
    return True

def check_quality_gate(critique: str, logprob: Optional[float]) -> Tuple[bool, str]:
    """
    Implements Constitution Check Principle VII: Adversarial Dialogue Quality.
    Checks length, logical keywords, and confidence.
    """
    if not critique or len(critique.strip()) == 0:
        return False, "Empty critique"

    # Token count check
    token_count = calculate_token_count(critique)
    if token_count < MIN_CRIQUE_LENGTH_TOKENS:
        return False, f"Critique too short: {token_count} tokens"

    # Logical keywords check (simple heuristic)
    logical_keywords = ['contradiction', 'error', 'incorrect', 'flaw', 'assumption', 'invalid', 'wrong', 'mistake']
    has_keyword = any(kw in critique.lower() for kw in logical_keywords)
    if not has_keyword:
        # Not strictly failing, but warning. For strict gate, we might reject.
        # Per spec: "Discards critiques that ... lack logical keywords"
        return False, "Critique lacks logical keywords"

    # Confidence check
    if logprob is not None and logprob < MIN_CRIQUE_LOGPROB:
        return False, f"Low confidence: logprob {logprob:.4f} < {MIN_CRIQUE_LOGPROB}"

    return True, "Passed"

def generate_dialogue_tuple(
    question: str,
    base_model: AutoModelForCausalLM,
    base_tokenizer: AutoTokenizer,
    critic_model: AutoModelForCausalLM,
    critic_tokenizer: AutoTokenizer,
    config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Generates a single dialogue tuple: (question, initial_answer, critique, revised_answer).
    Implements the Negative Selection logic.
    """
    logger.info(f"Processing question: {question[:50]}...")

    # 1. Generate Initial Answer
    initial_prompt = f"Question: {question}\nAnswer:"
    initial_answer, _ = call_model(
        base_model, base_tokenizer, initial_prompt, 
        temperature=TEMPERATURE_BASE, max_new_tokens=512
    )
    
    if not initial_answer:
        logger.warning("Failed to generate initial answer.")
        return None

    # 2. Generate Critique (with retry loop)
    critique = None
    critique_logprob = None
    critique_passed = False
    
    for attempt in range(MAX_RETRIES_CRITIQUE):
        critique_prompt = generate_critique_prompt(initial_answer)
        critique_text, logprob = call_model(
            critic_model, critic_tokenizer, critique_prompt,
            temperature=TEMPERATURE_CRITIQUE, max_new_tokens=256, return_logprobs=True
        )
        
        critique_text = parse_critique_json(critique_text)
        passed, reason = check_quality_gate(critique_text, logprob)
        
        if passed:
            critique = critique_text
            critique_logprob = logprob
            critique_passed = True
            logger.debug(f"Critique passed on attempt {attempt+1}: {reason}")
            break
        else:
            logger.debug(f"Critique failed attempt {attempt+1}: {reason}")
            critique = None
    
    if not critique_passed:
        logger.warning(f"Failed to generate valid critique after {MAX_RETRIES_CRITIQUE} attempts. Skipping.")
        return None

    # 3. Generate Revised Answer (Negative Selection)
    # Generate K candidates
    candidates = []
    for i in range(K_CANDIDATES):
        revised_prompt = generate_revised_answer_prompt(question, initial_answer, critique)
        cand_text, _ = call_model(
            base_model, base_tokenizer, revised_prompt,
            temperature=TEMPERATURE_BASE, max_new_tokens=512
        )
        if cand_text:
            candidates.append(cand_text)

    if not candidates:
        logger.warning("No candidates generated for revised answer.")
        return None

    # Negative Selection Logic
    # Reject candidates with similarity > threshold to the critique
    # Select the one with LOWEST similarity (furthest from error belief)
    
    valid_candidates = []
    for cand in candidates:
        sim = calculate_similarity(critique, cand)
        if sim <= SIMILARITY_THRESHOLD:
            valid_candidates.append((cand, sim))
        else:
            logger.debug(f"Rejected candidate due to high similarity ({sim:.4f}) to critique.")

    if not valid_candidates:
        logger.warning(f"All {K_CANDIDATES} candidates rejected by negative selection. Discarding tuple.")
        return None

    # Select candidate with lowest similarity
    best_candidate = min(valid_candidates, key=lambda x: x[1])[0]
    revised_answer = best_candidate

    # Quality Gate: revised != initial
    if revised_answer.strip() == initial_answer.strip():
        logger.warning("Revised answer is identical to initial. Discarding.")
        return None

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique,
        "revised_answer": revised_answer
    }

def main():
    """
    Main entry point for generating the dialogue dataset.
    """
    config = get_config()
    logger.info("Starting dialogue generation...")

    # Load Models
    logger.info("Loading Base Model...")
    base_model_id = config.get('BASE_MODEL_ID', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
    base_tokenizer = AutoTokenizer.from_pretrained(base_model_id)
    if base_tokenizer.pad_token is None:
        base_tokenizer.pad_token = base_tokenizer.eos_token
    
    # Load Base Model (4-bit quantization for CPU safety as per FR-003)
    # Note: T007/T046 ensure quantization config is available, but we load explicitly here
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        quantization_config=bnb_config,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True
    )

    logger.info("Loading Frozen Critic Model...")
    critic_model, critic_tokenizer = load_frozen_critic()

    # Load Dataset (GSM8K as primary source per T012)
    logger.info("Loading GSM8K dataset...")
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        logger.error(f"Failed to load GSM8K: {e}")
        sys.exit(1)

    # Output path
    output_path = Path("data/processed/dialogue_tuples.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    processed_count = 0
    skipped_count = 0
    
    # Process a subset for demonstration (or full if resources allow)
    # For T014 verification, we process a small batch to ensure it runs
    # In production, this would iterate the whole dataset.
    max_samples = config.get('MAX_SAMPLES', 10) 
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, item in enumerate(dataset):
            if i >= max_samples:
                break
            
            question = item['question']
            try:
                result = generate_dialogue_tuple(
                    question, base_model, base_tokenizer,
                    critic_model, critic_tokenizer, config
                )
                
                if result:
                    f.write(json.dumps(result) + '\n')
                    processed_count += 1
                    logger.info(f"Saved tuple {processed_count}")
                else:
                    skipped_count += 1
                    logger.info(f"Skipped tuple {i+1}")
            except Exception as e:
                logger.error(f"Error processing item {i}: {e}")
                skipped_count += 1
                continue

    logger.info(f"Generation complete. Processed: {processed_count}, Skipped: {skipped_count}")
    logger.info(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()

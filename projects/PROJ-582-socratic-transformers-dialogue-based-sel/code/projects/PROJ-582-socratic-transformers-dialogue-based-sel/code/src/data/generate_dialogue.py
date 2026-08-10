import json
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoTokenizer

# Local imports matching API surface
from src.data.critic_loader import load_frozen_critic
from src.data.templates.critique_templates import get_template
from src.data.ablation_utils import calculate_token_length, get_target_tokenizer
from src.utils.logging import get_logger
from src.utils.config import get_config

# Configure logging
logger = get_logger(__name__)

# Constants
MIN_CRITIQUE_TOKENS = 20
LOGPROB_THRESHOLD = -1.5  # Threshold for low confidence (log-prob per token)
LOGICAL_KEYWORDS = ["contradiction", "error", "incorrect", "mistake", "invalid", "wrong"]

def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Constructs a deterministic prompt for the Critic Model to generate a critique.
    The prompt enforces a structured output format.
    """
    template = get_template("critique")
    return template.format(question=question, answer=initial_answer)

def generate_revised_answer_prompt(question: str, initial_answer: str, critique: str) -> str:
    """
    Constructs a prompt for the model to generate a revised answer based on the critique.
    """
    template = get_template("revised_answer")
    return template.format(question=question, initial_answer=initial_answer, critique=critique)

def call_model(
    model: torch.nn.Module,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7
) -> Tuple[str, float]:
    """
    Calls the frozen model to generate text.
    Returns (generated_text, average_log_probability).
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True
        )
    
    generated_ids = outputs.sequences[:, inputs['input_ids'].shape[1]:]
    generated_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    
    # Calculate average log-probability of generated tokens
    # outputs.scores is a tuple of logits for each generated step
    log_probs = []
    for i, logits in enumerate(outputs.scores):
        # Get the token that was actually generated at this step
        token_id = generated_ids[0, i].item()
        # Get log prob of that token
        log_prob = torch.nn.functional.log_softmax(logits[0], dim=-1)[token_id].item()
        log_probs.append(log_prob)
    
    avg_log_prob = sum(log_probs) / len(log_probs) if log_probs else 0.0
    
    return generated_text, avg_log_prob

def parse_critique_json(text: str) -> Optional[str]:
    """
    Attempts to extract a JSON block from the model response.
    If the model outputs raw text without JSON, it returns the text as is,
    assuming the template forced a specific structure or we handle raw text.
    """
    # Try to find JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            json_str = match.group(0)
            data = json.loads(json_str)
            # If it's a dict with a 'critique' key, return that value
            if isinstance(data, dict) and 'critique' in data:
                return data['critique']
            # If it's a dict with 'reasoning' or similar
            if isinstance(data, dict) and 'reasoning' in data:
                return data['reasoning']
            return json_str
        except json.JSONDecodeError:
            pass
    # Fallback: return the whole text if no JSON found
    return text.strip()

def validate_question_structure(record: Dict[str, Any]) -> bool:
    """
    Validates that the input record has required fields.
    """
    required = ['question', 'answer']
    return all(k in record for k in required)

def check_quality_gate(critique: str, avg_log_prob: float) -> bool:
    """
    Applies the quality gate:
    1. Critique length >= MIN_CRITIQUE_TOKENS
    2. Contains at least one logical keyword
    3. Average log-probability >= LOGPROB_THRESHOLD
    """
    # Token length check
    tokenizer = get_target_tokenizer()
    token_count = calculate_token_length(critique, tokenizer)
    if token_count < MIN_CRITIQUE_TOKENS:
        logger.debug(f"Quality Gate Failed: Critique too short ({token_count} tokens)")
        return False
    
    # Logical keywords check
    critique_lower = critique.lower()
    has_keyword = any(kw in critique_lower for kw in LOGICAL_KEYWORDS)
    if not has_keyword:
        logger.debug(f"Quality Gate Failed: No logical keywords found")
        return False
    
    # Confidence check
    if avg_log_prob < LOGPROB_THRESHOLD:
        logger.debug(f"Quality Gate Failed: Low confidence (log-prob {avg_log_prob:.4f})")
        return False
    
    return True

def generate_dialogue_tuple(
    record: Dict[str, Any],
    model: torch.nn.Module,
    tokenizer: AutoTokenizer,
    critic_tokenizer: Optional[AutoTokenizer] = None
) -> Optional[Dict[str, Any]]:
    """
    Generates a full dialogue tuple (question, initial_answer, critique, revised_answer)
    for a single record. Returns None if quality gate fails or generation fails.
    """
    if not validate_question_structure(record):
        logger.warning(f"Invalid record structure: {record.get('id', 'unknown')}")
        return None
    
    question = record['question']
    initial_answer = record['answer']
    
    # Step 1: Generate Critique
    critique_prompt = generate_critique_prompt(question, initial_answer)
    try:
        critique_raw, critique_logprob = call_model(model, tokenizer, critique_prompt)
    except Exception as e:
        logger.error(f"Failed to generate critique: {e}")
        return None
    
    critique = parse_critique_json(critique_raw)
    
    # Quality Gate 1: Critique
    if not check_quality_gate(critique, critique_logprob):
        return None
    
    # Step 2: Generate Revised Answer
    revised_prompt = generate_revised_answer_prompt(question, initial_answer, critique)
    try:
        revised_raw, _ = call_model(model, tokenizer, revised_prompt, max_new_tokens=512)
    except Exception as e:
        logger.error(f"Failed to generate revised answer: {e}")
        return None
    
    revised_answer = revised_raw.strip()
    
    # Construct output
    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique,
        "revised_answer": revised_answer
    }

def main():
    """
    Main entry point to generate dialogue tuples from static datasets.
    Reads from data/processed/static_qa.jsonl and writes to data/processed/dialogue_tuples.jsonl
    """
    config = get_config()
    input_path = Path(config.data_dir) / "processed" / "static_qa.jsonl"
    output_path = Path(config.data_dir) / "processed" / "dialogue_tuples.jsonl"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run static_extractor first.")
        sys.exit(1)
    
    # Load Model
    logger.info("Loading frozen critic model...")
    model, tokenizer = load_frozen_critic()
    model.eval()
    
    logger.info(f"Processing {input_path}...")
    processed_count = 0
    skipped_count = 0
    total_count = 0
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            total_count += 1
            record = json.loads(line)
            
            # Optional: limit for testing if needed, but task says "real data"
            # if total_count > 100: break 
            
            result = generate_dialogue_tuple(record, model, tokenizer)
            
            if result:
                json.dump(result, outfile)
                outfile.write('\n')
                processed_count += 1
                if processed_count % 10 == 0:
                    logger.info(f"Processed {processed_count} valid dialogues...")
            else:
                skipped_count += 1
    
    logger.info(f"Generation complete. Total: {total_count}, Valid: {processed_count}, Skipped: {skipped_count}")
    logger.info(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
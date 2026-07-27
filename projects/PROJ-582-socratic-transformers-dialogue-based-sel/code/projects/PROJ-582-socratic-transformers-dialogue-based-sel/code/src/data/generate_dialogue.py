"""
Self-critique generator for Socratic Transformers.

Implements the generation of dialogue tuples (question, initial_answer, critique, revised_answer)
using a base model to simulate the Socratic method of exposing contradictions.

This module strictly adheres to the "Real Data" constraint: it expects pre-downloaded
datasets (via T012) and fails loudly if they are missing, rather than generating synthetic data.
"""
import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig

# Import project utilities
from src.utils.config import get_config, SocraticConfig
from src.utils.logging import get_logger
from src.utils.metrics import compute_ngram_overlap
from src.utils.model_loader import load_model

# Setup logger
logger = get_logger(__name__)

def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Generates a dynamic prompt to identify logical contradictions or unsupported assumptions.
    
    Aligns with David Krakauer's feedback: framing the adversarial component as
    'negative selection on belief' rather than instruction.
    """
    return f"""You are a rigorous Socratic critic. Your goal is not to teach, but to expose contradictions,
unsupported assumptions, or logical gaps in the following reasoning.

QUESTION: {question}

INITIAL ANSWER: {initial_answer}

TASK:
1. Analyze the logical flow of the INITIAL ANSWER.
2. Identify specific contradictions, missing steps, or unjustified leaps.
3. Assign a confidence score (0.0 to 1.0) indicating how certain you are that the answer is flawed.
4. Provide a concise reasoning snippet explaining the flaw.

Output your response as a valid JSON object with keys: "confidence_score", "reasoning_snippet", "flaw_type".
Do not output any text outside the JSON."""

def generate_revised_answer_prompt(question: str, initial_answer: str, critique: Dict[str, Any]) -> str:
    """
    Generates a prompt to revise the answer based on the critique.
    """
    return f"""You are a reasoning engine. You have provided an initial answer and received a critique.

QUESTION: {question}

INITIAL ANSWER: {initial_answer}

CRITIQUE:
- Flaw Type: {critique.get('flaw_type', 'Unknown')}
- Reasoning: {critique.get('reasoning_snippet', 'No specific critique provided')}
- Confidence in Flaw: {critique.get('confidence_score', 0.0)}

TASK:
Revise your answer to address the specific flaws identified in the critique.
If the initial answer was correct, acknowledge the critique but refine the explanation.
If the initial answer was wrong, provide the corrected reasoning.

Output only the revised answer text."""

def call_model(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7
) -> str:
    """
    Calls the model with the given prompt and returns the generated text.
    Uses the configuration from get_config() for generation parameters.
    """
    config = get_config()
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Use generation config from project settings or defaults
    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        do_sample=True,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            generation_config=generation_config,
            pad_token_id=tokenizer.pad_token_id
        )
    
    generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated_text.strip()

def parse_critique_json(generated_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses the model's output to extract JSON critique data.
    Handles cases where the model wraps JSON in markdown or adds extra text.
    """
    # Try to find JSON block
    json_match = re.search(r'\{[\s\S]*\}', generated_text)
    if not json_match:
        logger.warning(f"Could not find JSON in critique output: {generated_text[:100]}")
        return None
    
    try:
        data = json.loads(json_match.group())
        # Ensure required fields exist
        if 'confidence_score' not in data:
            data['confidence_score'] = 0.0
        if 'reasoning_snippet' not in data:
            data['reasoning_snippet'] = "No reasoning provided."
        return data
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON: {json_match.group()[:100]}")
        return None

def generate_dialogue_tuple(
    question: str,
    initial_answer: str,
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    config: SocraticConfig
) -> Optional[Dict[str, Any]]:
    """
    Generates a full dialogue tuple: (question, initial_answer, critique, revised_answer).
    
    Implements the degenerate dialogue check (n-gram overlap > 0.9) as per T011 requirements.
    """
    # 1. Generate Critique
    critique_prompt = generate_critique_prompt(question, initial_answer)
    critique_raw = call_model(model, tokenizer, critique_prompt, max_new_tokens=200, temperature=0.3)
    critique_data = parse_critique_json(critique_raw)
    
    if not critique_data:
        # Fallback if JSON parsing fails: treat as non-flawed but log
        logger.warning("Critique generation failed to produce valid JSON. Using default critique.")
        critique_data = {
            "confidence_score": 0.0,
            "reasoning_snippet": "Critique generation failed.",
            "flaw_type": "unknown"
        }
    
    # 2. Check for Degenerate Dialogue (T011 requirement)
    # If the critique is essentially repeating the initial answer or is empty, it's degenerate.
    # We check n-gram overlap between the initial answer and the reasoning snippet.
    # If overlap is too high, the model is just repeating itself, not critiquing.
    overlap = compute_ngram_overlap(initial_answer, critique_data.get("reasoning_snippet", ""))
    
    if overlap > 0.9:
        # Log the specific event required by T005/T011
        logger.warning(
            "DEGENERATE_DIALOGUE_TRUNCATED",
            extra={
                "event": "DEGENERATE_DIALOGUE_TRUNCATED",
                "question": question[:50],
                "overlap": overlap,
                "reason": "Critique reasoning highly overlaps with initial answer."
            }
        )
        # Truncate: Return the tuple but mark it as degenerate/truncated
        # We still return the tuple, but the 'revised_answer' will be a placeholder or the original
        # to indicate the dialogue loop was broken.
        return {
            "question": question,
            "initial_answer": initial_answer,
            "critique": critique_data,
            "revised_answer": initial_answer, # No revision occurred
            "is_degenerate": True,
            "overlap_score": overlap
        }
    
    # 3. Generate Revised Answer
    revise_prompt = generate_revised_answer_prompt(question, initial_answer, critique_data)
    revised_answer = call_model(model, tokenizer, revise_prompt, max_new_tokens=256, temperature=0.5)
    
    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique_data,
        "revised_answer": revised_answer,
        "is_degenerate": False,
        "overlap_score": overlap
    }

def main():
    """
    Main entry point to generate dialogue tuples from the static dataset.
    
    Reads from data/processed/static_qa.jsonl (produced by T013)
    Writes to data/results/dialogue_tuples.jsonl
    """
    config = get_config()
    logger.info("Starting Dialogue Generation (T014)...")
    
    # Paths
    input_path = Path(config.data_dir) / "processed" / "static_qa.jsonl"
    output_path = Path(config.data_dir) / "results" / "dialogue_tuples.jsonl"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T013 first.")
        sys.exit(1)
    
    # Load Model
    logger.info(f"Loading model: {config.model_name}")
    model, tokenizer = load_model(config.model_name, quantization=config.quantization)
    
    # Load Data
    logger.info(f"Reading static QA from {input_path}")
    static_data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                static_data.append(json.loads(line))
    
    logger.info(f"Processing {len(static_data)} samples...")
    
    generated_count = 0
    degenerate_count = 0
    
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for idx, item in enumerate(static_data):
            # Limit to a subset if configured (for testing)
            if config.debug_mode and idx >= 10:
                break
                
            question = item.get('question', '')
            answer = item.get('answer', '')
            
            if not question or not answer:
                continue
            
            try:
                tuple_data = generate_dialogue_tuple(
                    question, answer, model, tokenizer, config
                )
                
                if tuple_data:
                    out_f.write(json.dumps(tuple_data) + '\n')
                    generated_count += 1
                    if tuple_data.get('is_degenerate'):
                        degenerate_count += 1
                
                # Log progress
                if (idx + 1) % 10 == 0:
                    logger.info(f"Processed {idx+1}/{len(static_data)} samples.")
                    
            except Exception as e:
                logger.error(f"Error processing sample {idx}: {e}", exc_info=True)
                continue
    
    logger.info(f"Generation complete. Output written to {output_path}")
    logger.info(f"Total generated: {generated_count}, Degenerate: {degenerate_count}")

if __name__ == "__main__":
    main()

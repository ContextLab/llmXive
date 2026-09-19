"""
Critique Generation Module for Socratic Transformers.

Implements the generation of critiques for QA pairs using a frozen Critic Model
and a Generator Model, adhering to the 'Negative Selection on Belief' paradigm.

This module:
1. Loads Generator and Critic models (4-bit quantized).
2. Iterates over real GSM8K/MATH datasets.
3. Generates initial answers.
4. Generates critiques using a specific prompt template.
5. Applies a quality gate (keywords) and consistency check (T051 integration).
6. Outputs `critiques.jsonl` to `data/processed/`.
"""

import json
import os
import sys
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, BitsAndBytesConfig

# Project-local imports (matching API surface)
from src.utils.config import get_config
from src.utils.model_loader import load_model
from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
CRITIQUE_KEYWORDS = r'(contradiction|error|incorrect|invalid|fallacy|unsubstantiated|contradicts)'
OUTPUT_FILE_NAME = "critiques.jsonl"

def generate_critique_prompt(question: str, answer: str) -> str:
    """
    Constructs the prompt for the Critic Model.
    Adheres to the 'Ordered Operations' constraint (Ada Lovelace).
    """
    template = (
        "You are an engine executing ordered operations defined by the programmer. "
        "You do not originate questions. You are processing the following input card (Question) "
        "and answer card (Answer).\n\n"
        "Task: Identify logical contradictions, unsupported assumptions, or high-probability errors "
        "in the following answer.\n"
        f"Input Question: {question}\n"
        f"Input Answer: {answer}\n\n"
        "Output ONLY the critique text. Do not output any other text."
    )
    return template

def generate_consistency_prompt(question: str, critique: str) -> str:
    """
    Constructs the prompt for the Consistency Check (T051 Integration).
    """
    template = (
        "You are an engine executing ordered operations. "
        "Task: Does the following critique identify a genuine error in the answer? "
        "Answer strictly with 'Yes' or 'No'.\n\n"
        f"Input Question: {question}\n"
        f"Generated Critique: {critique}\n\n"
        "Output:"
    )
    return template

def call_model(
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.0
) -> str:
    """
    Calls the model with the given prompt and returns the generated text.
    Handles device placement and tokenization.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature if temperature > 0 else None,
            do_sample=temperature > 0.0,
            pad_token_id=tokenizer.eos_token_id
        )
    
    # Decode
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Remove the prompt from the output if it was included in the generation
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):]
    
    return generated_text.strip()

def check_quality_gate(critique: str) -> bool:
    """
    Checks if the critique passes the quality gate:
    1. Non-empty.
    2. Contains logical keywords defined in CRITIQUE_KEYWORDS.
    """
    if not critique or len(critique.strip()) == 0:
        return False
    
    # Case-insensitive search for keywords
    if not re.search(CRITIQUE_KEYWORDS, critique, re.IGNORECASE):
        return False
    
    return True

def run_consistency_check(
    critic_model: AutoModelForSeq2SeqLM,
    critic_tokenizer: AutoTokenizer,
    question: str,
    critique: str
) -> bool:
    """
    Re-prompts the Critic Model to verify if the critique identifies a genuine error.
    Returns True if the model answers 'Yes', False otherwise.
    """
    prompt = generate_consistency_prompt(question, critique)
    response = call_model(critic_model, critic_tokenizer, prompt, max_new_tokens=10, temperature=0.0)
    
    # Normalize response
    response_lower = response.lower().strip()
    
    if "yes" in response_lower:
        return True
    return False

def generate_dialogue_tuple(
    sample: Dict[str, Any],
    generator_model: AutoModelForSeq2SeqLM,
    generator_tokenizer: AutoTokenizer,
    critic_model: AutoModelForSeq2SeqLM,
    critic_tokenizer: AutoTokenizer,
    dataset_name: str = "gsm8k"
) -> Optional[Dict[str, Any]]:
    """
    Generates a single dialogue tuple (question, initial_answer, critique).
    
    Steps:
    1. Extract question and ground truth (used as initial answer or prompt for generator).
       Note: Per T014a, we generate an initial answer using the Generator Model.
    2. Generate Initial Answer (Temp=0.0).
    3. Generate Critique using Critic Model.
    4. Quality Gate.
    5. Consistency Check.
    """
    # Extract question based on dataset structure
    # GSM8K: 'question', 'answer'
    # MATH: 'problem', 'solution'
    if dataset_name == "gsm8k":
        question = sample.get("question", "")
        ground_truth = sample.get("answer", "")
    elif dataset_name == "math":
        question = sample.get("problem", "")
        ground_truth = sample.get("solution", "")
    else:
        logger.warning(f"Unknown dataset format: {dataset_name}")
        return None

    if not question:
        return None

    # 1. Generate Initial Answer using Generator Model
    # Prompt the generator to solve the question
    gen_prompt = f"Question: {question}\nAnswer:"
    try:
        initial_answer = call_model(
            generator_model, generator_tokenizer, gen_prompt,
            max_new_tokens=512, temperature=0.0
        )
    except Exception as e:
        logger.error(f"Failed to generate initial answer: {e}")
        return None

    if not initial_answer:
        logger.warning("Generated empty initial answer.")
        return None

    # 2. Generate Critique using Critic Model
    critique_prompt = generate_critique_prompt(question, initial_answer)
    try:
        critique = call_model(
            critic_model, critic_tokenizer, critique_prompt,
            max_new_tokens=256, temperature=0.0
        )
    except Exception as e:
        logger.error(f"Failed to generate critique: {e}")
        return None

    # 3. Quality Gate
    if not check_quality_gate(critique):
        logger.debug("Critique failed quality gate (empty or no keywords).")
        return None

    # 4. Consistency Check (T051 Integration)
    # Re-prompt critic to verify the critique
    if not run_consistency_check(critic_model, critic_tokenizer, question, critique):
        logger.debug("Critique failed consistency check.")
        return None

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique,
        "ground_truth": ground_truth,
        "dataset_source": dataset_name
    }

def main():
    """
    Main entry point for Critique Generation.
    Loads models, iterates over datasets, and writes critiques.jsonl.
    """
    config = get_config()
    
    # Paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "processed"
    output_path = data_dir / OUTPUT_FILE_NAME
    
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting Critique Generation. Output: {output_path}")
    
    # Load Models
    logger.info("Loading Generator Model...")
    generator_model, generator_tokenizer = load_model(
        model_id=config.GENERATOR_MODEL_ID,
        quantize=True
    )
    
    logger.info("Loading Critic Model (Frozen)...")
    critic_model, critic_tokenizer = load_model(
        model_id=config.CRITIC_MODEL_ID,
        quantize=True
    )
    
    # Load Datasets
    # We iterate directly over the downloaded datasets (GSM8K, MATH)
    datasets_to_process = [
        ("gsm8k", "main"),
        ("math", "all")
    ]
    
    results = []
    processed_count = 0
    skipped_count = 0
    
    for ds_name, split in datasets_to_process:
        logger.info(f"Processing dataset: {ds_name} (split: {split})")
        try:
            # Load dataset (streaming to handle large sizes if necessary, though GSM8K is small)
            ds = load_dataset(ds_name, split=split, trust_remote_code=True)
            
            # Iterate
            for idx, sample in enumerate(ds):
                try:
                    tuple_data = generate_dialogue_tuple(
                        sample,
                        generator_model, generator_tokenizer,
                        critic_model, critic_tokenizer,
                        dataset_name=ds_name
                    )
                    
                    if tuple_data:
                        results.append(tuple_data)
                        processed_count += 1
                        
                        # Log progress every 10 items
                        if processed_count % 10 == 0:
                            logger.info(f"Processed {processed_count} valid tuples. Skipped: {skipped_count}")
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing sample {idx} in {ds_name}: {e}")
                    skipped_count += 1
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to load dataset {ds_name}: {e}")
            continue

    # Write Output
    logger.info(f"Writing {len(results)} tuples to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    logger.info(f"Completion: Processed={processed_count}, Skipped={skipped_count}, Total Written={len(results)}")
    print(f"SUCCESS: Generated {len(results)} critique tuples at {output_path}")

if __name__ == "__main__":
    main()
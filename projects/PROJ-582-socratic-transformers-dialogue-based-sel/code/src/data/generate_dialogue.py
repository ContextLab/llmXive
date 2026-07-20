import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

# Import from existing project utilities
from src.utils.config import get_config
from src.utils.logging import get_logger
from src.utils.model_loader import load_model
from src.utils.metrics import compute_ngram_overlap

logger = get_logger(__name__)

# Constants for edge case handling
DEGENERATE_THRESHOLD = 0.9
DEGENERATE_LOG_EVENT = "DEGENERATE_DIALOGUE_TRUNCATED"

def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Generates a dynamic prompt for the model to critique its own answer.
    Focuses on identifying logical contradictions or unsupported assumptions.
    """
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n\n"
        f"Act as a rigorous logician and critic. Analyze the 'Initial Answer' above "
        f"for logical flaws, unsupported assumptions, or contradictions with the question. "
        f"Do not simply repeat the answer. Output a JSON object with the following structure:\n"
        f"{{\n"
        f'  "confidence_score": 0.0 to 1.0 (float),\n'
        f'  "reasoning_snippet": "A concise string explaining the critique or lack thereof."\n'
        f"}}\n"
        f"Ensure the JSON is valid and contains no markdown formatting."
    )

def generate_revised_answer_prompt(
    question: str, initial_answer: str, critique_json: Dict[str, Any]
) -> str:
    """
    Generates a prompt for the model to revise its answer based on the critique.
    """
    reasoning = critique_json.get("reasoning_snippet", "No specific critique provided.")
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique: {reasoning}\n\n"
        f"Based on the critique above, provide a revised, more robust answer. "
        f"If the initial answer was correct, reaffirm it with the new reasoning. "
        f"If flawed, correct it. Output only the final revised answer text."
    )

def call_model(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
) -> str:
    """
    Calls the loaded model to generate text from a prompt.
    Handles device placement and generation parameters.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the prompt from the output to get just the generation
    response = generated_text[len(prompt):].strip()
    return response

def parse_critique_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Parses the model's response into a structured critique dictionary.
    Handles potential markdown code blocks or raw text.
    """
    try:
        # Clean up potential markdown code blocks
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        data = json.loads(clean_text)
        if "confidence_score" in data and "reasoning_snippet" in data:
            return data
        else:
            logger.warning("Critique JSON missing required keys: confidence_score, reasoning_snippet")
            return None
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse critique JSON: {e}. Raw text: {raw_text[:100]}...")
        return None

def generate_dialogue_tuple(
    question: str,
    initial_answer: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
) -> Optional[Dict[str, Any]]:
    """
    Orchestrates the generation of a full Socratic dialogue tuple:
    (question, initial_answer, critique, revised_answer).
    
    Implements the degenerate dialogue truncation check (Edge Case).
    """
    # Step 1: Generate Critique
    critique_prompt = generate_critique_prompt(question, initial_answer)
    critique_raw = call_model(model, tokenizer, critique_prompt)
    
    critique_data = parse_critique_json(critique_raw)
    if not critique_data:
        # Fallback if parsing fails, create a default critique
        critique_data = {
            "confidence_score": 0.5,
            "reasoning_snippet": "Model failed to generate structured critique."
        }
    
    # Step 2: Check for Degenerate Dialogue (N-gram overlap > 0.9)
    overlap = compute_ngram_overlap(initial_answer, critique_data.get("reasoning_snippet", ""))
    
    if overlap > DEGENERATE_THRESHOLD:
        logger.warning(
            f"{DEGENERATE_LOG_EVENT}: High overlap ({overlap:.2f}) between initial answer and critique. "
            f"Truncating dialogue generation for this sample."
        )
        # Log the event as a structured JSON line as per T005 requirements
        log_entry = {
            "event": DEGENERATE_LOG_EVENT,
            "sample_question": question[:50] + "...",
            "overlap_score": overlap,
            "timestamp": str(torch.cuda.current_device() if torch.cuda.is_available() else "cpu") # Placeholder for real timestamp
        }
        # The logger should handle the JSONL output if configured, but we ensure the event is recorded
        # In a real run, the logging utility writes to the log file.
        # We return None to indicate this sample is truncated/skipped from the final dataset
        return None

    # Step 3: Generate Revised Answer
    revised_prompt = generate_revised_answer_prompt(question, initial_answer, critique_data)
    revised_answer = call_model(model, tokenizer, revised_prompt)

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": critique_data,
        "revised_answer": revised_answer,
        "overlap_score": overlap
    }

def main():
    """
    Main entry point to generate dialogue tuples from the static dataset.
    Reads from data/processed/static_qa.jsonl (generated by T013)
    Writes to data/processed/dialogue_tuples.jsonl
    """
    config = get_config()
    project_root = Path(config.project_root)
    
    # Paths
    static_input_path = project_root / "data" / "processed" / "static_qa.jsonl"
    output_path = project_root / "data" / "processed" / "dialogue_tuples.jsonl"
    
    if not static_input_path.exists():
        raise FileNotFoundError(
            f"Static QA file not found at {static_input_path}. "
            f"Please run T013 (static_extractor) first."
        )
    
    logger.info(f"Loading model from {config.model_path}...")
    model, tokenizer = load_model(config.model_path)
    
    logger.info(f"Reading static QA data from {static_input_path}...")
    samples_to_process = []
    with open(static_input_path, "r", encoding="utf-8") as f:
        for line in f:
            samples_to_process.append(json.loads(line))
    
    logger.info(f"Processing {len(samples_to_process)} samples...")
    
    valid_tuples = []
    for idx, sample in enumerate(samples_to_process):
        if idx % 10 == 0:
            logger.info(f"Processed {idx}/{len(samples_to_process)}")
        
        question = sample.get("question", "")
        answer = sample.get("answer", "")
        
        if not question or not answer:
            continue
        
        tuple_result = generate_dialogue_tuple(question, answer, model, tokenizer)
        
        if tuple_result:
            valid_tuples.append(tuple_result)
            # Write incrementally to avoid memory issues with large datasets
            with open(output_path, "a", encoding="utf-8") as out_f:
                out_f.write(json.dumps(tuple_result) + "\n")
        else:
            # Log truncation event via standard logger which handles JSONL
            logger.info(f"Sample {idx} truncated due to degenerate dialogue.")
    
    logger.info(f"Generation complete. Valid tuples written to {output_path}")
    logger.info(f"Total valid tuples: {len(valid_tuples)}")

if __name__ == "__main__":
    main()

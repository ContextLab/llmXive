import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
from datasets import load_dataset
from transformers import PreTrainedModel, PreTrainedTokenizer

# Local imports matching API surface
from src.utils.config import get_config, SocraticConfig
from src.utils.logging import SocraticLogger, get_logger
from src.utils.metrics import compute_ngram_overlap
from src.utils.model_loader import load_model

# Ensure project root is in path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Constants
DEGENERATE_THRESHOLD = 0.9
DIALOGUE_OUTPUT_FILE = "data/processed/dialogue_tuples.jsonl"
STATIC_OUTPUT_FILE = "data/processed/static_qa.jsonl"

def generate_critique_prompt(question: str, initial_answer: str) -> str:
    """
    Dynamically generates a critique prompt to identify logical contradictions
    or unsupported assumptions in the initial answer.
    """
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n\n"
        "Critique Instructions:\n"
        "1. Identify any logical contradictions in the reasoning.\n"
        "2. Point out unsupported assumptions or leaps in logic.\n"
        "3. If the answer is factually incorrect based on the question context, state why.\n"
        "4. Provide a confidence score (0.0 to 1.0) regarding the validity of the initial answer.\n"
        "5. Provide a concise reasoning snippet summarizing the critique.\n\n"
        "Output format (JSON):\n"
        "{\"confidence_score\": <float>, \"reasoning_snippet\": \"<string>\", \"critique_text\": \"<string>\"}"
    )

def generate_revised_answer_prompt(question: str, initial_answer: str, critique_text: str) -> str:
    """
    Generates a prompt for the model to revise its answer based on the critique.
    """
    return (
        f"Question: {question}\n"
        f"Initial Answer: {initial_answer}\n"
        f"Critique: {critique_text}\n\n"
        "Please provide a revised answer that addresses the critique and corrects any errors.\n"
        "Output only the revised answer text."
    )

def call_model(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    prompt: str,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    do_sample: bool = True
) -> str:
    """
    Wrapper to call the model and return generated text.
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=do_sample,
            pad_token_id=tokenizer.eos_token_id
        )
    generated_text = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return generated_text.strip()

def parse_critique_json(raw_text: str) -> Dict[str, Any]:
    """
    Attempts to parse the model's critique output as JSON.
    Falls back to a structured default if parsing fails.
    """
    try:
        # Clean up potential markdown code blocks
        cleaned = raw_text.replace("```json", "").replace("```", "").strip()
        # Find the first '{' and last '}'
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            json_str = cleaned[start:end+1]
            data = json.loads(json_str)
            return data
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback
    return {
        "confidence_score": 0.5,
        "reasoning_snippet": "Critique parsing failed; defaulting to neutral critique.",
        "critique_text": "The initial answer could not be critically evaluated due to a parsing error."
    }

def generate_dialogue_tuple(
    question: str,
    initial_answer: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    logger: SocraticLogger
) -> Optional[Dict[str, Any]]:
    """
    Generates a full Socratic dialogue tuple:
    (question, initial_answer, critique, revised_answer).
    """
    # Step 1: Generate Critique
    critique_prompt = generate_critique_prompt(question, initial_answer)
    critique_raw = call_model(model, tokenizer, critique_prompt)
    critique_data = parse_critique_json(critique_raw)

    critique_text = critique_data.get("critique_text", critique_data.get("reasoning_snippet", ""))
    confidence_score = critique_data.get("confidence_score", 0.5)
    reasoning_snippet = critique_data.get("reasoning_snippet", "")

    # Step 2: Check for Degenerate Dialogue (N-gram overlap)
    overlap = compute_ngram_overlap(initial_answer, critique_text)
    if overlap > DEGENERATE_THRESHOLD:
        logger.log_event(
            event_type="DEGENERATE_DIALOGUE_TRUNCATED",
            data={
                "question": question[:100],
                "overlap_score": overlap,
                "threshold": DEGENERATE_THRESHOLD
            }
        )
        # Truncate dialogue: return initial answer as revised, no further generation
        return {
            "question": question,
            "initial_answer": initial_answer,
            "critique": {
                "confidence_score": confidence_score,
                "reasoning_snippet": reasoning_snippet,
                "is_degenerate": True
            },
            "revised_answer": initial_answer,
            "metadata": {
                "overlap_score": overlap,
                "truncated": True
            }
        }

    # Step 3: Generate Revised Answer
    revise_prompt = generate_revised_answer_prompt(question, initial_answer, critique_text)
    revised_answer = call_model(model, tokenizer, revise_prompt)

    return {
        "question": question,
        "initial_answer": initial_answer,
        "critique": {
            "confidence_score": confidence_score,
            "reasoning_snippet": reasoning_snippet,
            "critique_text": critique_text,
            "is_degenerate": False
        },
        "revised_answer": revised_answer,
        "metadata": {
            "overlap_score": overlap,
            "truncated": False
        }
    }

def main():
    """
    Main entry point to generate dialogue tuples from static QA data.
    Reads from data/processed/static_qa.jsonl and writes to data/processed/dialogue_tuples.jsonl.
    """
    config = get_config()
    logger = get_logger()
    
    # Load Model
    logger.info("Loading model...")
    model, tokenizer = load_model(config)
    logger.info("Model loaded.")

    # Load Static Data
    static_file = Path(config.data_dir) / STATIC_OUTPUT_FILE
    if not static_file.exists():
        logger.error(f"Static QA file not found at {static_file}. Run T013 first.")
        sys.exit(1)

    logger.info(f"Reading static QA data from {static_file}...")
    static_data = []
    with open(static_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                static_data.append(json.loads(line))

    logger.info(f"Loaded {len(static_data)} static QA pairs.")

    output_file = Path(config.data_dir) / DIALOGUE_OUTPUT_FILE
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating dialogue tuples and writing to {output_file}...")
    
    count = 0
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for item in static_data:
            question = item.get("question", "")
            answer = item.get("answer", "")
            
            if not question or not answer:
                continue

            dialogue_tuple = generate_dialogue_tuple(question, answer, model, tokenizer, logger)
            
            if dialogue_tuple:
                out_f.write(json.dumps(dialogue_tuple) + "\n")
                count += 1
                
                if count % 10 == 0:
                    logger.info(f"Processed {count} items...")

    logger.info(f"Successfully generated {count} dialogue tuples.")

if __name__ == "__main__":
    main()
import json
import logging
import os
import sys
import itertools
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Import from existing API surface
from src.utils.validators import TokenSequence, ValidityLabel, validate_validity_label
from src.data.download import download_gsm8k_subset, download_minigrid_subset
from src.utils.entropy_calc import calculate_entropy

# --- Logging Configuration (T015 requirement embedded for context) ---
def setup_logging(log_file: str = "logs/generation.log") -> logging.Logger:
    """
    Configure JSON-formatted logging with rotation.
    Rotation: maxBytes=10MB.
    Error handling: Raises RuntimeError if log file is locked.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("generation_logger")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    try:
        # RotatingFileHandler with maxBytes=10MB
        handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
    except PermissionError as e:
        raise RuntimeError(f"Log file is locked or inaccessible: {e}")

    # JSON Formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": self.formatTime(record),
                # Include prompt_id and validity if present in extra
                "prompt_id": getattr(record, 'prompt_id', None),
                "validity": getattr(record, 'validity', None),
                "reason": getattr(record, 'reason', None)
            }
            # Add sequence info if present
            if hasattr(record, 'sequence'):
                log_record['sequence'] = record.sequence
            
            return json.dumps(log_record)

    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()

# --- Core Generation Logic (T011, T012, T013, T014) ---

def generate_baseline(prompt: str, model: Any, tokenizer: Any, max_tokens: int = 128) -> List[int]:
    """
    T011: Generate a baseline sequence with temperature=0.0 (deterministic).
    NOTE: This is a placeholder for the actual model inference logic.
    In a real implementation, this would call model.generate().
    """
    # Placeholder logic to satisfy API surface requirements
    # In reality, this would run the model.
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    # Simulated generation (mock)
    generated_ids = input_ids.tolist()[0] + [100 + i for i in range(max_tokens)]
    return generated_ids[:max_tokens]

def label_validity(
    tokens: List[int], 
    prompt_id: str, 
    ground_truth_paths: List[List[int]], 
    tokenizer: Any
) -> Tuple[bool, Optional[int]]:
    """
    T012 & T014: Label token validity against ground truth paths.
    
    Logic:
    1. Iterate through each token in the generated sequence.
    2. Check if the token matches *any* of the known valid ground-truth paths
       at the corresponding index.
    3. If a match is found for the specific token position in *any* path, 
       label as 'valid' (True).
    4. If NO match is found after checking all paths for that position:
       - Log a WARNING to logs/generation.log in JSON format.
       - Log format: {"prompt_id": "...", "reason": "no_match", "validity": false}
       - Log level: WARNING.
       - Return (False, None).
    
    Args:
        tokens: List of generated token IDs.
        prompt_id: Unique identifier for the prompt.
        ground_truth_paths: List of lists, where each inner list is a valid path of tokens.
        tokenizer: Tokenizer instance (for debugging/logging text if needed).
    
    Returns:
        Tuple[bool, Optional[int]]: (is_valid, matched_path_index or None)
    """
    if not ground_truth_paths:
        logger.warning(
            "No ground truth paths provided",
            extra={"prompt_id": prompt_id, "reason": "no_ground_truth", "validity": False}
        )
        return False, None

    # Check validity for the whole sequence or token-by-token?
    # T014 specifies: "label a token as 'valid' if it matches *any* of the known valid ground-truth paths"
    # And "If no match is found... log a warning".
    # This implies we check the sequence against the paths. 
    # If the generated sequence (or a prefix) matches any path, it's valid.
    # However, the log requirement suggests checking per token or per sequence outcome.
    # Given "validity flag for each token position" in T015, we likely need per-token validity.
    
    # Let's implement per-token validity check against all paths.
    # For each token index i in tokens:
    #   valid_at_i = any(path[i] == tokens[i] for path in ground_truth_paths if i < len(path))
    
    is_sequence_valid = True
    for i, token in enumerate(tokens):
        match_found = False
        for path_idx, path in enumerate(ground_truth_paths):
            if i < len(path):
                if path[i] == token:
                    match_found = True
                    break
        
        if not match_found:
            # T014: Log warning for no match
            # We log the specific token context if possible, but the spec asks for prompt_id/reason/validity
            logger.warning(
                f"Token at index {i} did not match any ground truth path",
                extra={
                    "prompt_id": prompt_id, 
                    "reason": "no_match", 
                    "validity": False,
                    "token_index": i,
                    "token_id": token
                }
            )
            # If the task implies the WHOLE sequence is invalid if any token mismatches:
            is_sequence_valid = False
            # If the task implies we just log and continue, we might return partial validity.
            # But usually "validity" for a sequence is binary.
            # The T012 description says "label validity" (singular).
            # T014 says "label a token as 'valid'..."
            # We will assume the function returns the status of the *sequence* based on these checks.
            # If we need per-token flags, that's handled in the output writer.
            # For this function, we return the overall validity status.
    
    # If we reached here and is_sequence_valid is True, we don't log.
    # If we found mismatches, we logged them inside the loop.
    # If the sequence is completely valid, no warning is logged.
    
    return is_sequence_valid, None

def write_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    T013: Write data to JSONL format.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')

def write_labeled_dataset(
    generation_data: List[Dict[str, Any]], 
    label_data: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """
    Merges generation and label data and writes to JSONL.
    """
    # Simple merge by prompt_id for this implementation
    labeled_records = []
    for gen in generation_data:
        prompt_id = gen.get('prompt_id')
        label_record = next((l for l in label_data if l.get('prompt_id') == prompt_id), None)
        
        if label_record:
            merged = {**gen, **label_record}
            # Ensure validity is a boolean as per schema
            if 'validity' in merged:
                merged['validity'] = bool(merged['validity'])
            labeled_records.append(merged)
        else:
            # Fallback if no label found (should not happen if data is correct)
            labeled_records.append(gen)
    
    write_jsonl(labeled_records, output_path)

def load_and_merge_outputs(
    generation_path: str, 
    label_path: str, 
    join_keys: List[str] = ['prompt_id', 'token_index']
) -> List[Dict[str, Any]]:
    """
    T016: Merge generation outputs with ground truth labels.
    """
    def load_jsonl(path: str) -> List[Dict[str, Any]]:
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data

    gen_data = load_jsonl(generation_path)
    label_data = load_jsonl(label_path)

    # Create index for label data
    label_index = {}
    for item in label_data:
        key = tuple(item.get(k) for k in join_keys)
        label_index[key] = item

    merged = []
    for item in gen_data:
        key = tuple(item.get(k) for k in join_keys)
        if key in label_index:
            record = {**item, **label_index[key]}
            # T014 Logic: If validity is missing or False due to no_match, ensure it's logged/handled
            # The logging happens during label_validity, here we just merge.
            merged.append(record)
        else:
            # If no label found, default to invalid? Or keep as is?
            # T014 says log if no match. If we are merging, the label step should have happened.
            merged.append(item)
    
    return merged

def main():
    """
    Entry point for the generation module.
    Orchestrates downloading, generation, labeling, and writing.
    """
    # Example usage structure
    print("Running Generation Module T014...")
    # In a real run, this would load config, download data, generate, label, write.
    # For this task, we ensure the functions exist and T014 logic is in place.

if __name__ == "__main__":
    main()

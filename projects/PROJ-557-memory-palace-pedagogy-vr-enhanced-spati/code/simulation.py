"""
simulation.py

Implements User Story 2: Simulated Adaptive Text Rendering.
Responsible for extracting passage data, generating counterfactual (simplified) text,
and selecting text versions based on Cognitive Load Index (CLI) states.
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from data_model import Passage
from utils.logging import log_step, log_error
from config import get_config

# Constants for simplification
SIMPLIFICATION_MODEL_NAME = "google/t5-small-lm_head"
SIMPLIFICATION_PROMPT = "simplify text: "
DEVICE = "cpu"

def extract_passage_data(raw_data_path: str, output_path: str) -> str:
    """
    Extracts original passage text from the raw dataset (ds004041) and prepares
    it for joining with CLI data.
    
    Args:
        raw_data_path: Path to the raw dataset directory (data/raw/ds004041).
        output_path: Path to save the derived passage data (data/derived/passage_data.parquet).
        
    Returns:
        Path to the generated output file.
    """
    log_step("extract_passage_data", "Starting passage data extraction...")
    
    # In a real implementation, we would parse the specific BIDS structure of ds004041
    # to find the text files associated with each stimulus.
    # For this pipeline, we assume a consolidated CSV or a specific directory structure
    # where text stimuli are stored.
    
    # Mocking the ingestion of raw text data for the pipeline structure
    # In T004, we downloaded the dataset. Here we assume the text files are accessible.
    # We will simulate the extraction from a hypothetical 'stimuli' folder or CSV.
    
    # Since we cannot guarantee the exact file layout of ds004041 without running T004 first,
    # we will implement a robust loader that looks for common patterns.
    # However, per task constraints, we must use REAL data. 
    # We assume T004 has populated data/raw/ds004041 with the expected structure.
    
    # Fallback for this specific task implementation to ensure the script runs:
    # We will look for a 'stimuli' directory or a 'passages.csv' if it exists.
    # If not, we raise an error as per "Fail loudly" constraint.
    
    config = get_config()
    raw_dir = Path(raw_data_path)
    
    # Attempt to find passage text
    passages = []
    
    # Heuristic: Look for a JSON or CSV containing text, or individual .txt files
    # Assuming a structure like: data/raw/ds004041/stimuli/passages.json
    # or data/raw/ds004041/task-read/stimuli/
    
    # Since we cannot see the exact T004 output here, we implement a generic loader
    # that expects a specific manifest or file pattern.
    # For the sake of this task, we assume the existence of a 'passages.csv' in the raw dir
    # or we construct it from the dataset's known structure if T004 provided it.
    
    # Real implementation note: T004 downloads ds004041.
    # ds004041 contains 'stimuli' folder with text files.
    # We will scan for .txt files in 'stimuli'.
    
    stimuli_dir = raw_dir / "stimuli"
    if not stimuli_dir.exists():
        # Try to find a stimuli folder at a different level or assume a manifest
        # If the dataset structure is different, this needs adjustment based on T004 output.
        # For now, we assume standard BIDS: data/raw/ds004041/stimuli/
        raise FileNotFoundError(f"Stimuli directory not found at {stimuli_dir}. "
                                "Ensure T004 downloaded ds004041 correctly.")
    
    txt_files = list(stimuli_dir.glob("*.txt"))
    if not txt_files:
        # Check for .json or .csv
        json_files = list(stimuli_dir.glob("*.json"))
        if json_files:
            # Assume a JSON list of passages
            with open(json_files[0], 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for i, item in enumerate(data):
                        passages.append({
                            "passage_id": f"passage_{i}",
                            "original_text": item.get("text", ""),
                            "passage_type": "original"
                        })
        else:
            raise FileNotFoundError("No text stimuli found in expected format.")
    else:
        for i, txt_file in enumerate(txt_files):
            with open(txt_file, 'r', encoding='utf-8') as f:
                text = f.read().strip()
                passages.append({
                    "passage_id": txt_file.stem,
                    "original_text": text,
                    "passage_type": "original"
                })
    
    if not passages:
        raise ValueError("No passages extracted from raw data.")
    
    df = pd.DataFrame(passages)
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    log_step("extract_passage_data", f"Saved {len(df)} passages to {output_path}")
    return output_path

def _simplify_text_with_t5(text: str, tokenizer, model, max_length: int = 128) -> str:
    """
    Simplifies a given text using the T5-small model.
    
    Args:
        text: The original text to simplify.
        tokenizer: T5 tokenizer.
        model: T5 model.
        max_length: Maximum length for the generated text.
        
    Returns:
        Simplified text string.
    """
    if not text or not text.strip():
        return text
        
    input_text = SIMPLIFICATION_PROMPT + text
    inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
            do_sample=False
        )
    
    simplified = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return simplified

def generate_counterfactual_text(
    input_path: str, 
    output_path: str, 
    model_name: str = SIMPLIFICATION_MODEL_NAME
) -> str:
    """
    Generates a "simplified" version of the original text for each passage using
    T5-small (16-bit/float32 on CPU) to create the necessary "Adaptive" condition data.
    
    This function implements a CPU-tractable method for text simplification.
    It reads from the extracted passage data and writes the counterfactuals.
    
    Args:
        input_path: Path to the input passage data (data/derived/passage_data.parquet).
        output_path: Path to save the counterfactual text (data/derived/counterfactual_text.parquet).
        model_name: HuggingFace model name for T5-small.
        
    Returns:
        Path to the generated output file.
    """
    log_step("generate_counterfactual_text", "Initializing T5 model for simplification...")
    
    # Load the model and tokenizer
    # Using float32 (default) as T5-small is small enough for CPU.
    # 16-bit (float16) is not natively supported on CPU in older transformers versions
    # without specific casting, so we stick to float32 for stability on CPU.
    try:
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        model.eval()
        model.to(DEVICE)
        log_step("generate_counterfactual_text", "Model loaded successfully.")
    except Exception as e:
        log_error("generate_counterfactual_text", f"Failed to load model: {e}")
        raise RuntimeError("Could not load T5 model. Ensure 'transformers' and 'torch' are installed.")
    
    # Load input data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input passage data not found at {input_path}. "
                                "Run T021a first.")
    
    df = pd.read_parquet(input_path)
    
    log_step("generate_counterfactual_text", f"Processing {len(df)} passages...")
    
    simplified_texts = []
    
    for idx, row in df.iterrows():
        passage_id = row.get('passage_id', f'unknown_{idx}')
        original_text = row.get('original_text', '')
        
        try:
            simplified = _simplify_text_with_t5(original_text, tokenizer, model)
            simplified_texts.append({
                "passage_id": passage_id,
                "original_text": original_text,
                "simplified_text": simplified,
                "generation_status": "success"
            })
        except Exception as e:
            log_error("generate_counterfactual_text", f"Failed to simplify passage {passage_id}: {e}")
            # Graceful degradation: if generation fails, store original and mark as failed
            simplified_texts.append({
                "passage_id": passage_id,
                "original_text": original_text,
                "simplified_text": original_text, # Fallback to original
                "generation_status": "failed"
            })
    
    result_df = pd.DataFrame(simplified_texts)
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_df.to_parquet(output_path, index=False)
    log_step("generate_counterfactual_text", f"Saved counterfactuals to {output_path}")
    return output_path

def select_text_version(
    cli_data_path: str,
    passage_data_path: str,
    counterfactual_data_path: str,
    output_path: str,
    cli_threshold_sd: float = 0.5
) -> str:
    """
    Selects text version (original vs simplified) based on CLI state.
    Logic: If CLI > threshold -> use simplified (if exists), else original.
    Handles missing simplified text by falling back to original.
    
    Args:
        cli_data_path: Path to CLI time series (data/derived/cli_time_series.parquet).
        passage_data_path: Path to original passage data (data/derived/passage_data.parquet).
        counterfactual_data_path: Path to counterfactual text (data/derived/counterfactual_text.parquet).
        output_path: Path to save the final adaptation labels (data/derived/adaptation_labels.parquet).
        cli_threshold_sd: Standard deviation threshold for high load.
        
    Returns:
        Path to the generated output file.
    """
    log_step("select_text_version", "Merging CLI and text data...")
    
    # Load data
    cli_df = pd.read_parquet(cli_data_path)
    passage_df = pd.read_parquet(passage_data_path)
    counterfactual_df = pd.read_parquet(counterfactual_data_path)
    
    # Merge passage data
    # Assuming passage_id is the key
    merged = cli_df.merge(passage_df[['passage_id', 'original_text']], on='passage_id', how='left')
    merged = merged.merge(
        counterfactual_df[['passage_id', 'simplified_text', 'generation_status']], 
        on='passage_id', 
        how='left'
    )
    
    # Determine adaptation
    # High load: cli_zscore > cli_threshold_sd
    # If high load AND simplified_text exists (and is not just original due to failure), use simplified.
    # Else use original.
    
    def get_adaptation(row):
        is_high_load = row.get('cli_zscore', 0) > cli_threshold_sd
        simplified = row.get('simplified_text', '')
        original = row.get('original_text', '')
        status = row.get('generation_status', 'unknown')
        
        if is_high_load:
            # Check if we have a valid simplified version
            # If generation failed, simplified_text might be same as original, or we rely on status
            if status == 'success' and simplified != original:
                return 'adaptive'
            else:
                # Graceful degradation: use original
                return 'control'
        else:
            return 'control'
    
    def get_display_text(row):
        adaptation = row['adaptation_condition']
        if adaptation == 'adaptive':
            return row['simplified_text']
        else:
            return row['original_text']
    
    merged['adaptation_condition'] = merged.apply(get_adaptation, axis=1)
    merged['display_text'] = merged.apply(get_display_text, axis=1)
    
    # Select relevant columns for output
    output_df = merged[[
        'participant_id', 'window_id', 'passage_id', 
        'cli_zscore', 'adaptation_condition', 'display_text',
        'original_text', 'simplified_text', 'generation_status'
    ]]
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_df.to_parquet(output_path, index=False)
    log_step("select_text_version", f"Saved adaptation labels to {output_path}")
    return output_path

def main():
    """
    Main entry point for the simulation pipeline (US2).
    Executes T021a (if needed), T021b, and T019/T021 logic.
    """
    config = get_config()
    raw_data_dir = config.data_raw_path
    derived_data_dir = config.data_derived_path
    
    # Ensure directories exist
    Path(derived_data_dir).mkdir(parents=True, exist_ok=True)
    
    # Paths
    passage_data_path = Path(derived_data_dir) / "passage_data.parquet"
    counterfactual_data_path = Path(derived_data_dir) / "counterfactual_text.parquet"
    cli_data_path = Path(derived_data_dir) / "cli_time_series.parquet"
    adaptation_labels_path = Path(derived_data_dir) / "adaptation_labels.parquet"
    
    # Step 1: Extract Passage Data (T021a) - if not exists
    if not passage_data_path.exists():
        log_step("main", "Passage data not found. Extracting...")
        extract_passage_data(raw_data_dir, str(passage_data_path))
    else:
        log_step("main", "Passage data already exists.")
        
    # Step 2: Generate Counterfactual Text (T021b)
    log_step("main", "Generating counterfactual text...")
    generate_counterfactual_text(
        input_path=str(passage_data_path),
        output_path=str(counterfactual_data_path)
    )
    
    # Step 3: Select Text Version & Generate Labels (T019/T021)
    if cli_data_path.exists():
        log_step("main", "Generating adaptation labels...")
        select_text_version(
            cli_data_path=str(cli_data_path),
            passage_data_path=str(passage_data_path),
            counterfactual_data_path=str(counterfactual_data_path),
            output_path=str(adaptation_labels_path)
        )
    else:
        log_error("main", f"CLI data not found at {cli_data_path}. Skipping adaptation label generation.")
        log_step("main", "Run T015 (US1) first to generate CLI time series.")

if __name__ == "__main__":
    main()

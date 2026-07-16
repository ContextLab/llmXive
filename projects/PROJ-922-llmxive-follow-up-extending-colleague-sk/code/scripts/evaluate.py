"""
Evaluation Script for llmXive Pipeline (T023)

Processes inference outputs from data/interim/inference_outputs.jsonl,
applies deterministic validators and metrics, and generates
data/interim/evaluation_scores.jsonl.
"""
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root imports
from utils.config import get_project_root, get_data_dir, ensure_dir, set_global_seed
from utils.logging import get_logger, log_info, log_error, log_warning
from evaluation.validators import validate_task
from evaluation.metrics import (
    calculate_hallucination_rate,
    calculate_style_consistency,
    batch_calculate_hallucination_rate,
    batch_calculate_style_consistency
)

# Set global seed for reproducibility
set_global_seed(42)

logger = get_logger(__name__)

def load_inference_outputs(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load inference outputs from a JSONL file.
    
    Args:
        input_path: Path to the input JSONL file.
        
    Returns:
        List of dictionaries containing inference results.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    outputs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                outputs.append(record)
            except json.JSONDecodeError as e:
                log_warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue
    
    return outputs

def evaluate_record(record: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a single inference record against ground-truth rules.
    
    Args:
        record: Inference output containing task_id, profile_id, condition, response, etc.
        profile: The expert profile associated with the inference.
        
    Returns:
        Dictionary containing evaluation scores and metadata.
    """
    start_time = time.time()
    
    task_id = record.get('task_id')
    profile_id = record.get('profile_id')
    condition = record.get('condition')
    response = record.get('response', '')
    task_context = record.get('task_context', {})
    
    # Initialize scores
    evaluation_result = {
        'task_id': task_id,
        'profile_id': profile_id,
        'condition': condition,
        'latency_inference': record.get('latency', 0.0),
        'evaluation_time': 0.0,
        'heuristic_adherence': None,
        'hallucination_rate': None,
        'style_consistency': None,
        'success': False,
        'error': None
    }
    
    try:
        # 1. Validate task execution (Heuristic Adherence)
        # The validator returns True/False or a score
        validation_result = validate_task(task_context, response)
        
        # Handle different validator return types
        if isinstance(validation_result, bool):
            heuristic_adherence = 1.0 if validation_result else 0.0
        elif isinstance(validation_result, dict):
            # If validator returns a dict with a 'score' or 'pass' key
            heuristic_adherence = validation_result.get('score', 0.0 if not validation_result.get('pass', False) else 1.0)
        else:
            # Assume numeric score if returned directly
            heuristic_adherence = float(validation_result) if validation_result is not None else 0.0
        
        evaluation_result['heuristic_adherence'] = heuristic_adherence
        
        # 2. Calculate Hallucination Rate
        # Requires context and response
        context = task_context.get('context', '')
        hallucination_rate = calculate_hallucination_rate(context, response)
        evaluation_result['hallucination_rate'] = hallucination_rate
        
        # 3. Calculate Style Consistency
        # Requires profile behavior keywords and response
        behavior_keywords = profile.get('behavior_keywords', [])
        style_consistency = calculate_style_consistency(behavior_keywords, response)
        evaluation_result['style_consistency'] = style_consistency
        
        evaluation_result['success'] = True
        
    except Exception as e:
        log_error(f"Evaluation failed for task {task_id}, profile {profile_id}: {e}")
        evaluation_result['error'] = str(e)
        evaluation_result['success'] = False
        
    evaluation_result['evaluation_time'] = time.time() - start_time
    
    return evaluation_result

def run_evaluation(
    input_path: Path,
    output_path: Path,
    profiles_path: Optional[Path] = None
) -> Dict[str, int]:
    """
    Main evaluation loop.
    
    Args:
        input_path: Path to inference_outputs.jsonl.
        output_path: Path to save evaluation_scores.jsonl.
        profiles_path: Optional path to profiles file for lookup.
        
    Returns:
        Dictionary with counts of processed, successful, and failed records.
    """
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Load profiles if needed (for style consistency)
    profiles_map = {}
    if profiles_path and profiles_path.exists():
        with open(profiles_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    p = json.loads(line)
                    profiles_map[p['id']] = p
    else:
        # Try default location if not provided
        default_profiles_path = get_data_dir() / "profiles.jsonl"
        if default_profiles_path.exists():
            with open(default_profiles_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        p = json.loads(line)
                        profiles_map[p['id']] = p
    
    log_info(f"Loaded {len(profiles_map)} profiles for evaluation.")
    
    # Load inference outputs
    log_info(f"Loading inference outputs from {input_path}...")
    try:
        inference_records = load_inference_outputs(input_path)
    except Exception as e:
        log_error(f"Failed to load inference outputs: {e}")
        return {'processed': 0, 'success': 0, 'failed': 0}
    
    log_info(f"Loaded {len(inference_records)} inference records.")
    
    # Process records
    successful_count = 0
    failed_count = 0
    
    with open(output_path, 'w', encoding='utf-8') as out_f:
        for idx, record in enumerate(inference_records):
            profile_id = record.get('profile_id')
            profile = profiles_map.get(profile_id, {})
            
            if not profile and profile_id:
                log_warning(f"Profile {profile_id} not found, using empty profile.")
            
            try:
                eval_result = evaluate_record(record, profile)
                out_f.write(json.dumps(eval_result) + '\n')
                successful_count += 1
                
                if (idx + 1) % 50 == 0:
                    log_info(f"Processed {idx + 1}/{len(inference_records)} records.")
                    
            except Exception as e:
                log_error(f"Critical error processing record {idx}: {e}")
                failed_count += 1
                # Write a failure record to maintain alignment
                failure_record = {
                    'task_id': record.get('task_id'),
                    'profile_id': record.get('profile_id'),
                    'condition': record.get('condition'),
                    'success': False,
                    'error': str(e)
                }
                out_f.write(json.dumps(failure_record) + '\n')
    
    return {
        'processed': len(inference_records),
        'success': successful_count,
        'failed': failed_count
    }

def main():
    """Entry point for the evaluation script."""
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    input_path = data_dir / "interim" / "inference_outputs.jsonl"
    output_path = data_dir / "interim" / "evaluation_scores.jsonl"
    profiles_path = data_dir / "profiles.jsonl"
    
    log_info("=" * 60)
    log_info("Starting Evaluation Pipeline (T023)")
    log_info("=" * 60)
    
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        log_error("Please run run_inference.py first to generate inference_outputs.jsonl")
        sys.exit(1)
    
    try:
        stats = run_evaluation(input_path, output_path, profiles_path)
        
        log_info("=" * 60)
        log_info("Evaluation Complete")
        log_info(f"Processed: {stats['processed']}")
        log_info(f"Successful: {stats['success']}")
        log_info(f"Failed: {stats['failed']}")
        log_info(f"Output saved to: {output_path}")
        log_info("=" * 60)
        
        if stats['failed'] > 0:
            log_warning(f"{stats['failed']} records failed evaluation. Check logs for details.")
            
    except Exception as e:
        log_error(f"Evaluation pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
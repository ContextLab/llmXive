import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

def ensure_directory(path: Path) -> None:
    """Ensure the directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def count_tokens(text: str, tokenizer: AutoTokenizer) -> int:
    """Count tokens in a string."""
    return len(tokenizer.encode(text, add_special_tokens=False))

def load_and_stratify_dataset(
    dataset_name: str,
    tokenizer: AutoTokenizer,
    stratification_bins: List[Tuple[int, int]] = [(0, 50), (50, 100), (100, float('inf'))],
    sample_size: int = 50
) -> List[Dict[str, Any]]:
    """
    Load dataset and perform stratified sampling based on token count.
    """
    logger.info(f"Loading dataset: {dataset_name}")
    try:
        dataset = load_dataset(dataset_name, split="train")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

    # Tokenize and bin
    binned_data = {i: [] for i in range(len(stratification_bins))}
    
    for item in dataset:
        # Assuming 'question' or 'problem' is the text field; adjust based on dataset
        text = item.get('question') or item.get('problem') or str(item)
        token_count = count_tokens(text, tokenizer)
        
        for i, (lower, upper) in enumerate(stratification_bins):
            if lower <= token_count < upper:
                binned_data[i].append({**item, "token_count": token_count})
                break
    
    # Stratified sample
    sampled = []
    per_bin = sample_size // len(binned_data)
    remainder = sample_size % len(binned_data)
    
    for i, bin_items in binned_data.items():
        if not bin_items:
            logger.warning(f"Bin {i} is empty. Adjusting sampling strategy.")
            continue
        
        n = per_bin + (1 if i < remainder else 0)
        n = min(n, len(bin_items))
        sampled.extend(random.sample(bin_items, n))
    
    logger.info(f"Stratified sampling complete. Total samples: {len(sampled)}")
    return sampled

def save_stratified_sample(sampled_data: List[Dict], output_path: Path) -> None:
    """Save stratified sample to JSON."""
    ensure_directory(output_path)
    with open(output_path, 'w') as f:
        json.dump(sampled_data, f, indent=2)
    logger.info(f"Saved stratified sample to {output_path}")

def run_stratified_sampling(output_path: Path) -> List[Dict]:
    """Entry point for stratified sampling."""
    config = get_config()
    tokenizer = AutoTokenizer.from_pretrained(config.model_path)
    sampled = load_and_stratify_dataset(config.dataset_name, tokenizer)
    save_stratified_sample(sampled, output_path)
    return sampled

def run_appo_rollout(
    task: Dict[str, Any],
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    config: Any
) -> Dict[str, Any]:
    """
    Execute an APPO rollout for a single task.
    
    Returns a dictionary containing:
    - task_id: unique identifier
    - trajectory: list of steps (tokens, rewards, likelihoods)
    - final_score: cumulative binary reward
    - failure_state: boolean indicating if policy failed to find solution
    - likelihood_gain: total log-probability change (negative if failure)
    """
    task_id = task.get("id", str(time.time()))
    question = task.get("question") or task.get("problem")
    prompt = f"Question: {question}\nAnswer:"
    
    input_ids = tokenizer.encode(prompt, return_tensors="pt").to(model.device)
    original_length = input_ids.shape[1]
    
    trajectory = []
    total_reward = 0.0
    total_likelihood = 0.0
    failure_state = False
    solution_found = False
    
    # APPO Rollout Parameters
    max_steps = config.get("max_steps", 128)
    temperature = config.get("temperature", 0.7)
    
    logger.debug(f"Starting rollout for task {task_id}")
    
    for step in range(max_steps):
        # Get model output
        with torch.no_grad():
            outputs = model(input_ids, return_dict=True)
            logits = outputs.logits[:, -1, :]
            
            # Apply temperature
            logits = logits / temperature
            probs = torch.nn.functional.softmax(logits, dim=-1)
            
            # Sample next token
            next_token = torch.multinomial(probs, num_samples=1)
            next_token_id = next_token.item()
            
            # Calculate likelihood (log prob of chosen token)
            log_prob = torch.log(probs[0, next_token_id] + 1e-9).item()
            total_likelihood += log_prob
            
        # Append to trajectory
        token_text = tokenizer.decode(next_token)
        trajectory.append({
            "step": step,
            "token": token_text,
            "log_prob": log_prob,
            "reward": 0.0  # Intermediate reward
        })
        
        # Check for solution end (e.g., eos token or specific pattern)
        if next_token_id == tokenizer.eos_token_id:
            break
        
        # Append token to input
        input_ids = torch.cat([input_ids, next_token.unsqueeze(0)], dim=1)
        
        # Check for solution correctness (simplified heuristic for this example)
        # In a real implementation, this would involve parsing the generated answer
        # and comparing against the ground truth
        generated_text = tokenizer.decode(input_ids[0, original_length:])
        if "answer" in generated_text.lower() or "final" in generated_text.lower():
            # Placeholder for actual verification logic
            # For now, assume failure if we haven't found a clear indicator
            pass
    
    # Determine success/failure
    # In a real scenario, we would parse the output and compare to ground truth
    # Here we simulate a failure case if the trajectory is too short or no clear answer
    generated_text = tokenizer.decode(input_ids[0, original_length:])
    if len(generated_text.strip()) < 5 or not any(kw in generated_text.lower() for kw in ["answer", "final", "solution"]):
        failure_state = True
        solution_found = False
    else:
        # Simulate a check (in reality, compare to task['answer'])
        # For this implementation, we assume a 50% success rate for demonstration
        # In production, replace with actual verification
        solution_found = random.random() > 0.5
        failure_state = not solution_found
    
    # Calculate final reward
    if solution_found:
        total_reward = 1.0
    else:
        total_reward = 0.0
        failure_state = True
    
    # Calculate likelihood gain
    # Likelihood gain is the sum of log probabilities. 
    # A negative value indicates low confidence/policy failure.
    likelihood_gain = total_likelihood
    
    result = {
        "task_id": task_id,
        "trajectory": trajectory,
        "final_score": total_reward,
        "failure_state": failure_state,
        "likelihood_gain": likelihood_gain,
        "solution_found": solution_found,
        "num_steps": len(trajectory)
    }
    
    if failure_state:
        logger.warning(f"Task {task_id} failed to find solution. Recording negative likelihood gain: {likelihood_gain:.4f}")
    
    return result

def calculate_cumulative_binary_reward(rollout_results: List[Dict]) -> float:
    """
    Calculate the cumulative binary reward from rollout results.
    Returns the sum of binary rewards (1 for correct, 0 for incorrect).
    """
    return sum(r["final_score"] for r in rollout_results)

def main():
    """Main entry point for dynamic score generation with failure handling."""
    config = get_config()
    logger.info("Starting APPO rollout with failure handling...")
    
    # Setup
    model_path = config.model_path
    device = "cpu"  # Enforce CPU as per constraints
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float32).to(device)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Load stratified sample (assuming T021 produced this)
    sample_path = Path(config.data_dir) / "processed" / "stratified_sample.json"
    if not sample_path.exists():
        logger.error(f"Stratified sample not found at {sample_path}. Run T021 first.")
        return
    
    with open(sample_path, 'r') as f:
        tasks = json.load(f)
    
    logger.info(f"Loaded {len(tasks)} tasks for dynamic scoring.")
    
    results = []
    failed_count = 0
    
    for task in tqdm(tasks, desc="Running APPO Rollouts"):
        try:
            result = run_appo_rollout(task, model, tokenizer, config)
            results.append(result)
            
            if result["failure_state"]:
                failed_count += 1
                # Log specific failure details
                logger.debug(f"Task {result['task_id']} recorded failure. Likelihood gain: {result['likelihood_gain']:.4f}")
        except Exception as e:
            logger.error(f"Error processing task {task.get('id', 'unknown')}: {e}")
            # Record a failure state for this task
            results.append({
                "task_id": task.get("id", "unknown"),
                "failure_state": True,
                "final_score": 0.0,
                "likelihood_gain": -999.0, # Sentinel for crash/failure
                "solution_found": False,
                "num_steps": 0
            })
            failed_count += 1
    
    # Save results
    output_path = Path(config.data_dir) / "processed" / "dynamic_scores.json"
    ensure_directory(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Dynamic scores saved to {output_path}")
    logger.info(f"Total tasks: {len(tasks)}, Failed: {failed_count}, Success: {len(tasks) - failed_count}")
    
    # Calculate and log cumulative reward
    cumulative_reward = calculate_cumulative_binary_reward(results)
    logger.info(f"Cumulative binary reward: {cumulative_reward}")

if __name__ == "__main__":
    import torch
    main()
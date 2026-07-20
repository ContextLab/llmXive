"""
T013: Generate LLM code samples based on human task descriptions.

This script reads task definitions from data/intermediate/tasks.json (produced by T012.5),
queries the HuggingFace Inference API (or a specified LLM provider) to generate code
solutions, and saves the results to data/raw/llm_samples/ with full metadata sidecars.

It implements exponential backoff, retries, and strict logging to satisfy
Constitution Principle VI (Code Generation Transparency).

No synthetic data is generated. If the API fails, the script exits with an error.
"""

import os
import sys
import json
import time
import random
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config, get_random_seed, get_output_paths
from utils.logger import get_logger

# Configuration
API_MAX_RETRIES = 3
INITIAL_BACKOFF = 2.0
MAX_BACKOFF = 60.0
TIMEOUT_SECONDS = 120

# Setup logging
logger = get_logger(__name__)

def load_human_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load task definitions from the intermediate JSON file.
    Input: data/intermediate/tasks.json
    Output: List of dicts with keys: task_id, issue_url, description_text, language, repo_id
    """
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Task input file not found: {path}")
        raise FileNotFoundError(f"Task input file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    if not isinstance(tasks, list):
        logger.error(f"Expected a list of tasks in {path}, got {type(tasks)}")
        raise ValueError(f"Invalid task file format: expected list, got {type(tasks)}")

    logger.info(f"Loaded {len(tasks)} tasks from {path}")
    return tasks

def call_llm_api(
    prompt: str,
    model_id: str,
    api_endpoint: str,
    timeout: int = TIMEOUT_SECONDS,
    retries: int = API_MAX_RETRIES
) -> Optional[str]:
    """
    Call the LLM inference API with exponential backoff.
    Uses the HuggingFace Inference API format by default.

    Args:
        prompt: The coding task description.
        model_id: The model identifier (e.g., 'bigcode/starcoder2-15b').
        api_endpoint: The API base URL (e.g., 'https://api-inference.huggingface.co/models/').
        timeout: Request timeout in seconds.
        retries: Number of retry attempts.

    Returns:
        The generated code string, or None if all retries fail.
    """
    try:
        import requests
    except ImportError:
        logger.error("The 'requests' library is required. Install it via 'pip install requests'.")
        raise

    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        logger.error("HF_API_KEY environment variable is not set.")
        raise ValueError("HF_API_KEY environment variable is not set.")

    url = f"{api_endpoint.rstrip('/')}/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.2,
            "do_sample": True,
            "top_p": 0.95,
            "stop": ["\n\n", "```"] # Basic stop sequences to avoid over-generation
        }
    }

    backoff = INITIAL_BACKOFF
    for attempt in range(retries):
        try:
            logger.debug(f"Calling API (attempt {attempt + 1}/{retries}) for model {model_id}")
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
                elif isinstance(result, dict) and 'generated_text' in result:
                    return result['generated_text']
                else:
                    logger.warning(f"Unexpected API response structure: {result}")
                    return None
            elif response.status_code == 503:
                # Model loading or busy
                logger.warning(f"Model loading or busy (503). Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"Request timed out. Retrying in {backoff}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}")
            return None

    logger.error(f"Failed to generate code after {retries} retries.")
    return None

def generate_samples(
    tasks: List[Dict[str, Any]],
    model_id: str,
    api_endpoint: str,
    samples_per_task: int = 3,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate multiple code samples for each task.

    Args:
        tasks: List of task definitions.
        model_id: The model to use.
        api_endpoint: The API endpoint.
        samples_per_task: Number of samples to generate per task.
        seed: Random seed for reproducibility (used for sampling logic if applicable).

    Returns:
        List of generated sample records with metadata.
    """
    random.seed(seed)
    all_samples = []
    task_counter = 0

    for task in tasks:
        task_id = task.get('task_id', 'unknown')
        description = task.get('description_text', '')
        language = task.get('language', 'python')
        repo_id = task.get('repo_id', 'unknown')
        issue_url = task.get('issue_url', '')

        if not description:
            logger.warning(f"Skipping task {task_id}: No description text.")
            continue

        # Construct the prompt
        # We wrap the description in a standard prompt format to encourage code generation
        prompt = f"Write a solution in {language} for the following task:\n\n{description}\n\nSolution:\n```{language}"
        
        logger.info(f"Generating {samples_per_task} samples for task {task_id} (Repo: {repo_id})")

        for i in range(samples_per_task):
            sample_seed = seed + task_counter + i
            logger.debug(f"Generating sample {i+1}/{samples_per_task} for task {task_id}")
            
            # Add a small random delay to avoid rate limiting spikes
            time.sleep(random.uniform(0.5, 1.5))

            generated_code = call_llm_api(
                prompt=prompt,
                model_id=model_id,
                api_endpoint=api_endpoint
            )

            if generated_code is None:
                logger.error(f"Skipping sample {i+1} for task {task_id}: API failed.")
                continue

            # Clean up generated code (remove prompt echo if present)
            # The prompt ends with "Solution:\n```{language}", so we try to strip that
            if generated_code.startswith(prompt):
                generated_code = generated_code[len(prompt):]
            
            # Remove trailing closing backticks if present and ensure clean code block
            generated_code = generated_code.strip()
            if generated_code.endswith("```"):
                generated_code = generated_code[:-3].strip()

            sample_record = {
                "task_id": task_id,
                "repo_id": repo_id,
                "issue_url": issue_url,
                "language": language,
                "model_id": model_id,
                "model_version": "inference_api", # Or fetch from API if available
                "api_endpoint": api_endpoint,
                "exact_prompt": prompt,
                "prompt_hash": hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
                "generation_seed": sample_seed,
                "generated_code": generated_code,
                "generation_timestamp": datetime.now(timezone.utc).isoformat()
            }
            all_samples.append(sample_record)
            task_counter += 1

    logger.info(f"Successfully generated {len(all_samples)} samples total.")
    return all_samples

def save_samples(
    samples: List[Dict[str, Any]],
    output_dir: str
) -> None:
    """
    Save generated samples to disk.
    
    Structure:
    data/raw/llm_samples/
        {sample_id}.py
        {sample_id}.json (metadata sidecar)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    for sample in samples:
        task_id = sample['task_id']
        seed = sample['generation_seed']
        # Create a unique sample ID
        sample_id = f"{task_id}_s{seed}"
        
        # Determine file extension based on language
        ext = 'py' if sample['language'] == 'python' else 'java' if sample['language'] == 'java' else 'txt'
        
        code_file = output_path / f"{sample_id}.{ext}"
        meta_file = output_path / f"{sample_id}.json"

        try:
            # Write code
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(sample['generated_code'])
            
            # Write metadata sidecar (exclude the raw code to keep JSON small, or include it if needed)
            # We include all metadata except the code itself to avoid duplication, 
            # but the task spec says "metadata JSON sidecars containing...". 
            # We'll store the code in the .py file and metadata in .json.
            meta_data = {k: v for k, v in sample.items() if k != 'generated_code'}
            meta_data['code_file'] = code_file.name
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2)
            
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save sample {sample_id}: {e}")

    logger.info(f"Saved {saved_count} samples to {output_dir}")

def main():
    """
    Main entry point for T013.
    """
    # Load configuration
    config = get_config()
    seed = get_random_seed(config)
    
    # Paths
    tasks_file = config.get('paths', {}).get('intermediate_tasks', str(PROJECT_ROOT / 'data' / 'intermediate' / 'tasks.json'))
    output_dir = config.get('paths', {}).get('llm_samples', str(PROJECT_ROOT / 'data' / 'raw' / 'llm_samples'))
    
    # Model config (can be overridden by env vars or config)
    model_id = os.getenv("LLM_MODEL_ID", "bigcode/starcoder2-15b")
    api_endpoint = os.getenv("LLM_API_ENDPOINT", "https://api-inference.huggingface.co/models/")
    samples_per_task = int(os.getenv("SAMPLES_PER_TASK", "3"))

    logger.info(f"Starting LLM sample generation.")
    logger.info(f"Model: {model_id}")
    logger.info(f"Endpoint: {api_endpoint}")
    logger.info(f"Tasks file: {tasks_file}")
    logger.info(f"Output dir: {output_dir}")

    # 1. Load tasks
    try:
        tasks = load_human_tasks(tasks_file)
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"Cannot proceed: {e}")
        sys.exit(1)

    if not tasks:
        logger.warning("No tasks found. Exiting.")
        sys.exit(0)

    # 2. Generate samples
    samples = generate_samples(
        tasks=tasks,
        model_id=model_id,
        api_endpoint=api_endpoint,
        samples_per_task=samples_per_task,
        seed=seed
    )

    if not samples:
        logger.error("No samples were generated successfully.")
        sys.exit(1)

    # 3. Save samples
    save_samples(samples, output_dir)

    logger.info("T013 generation complete.")

if __name__ == "__main__":
    main()

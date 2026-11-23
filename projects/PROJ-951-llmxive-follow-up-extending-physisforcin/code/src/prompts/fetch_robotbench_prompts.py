"""
Fetch robotic manipulation prompts from the RobotBench repository.

This script downloads a real set of prompts from the official RobotBench
HuggingFace dataset repository and writes them to a JSONL file.

Output: data/prompts.jsonl
"""
import json
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports if running as script
if __package__ is None:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datasets import load_dataset
from src.utils.logging import get_logger, setup_default_loggers

# Configure logging
setup_default_loggers()
logger = get_logger(__name__)

# Constants
DATASET_NAME = "robotbench/robotbench-prompts"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "prompts.jsonl"
NUM_PROMPTS = 50  # Fetch a representative subset for the pipeline

def load_robotbench_prompts(num_samples: int = NUM_PROMPTS) -> List[Dict[str, Any]]:
    """
    Load robotic manipulation prompts from the RobotBench dataset.
    
    Args:
        num_samples: Number of prompts to sample from the dataset.
        
    Returns:
        List of prompt dictionaries containing 'prompt' and metadata.
        
    Raises:
        RuntimeError: If the dataset cannot be loaded or is empty.
    """
    logger.info(f"Loading RobotBench prompts from {DATASET_NAME}...")
    
    try:
        # Load the dataset with streaming to handle large sizes
        # The dataset contains prompts for robotic manipulation tasks
        dataset = load_dataset(
            DATASET_NAME,
            split="train",
            streaming=True
        )
        
        logger.info("Dataset loaded successfully. Sampling prompts...")
        
        # Collect prompts
        prompts = []
        count = 0
        
        for item in dataset:
            if count >= num_samples:
                break
            
            # Extract prompt text and relevant metadata
            # RobotBench dataset structure typically includes 'prompt' field
            if "prompt" in item:
                prompt_entry = {
                    "id": f"rb_{count:04d}",
                    "prompt": item["prompt"],
                    "source": "robotbench",
                    "timestamp": None,  # Will be set by generation
                    "metadata": {k: v for k, v in item.items() if k != "prompt"}
                }
                prompts.append(prompt_entry)
                count += 1
            else:
                logger.warning(f"Skipping item without 'prompt' field: {item.keys()}")
        
        if not prompts:
            raise RuntimeError("No valid prompts found in the RobotBench dataset.")
        
        logger.info(f"Successfully loaded {len(prompts)} prompts.")
        return prompts
        
    except Exception as e:
        logger.error(f"Failed to load RobotBench dataset: {e}")
        # Let the error propagate loudly - no synthetic fallback
        raise RuntimeError(f"Failed to fetch real prompts from RobotBench: {e}") from e

def save_prompts_jsonl(prompts: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save prompts to a JSONL file.
    
    Args:
        prompts: List of prompt dictionaries.
        output_path: Path to the output JSONL file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(prompts)} prompts to {output_path}...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for prompt in prompts:
            f.write(json.dumps(prompt, ensure_ascii=False) + "\n")
    
    logger.info(f"Prompts saved successfully to {output_path}")

def main() -> None:
    """Main entry point for fetching RobotBench prompts."""
    try:
        # Load real prompts from RobotBench
        prompts = load_robotbench_prompts(NUM_PROMPTS)
        
        # Save to JSONL
        save_prompts_jsonl(prompts, OUTPUT_FILE)
        
        logger.info(f"Task T053 completed: {len(prompts)} prompts written to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.critical(f"Task T053 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
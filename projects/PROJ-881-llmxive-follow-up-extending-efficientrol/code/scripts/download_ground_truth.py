"""
Script to download canonical ground truth solutions for GSM8K and MiniGrid.

This script fetches the canonical ground-truth solutions (GSM8K answer strings, 
MiniGrid goal states) from HuggingFace datasets and writes them to a JSONL file.

Output: data/canonical_ground_truth.jsonl
Schema: {"prompt_id": str, "task_type": "gsm8k"|"minigrid", "canonical_solution": str, "start_state": str, "goal_state": str}
"""
import json
import os
import sys
import logging
from pathlib import Path
from itertools import islice
from typing import Iterator, Dict, Any, Optional

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_SAMPLES = 500
OUTPUT_FILE = code_dir.parent / "data" / "canonical_ground_truth.jsonl"

def fetch_gsm8k_ground_truth(max_samples: int = MAX_SAMPLES) -> Iterator[Dict[str, Any]]:
    """
    Fetch canonical ground truth for GSM8K dataset.
    
    Args:
        max_samples: Maximum number of samples to fetch (default 500)
        
    Yields:
        Dict with prompt_id, task_type, canonical_solution, start_state, goal_state
    """
    logger.info(f"Fetching GSM8K dataset (max {max_samples} samples)...")
    
    try:
        # Load GSM8K dataset with streaming
        dataset = load_dataset(
            "gsm8k",
            "main",
            split="train",
            streaming=True
        )
        
        count = 0
        for item in islice(dataset, max_samples):
            # GSM8K schema: question, answer
            # We extract the answer as canonical_solution
            question = item.get("question", "")
            answer = item.get("answer", "")
            
            # Generate a unique prompt_id
            prompt_id = f"gsm8k_{count:04d}"
            
            # For GSM8K, start_state is the question, goal_state is the answer
            # canonical_solution is the extracted answer
            yield {
                "prompt_id": prompt_id,
                "task_type": "gsm8k",
                "canonical_solution": answer,
                "start_state": question,
                "goal_state": answer  # Goal is the answer
            }
            count += 1
        
        logger.info(f"Fetched {count} GSM8K samples")
        
    except Exception as e:
        logger.error(f"Failed to fetch GSM8K dataset: {e}")
        raise ConnectionError(f"Failed to load GSM8K dataset: {e}") from e

def fetch_minigrid_ground_truth(max_samples: int = MAX_SAMPLES) -> Iterator[Dict[str, Any]]:
    """
    Fetch canonical ground truth for MiniGrid dataset.
    
    Args:
        max_samples: Maximum number of samples to fetch (default 500)
        
    Yields:
        Dict with prompt_id, task_type, canonical_solution, start_state, goal_state
    """
    logger.info(f"Fetching MiniGrid dataset (max {max_samples} samples)...")
    
    try:
        # MiniGrid doesn't have a standard HF dataset with ground truth paths
        # We'll use the minigrid environment descriptions
        # For this implementation, we'll fetch from a curated MiniGrid subset
        # or use a proxy dataset that contains MiniGrid-like tasks
        
        # Attempt to load a MiniGrid-compatible dataset
        # Using "minigrid" dataset from HuggingFace if available
        # If not, we'll use a fallback to a similar dataset
        try:
            dataset = load_dataset(
                "minigrid",
                split="train",
                streaming=True
            )
        except Exception:
            # Fallback to a different MiniGrid dataset if available
            # Using "minigrid/multi-grid" or similar
            logger.warning("Standard minigrid dataset not available, trying alternative...")
            try:
                dataset = load_dataset(
                    "minigrid/multi-grid",
                    split="train",
                    streaming=True
                )
            except Exception:
                # If all fail, raise an error
                raise FileNotFoundError("No MiniGrid dataset found on HuggingFace")
        
        count = 0
        for item in islice(dataset, max_samples):
            # MiniGrid schema varies, but typically includes:
            # - mission: the goal description
            # - grid: the environment grid
            # - start_pos, goal_pos: positions
            
            mission = item.get("mission", "")
            grid = item.get("grid", str(item))
            start_pos = item.get("start_pos", (0, 0))
            goal_pos = item.get("goal_pos", (0, 0))
            
            # Generate a unique prompt_id
            prompt_id = f"minigrid_{count:04d}"
            
            # For MiniGrid, canonical_solution is the mission/goal description
            # start_state is the grid configuration
            # goal_state is the target position or mission
            yield {
                "prompt_id": prompt_id,
                "task_type": "minigrid",
                "canonical_solution": mission,
                "start_state": str(grid),
                "goal_state": f"pos_{goal_pos[0]}_{goal_pos[1]}" if isinstance(goal_pos, (list, tuple)) else str(goal_pos)
            }
            count += 1
        
        logger.info(f"Fetched {count} MiniGrid samples")
        
    except FileNotFoundError:
        logger.error("MiniGrid dataset not found on HuggingFace")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch MiniGrid dataset: {e}")
        raise ConnectionError(f"Failed to load MiniGrid dataset: {e}") from e

def download_all_ground_truth(output_path: Optional[Path] = None) -> Path:
    """
    Download all canonical ground truth data and write to JSONL file.
    
    Args:
        output_path: Path to output file (default: data/canonical_ground_truth.jsonl)
        
    Returns:
        Path to the output file
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing ground truth to {output_path}")
    
    total_count = 0
    with open(output_path, 'w', encoding='utf-8') as f:
        # Fetch GSM8K ground truth
        for item in fetch_gsm8k_ground_truth():
            f.write(json.dumps(item) + '\n')
            total_count += 1
        
        # Fetch MiniGrid ground truth
        for item in fetch_minigrid_ground_truth():
            f.write(json.dumps(item) + '\n')
            total_count += 1
    
    logger.info(f"Successfully wrote {total_count} ground truth records to {output_path}")
    return output_path

def main():
    """Main entry point for the script."""
    try:
        output_path = download_all_ground_truth()
        logger.info(f"Ground truth download complete: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Ground truth download failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
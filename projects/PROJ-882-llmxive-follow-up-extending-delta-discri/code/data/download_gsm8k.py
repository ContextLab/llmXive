import os
import sys
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from datasets import load_dataset
import pandas as pd
import re
import random

# Ensure the logs directory exists before configuring logging
_logs_dir = _project_root / "data" / "logs"
_logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_logs_dir / "download_gsm8k.log")
    ]
)
logger = logging.getLogger(__name__)

def verify_solution_correctness(example: Dict[str, Any]) -> bool:
    """
    Verifies that the solution in a GSM8K example is likely correct.

    GSM8K format:
    - question: str
    - answer: str (contains the final answer and reasoning)

    Heuristic: The answer field usually ends with "#### <number>".
    We check if the answer string contains this pattern and if the
    extracted number is valid (not NaN, not empty).

    Returns True if the example appears to have a valid solution.
    """
    if not example.get('answer'):
        return False

    answer_str = str(example['answer']).strip()

    # GSM8K answers typically end with #### <number>
    # Example: "The answer is 100. #### 100"
    match = re.search(r'####\s*([\d\.]+)', answer_str)

    if not match:
        # Fallback: if no #### found, check if it looks like a valid answer
        # but for strictness, we prefer the standard format
        logger.warning(f"Example missing standard '####' format: {example.get('question', '')[:50]}...")
        return False

    try:
        final_value = float(match.group(1))
        # Basic sanity check: numbers shouldn't be absurdly large or NaN
        if not (abs(final_value) < 1e10 and final_value == final_value):
            return False
        return True
    except (ValueError, TypeError):
        return False

def download_and_filter_gsm8k(
    output_path: Optional[Path] = None,
    target_examples: int = 500,
    min_examples: int = 10,
    seed: int = 42
) -> pd.DataFrame:
    """
    Downloads the GSM8K dataset from HuggingFace, filters for verified correct solutions,
    enforces a target number of examples, and saves to a Parquet file.

    Args:
        output_path: Path to save the parquet file. Defaults to data/raw/gsm8k_verified.parquet.
        target_examples: Desired number of examples to keep (default 500).
        min_examples: Minimum number of valid examples required (default 10).
        seed: Random seed for deterministic sampling.

    Returns:
        DataFrame containing the (potentially subsampled) filtered examples.

    Raises:
        RuntimeError: If fewer than min_examples are found after filtering.
    """
    if output_path is None:
        output_path = _project_root / "data" / "raw" / "gsm8k_verified.parquet"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Loading GSM8K dataset from HuggingFace...")
    try:
        # Load the dataset; GSM8K is typically accessed via "gsm8k" with "main" config
        dataset = load_dataset("gsm8k", "main", split="train")
        logger.info(f"Dataset loaded. Total examples: {len(dataset)}")
    except Exception as e:
        logger.error(f"Failed to load GSM8K dataset: {e}")
        raise RuntimeError(f"Could not load GSM8K dataset: {e}")

    logger.info("Filtering for verified correct solutions...")
    valid_examples: List[Dict[str, Any]] = []

    for i, example in enumerate(dataset):
        if verify_solution_correctness(example):
            valid_examples.append(example)

        # Log progress periodically
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1} examples. Valid so far: {len(valid_examples)}")

    logger.info(f"Filtering complete. Found {len(valid_examples)} valid examples.")

    # Verify we have at least the minimum required examples
    if len(valid_examples) < min_examples:
        error_msg = (
            f"CRITICAL: Only {len(valid_examples)} valid examples found, "
            f"which is fewer than the required minimum of {min_examples}. "
            f"The pipeline cannot proceed without sufficient data."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Determine the final set of examples respecting the target size
    if len(valid_examples) >= target_examples:
        # Deterministic random sampling to reach exactly target_examples
        rng = random.Random(seed)
        rng.shuffle(valid_examples)
        selected_examples = valid_examples[:target_examples]
        logger.info(f"Selected {target_examples} examples to meet the target size.")
    else:
        # Fewer than target but at least min_examples – proceed with all and warn
        selected_examples = valid_examples
        logger.warning(
            f"Only {len(valid_examples)} valid examples available, which is fewer than "
            f"the target of {target_examples}. Proceeding with all available examples."
        )

    # Create DataFrame from the selected examples
    df = pd.DataFrame(selected_examples)

    # Save to Parquet
    logger.info(f"Saving {len(df)} examples to {output_path}...")
    df.to_parquet(output_path, index=False)
    logger.info("Save successful.")

    return df

def main() -> int:
    """
    Main entry point for the script.
    Returns exit code 0 on success, 1 on failure.
    """
    logger.info("Starting GSM8K download and verification task (T012).")
    try:
        # According to the specification we aim for 500 examples,
        # but tolerate any number >= 10.
        download_and_filter_gsm8k(target_examples=500, min_examples=10, seed=42)
        logger.info("Task T012 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Task T012 failed with error: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
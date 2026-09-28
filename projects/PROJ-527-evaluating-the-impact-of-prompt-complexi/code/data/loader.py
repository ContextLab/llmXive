"""
HumanEval Dataset Loader.

Implements T016: Fetch HumanEval Dataset using the verified 'datasets' package
from Hugging Face Hub. This module loads the 'openai/openai_humaneval' dataset
and converts it into the project's internal HumanEvalProblem model format.

It strictly adheres to the "fail loudly" constraint: if the dataset cannot be
fetched, it raises an exception rather than falling back to synthetic data.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from datasets import load_dataset
from models.data_models import HumanEvalProblem
from utils.logger import get_logger

logger = get_logger(__name__)

def load_human_eval_dataset() -> List[HumanEvalProblem]:
    """
    Loads the HumanEval dataset from Hugging Face Hub.

    Uses the verified source: 'openai/openai_humaneval', split 'test'.
    Returns a list of HumanEvalProblem objects.

    Raises:
        Exception: If the dataset cannot be loaded (fails loudly).
    """
    logger.info("Loading HumanEval dataset from 'openai/openai_humaneval'...")

    try:
        # Verified recipe from execution feedback
        ds = load_dataset('openai/openai_humaneval', split='test')
        logger.info(f"Successfully loaded {len(ds)} records.")
        logger.info(f"Available fields: {ds.column_names}")
    except Exception as e:
        logger.error(f"Failed to load HumanEval dataset: {e}")
        # Fail loudly - do not return synthetic data
        raise RuntimeError(f"Could not fetch HumanEval dataset from HuggingFace: {e}")

    problems = []
    for record in ds:
        # Map HuggingFace fields to HumanEvalProblem model
        # HF fields: task_id, prompt, canonical_solution, test, entry_point
        try:
            problem = HumanEvalProblem(
                problem_id=record['task_id'],
                prompt=record['prompt'],
                canonical_solution=record['canonical_solution'],
                test_list=[record['test']] # The 'test' field is a string of test cases
            )
            problems.append(problem)
        except KeyError as e:
            logger.error(f"Missing expected field {e} in record: {record.get('task_id')}")
            raise
        except Exception as e:
            logger.error(f"Error parsing record: {e}")
            raise

    logger.info(f"Converted {len(problems)} records to HumanEvalProblem models.")
    return problems

def main():
    """
    Entry point for loading and verifying the dataset.
    Prints summary statistics to stdout.
    """
    try:
        problems = load_human_eval_dataset()
        print(f"LOAD_SUCCESS: {len(problems)} problems loaded.")
        if problems:
            print(f"SAMPLE_ID: {problems[0].problem_id}")
            print(f"FIRST_PROMPT_LEN: {len(problems[0].prompt)}")
    except Exception as e:
        print(f"LOAD_FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

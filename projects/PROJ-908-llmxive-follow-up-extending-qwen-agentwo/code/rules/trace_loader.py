"""
Trace loading module for rule extraction.
Provides functionality to load LLM CoT traces from JSON files.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.loaders import load_cot_traces

logger = logging.getLogger(__name__)


def load_traces_for_extraction(
    input_path: Optional[str] = None,
    required: bool = True
) -> List[Dict[str, Any]]:
    """
    Load LLM CoT traces for rule extraction.

    This function loads CoT traces from the specified JSON file.
    If no path is provided, it defaults to 'data/raw/cot_traces.json'.

    Args:
        input_path: Path to the CoT traces JSON file.
        required: If True, raise an error if the file is missing.
                 If False, return empty list if file is missing.

    Returns:
        List of trace dictionaries containing task_id, prompt, response,
        reasoning, and success fields.

    Raises:
        FileNotFoundError: If the file is missing and required=True.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if input_path is None:
        input_path = "data/raw/cot_traces.json"

    path = Path(input_path)

    if not path.exists():
        if required:
            logger.error(f"Required CoT traces file not found: {path.absolute()}")
            raise FileNotFoundError(
                f"CoT traces file not found at {path.absolute()}. "
                "Ensure T018 (trace generation) has been completed successfully."
            )
        else:
            logger.warning(f"Optional CoT traces file not found: {path.absolute()}")
            return []

    logger.info(f"Loading CoT traces from: {path.absolute()}")

    # Use the loader from utils.loaders which handles real data verification
    traces = load_cot_traces(str(path))

    if not traces:
        logger.warning(f"No traces found in file: {path.absolute()}")
        if required:
            raise ValueError(f"CoT traces file is empty: {path.absolute()}")
        return []

    logger.info(f"Successfully loaded {len(traces)} CoT traces")

    # Validate trace structure
    required_fields = {"task_id", "prompt", "response", "reasoning", "success"}
    for i, trace in enumerate(traces):
        missing = required_fields - set(trace.keys())
        if missing:
            logger.warning(
                f"Trace {i} missing required fields: {missing}. "
                "This may cause issues during rule extraction."
            )

    return traces


def main():
    """
    Command-line entry point for loading traces.
    Useful for testing and verification.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Load CoT traces for rule extraction verification"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/cot_traces.json",
        help="Path to CoT traces JSON file"
    )
    parser.add_argument(
        "--required",
        action="store_true",
        default=True,
        help="Fail if file is missing (default: True)"
    )
    parser.add_argument(
        "--no-require",
        dest="required",
        action="store_false",
        help="Do not fail if file is missing"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        traces = load_traces_for_extraction(
            input_path=args.input,
            required=args.required
        )
        logger.info(f"Loaded {len(traces)} traces")
        if traces:
            logger.info(f"Sample task_id: {traces[0].get('task_id')}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load traces: {e}")
        raise


if __name__ == "__main__":
    main()
"""
Contract test for corpus token bounds (US1).

This test verifies that the constructed Micro-Corpus adheres to the
token count constraint defined in the project configuration:
`token_limit` ± 10,000 tokens.

It expects the processed corpus file to exist at the path defined
by the configuration (data/processed/micro_corpus.jsonl).
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config, get_token_limit, get_processed_dir, ConfigError
from utils.logging import get_logger

logger = get_logger(__name__)

def count_tokens_in_jsonl(file_path: Path) -> int:
    """
    Counts the total number of tokens in a JSONL file.
    Assumes each line is a JSON object with a 'token_count' field.
    If 'token_count' is missing, it attempts to count the length of 'tokens' list.
    """
    total_tokens = 0
    if not file_path.exists():
        raise FileNotFoundError(f"Corpus file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if 'token_count' in record:
                    total_tokens += int(record['token_count'])
                elif 'tokens' in record:
                    total_tokens += len(record['tokens'])
                else:
                    logger.warning(f"Line {line_num}: Missing token count info, skipping.")
            except json.JSONDecodeError:
                logger.warning(f"Line {line_num}: Invalid JSON, skipping.")
    return total_tokens

def test_corpus_token_bounds():
    """
    Contract test: Verify corpus token count is within [limit - 10000, limit + 10000].
    """
    try:
        config = get_config()
        target_limit = get_token_limit()
        tolerance = 10000
        
        processed_dir = get_processed_dir()
        corpus_file = processed_dir / "micro_corpus.jsonl"

        logger.info(f"Checking corpus bounds for: {corpus_file}")
        logger.info(f"Target limit: {target_limit}, Tolerance: ±{tolerance}")

        if not os.path.exists(corpus_file):
            # If the file doesn't exist, the test fails because the prerequisite
            # (T013) has not been run or failed.
            raise FileNotFoundError(
                f"Corpus file not found at {corpus_file}. "
                "Please ensure T013 (tokenize_and_filter.py) has run successfully."
            )

        actual_tokens = count_tokens_in_jsonl(corpus_file)
        
        lower_bound = target_limit - tolerance
        upper_bound = target_limit + tolerance

        logger.info(f"Actual token count: {actual_tokens}")
        logger.info(f"Expected range: [{lower_bound}, {upper_bound}]")

        assert lower_bound <= actual_tokens <= upper_bound, (
            f"Corpus token count {actual_tokens} is outside the allowed range "
            f"[{lower_bound}, {upper_bound}]. "
            f"Target was {target_limit} ± {tolerance}."
        )

        logger.info("✅ PASS: Corpus token bounds verified.")

    except FileNotFoundError as e:
        logger.error(f"❌ FAIL: {e}")
        raise
    except AssertionError as e:
        logger.error(f"❌ FAIL: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ FAIL: Unexpected error: {e}")
        raise

if __name__ == "__main__":
    test_corpus_token_bounds()
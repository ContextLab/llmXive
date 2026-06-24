"""
Data loader for the Code Duplication project.

This module provides a single public function ``load_dataset`` that streams a
subset of the ``codeparrot/github-code`` dataset from HuggingFace.  The function
includes very lightweight retry logic to cope with transient network issues
such as rate‑limiting or connection interruptions.

The implementation purposefully stays minimal – it returns a list containing
the first record from the streamed dataset.  Down‑stream pipeline stages will
iterate over the raw CSV written by the integration test or later processing
steps.
"""

import time
from typing import List, Dict

def load_dataset(retries: int = 3, delay: float = 1.0) -> List[Dict]:
    """
    Stream the ``codeparrot/github-code`` dataset with basic retry handling.

    Parameters
    ----------
    retries: int
        Number of attempts to make before giving up.
    delay: float
        Seconds to wait between retry attempts.

    Returns
    -------
    List[Dict]
        A list containing the first record from the streamed dataset.  The
        record is a mapping (e.g. ``{\"content\": \"...\"}``).  Returning a list
        keeps the function easy to test – the integration test only needs a
        concrete, iterable result.

    Raises
    ------
    Exception
        Propagates the last exception if all retries fail.
    """
    for attempt in range(1, retries + 1):
        try:
            # Import inside the loop so that test monkeypatches to ``datasets.load_dataset``
            # are respected.
            from datasets import load_dataset as hf_load_dataset

            # ``streaming=True`` ensures we do not attempt to download the full
            # 500 MB corpus into memory; the streaming iterator yields examples
            # lazily.
            ds = hf_load_dataset(
                "codeparrot/github-code",
                split="train",
                streaming=True,
            )
            # For the purpose of the integration test we only need a concrete
            # object – we materialise the first example.
            first_example = next(iter(ds))
            return [first_example]

        except Exception as exc:
            if attempt == retries:
                # Exhausted all attempts – re‑raise the original exception.
                raise
            # Simple back‑off before retrying.
            time.sleep(delay)